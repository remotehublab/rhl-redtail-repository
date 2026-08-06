import logging
import os
import re
import shutil
import tempfile
import traceback
from functools import wraps
from urllib.parse import urljoin, urlparse, urlunparse
from uuid import uuid4

import pypandoc
import requests
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    has_app_context,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_babel import gettext
from flask_login import current_user
from markdown import markdown
from slugify import slugify
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from redtail_repository import db
from redtail_repository.models import (
    Author,
    Device,
    DeviceCategory,
    DeviceFramework,
    LaboratoryExercise,
    LaboratoryExerciseCategory,
    LaboratoryExerciseDoc,
    LaboratoryExerciseLevel,
    Simulation,
    SimulationCategory,
    SimulationDeviceDocument,
    SimulationDoc,
)
from redtail_repository.seo import (
    absolute_public_url,
    breadcrumb_schema,
    learning_resource_schema,
    page_metadata,
    research_organization_schema,
    schema_graph,
    website_schema,
)

logger = logging.getLogger(__name__)

public_blueprint = Blueprint('public', __name__)

LEGACY_EXERCISE_SLUGS = {
    "parking-lot-stm32-nucleo-wb55rg-stm32cubemx": (
        "stm32-parking-lot-intermediate-level-keil-studio"
    ),
}

LEGACY_DEVICE_SLUGS = {
    "stm32-wb55rg": "stm32-nucleo-wb55rg",
}


@public_blueprint.route('/')
def index():
    return render_template(
        'public/index.html',
        **page_metadata(
            structured_data=schema_graph(
                research_organization_schema(),
                website_schema(),
            )
        ),
    )


@public_blueprint.route('/author/<int:author_id>')
def legacy_author(author_id):
    if db.session.get(Author, author_id) is None:
        abort(404)
    return redirect(url_for('public.view_author', author_id=author_id), code=301)


@public_blueprint.route('/lessons')
@public_blueprint.route('/laboratory_exercise')
def legacy_exercise_collection():
    return redirect(url_for('public.laboratory_exercises'), code=301)


@public_blueprint.route('/lessons/<lesson_slug>')
def legacy_exercise(lesson_slug):
    current_slug = LEGACY_EXERCISE_SLUGS.get(lesson_slug, lesson_slug)
    exercise = db.session.query(LaboratoryExercise).filter_by(
        slug=current_slug,
        active=True,
    ).first()
    if exercise is None:
        abort(404)
    return redirect(
        url_for(
            'public.laboratory_exercise',
            laboratory_exercise_slug=exercise.slug,
        ),
        code=301,
    )


def _sitemap_lastmod(record):
    last_updated = getattr(record, "last_updated", None)
    return last_updated.date().isoformat() if last_updated else None


@public_blueprint.route('/robots.txt')
def robots_txt():
    body = "\n".join(
        (
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {absolute_public_url('/sitemap.xml')}",
            "",
        )
    )
    return Response(
        body,
        content_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@public_blueprint.route('/sitemap.xml')
def sitemap_xml():
    entries_by_url = {}

    def add(endpoint, *, lastmod=None, **values):
        location = absolute_public_url(url_for(endpoint, **values))
        entries_by_url[location] = {"loc": location, "lastmod": lastmod}

    add('public.index')
    add('public.authors')
    add('public.laboratory_exercises')
    add('public.simulations')
    add('public.devices')

    authors = db.session.query(Author).order_by(Author.id).all()
    exercises = (
        db.session.query(LaboratoryExercise)
        .filter_by(active=True)
        .order_by(LaboratoryExercise.slug)
        .all()
    )
    simulations = (
        db.session.query(Simulation)
        .options(
            joinedload(Simulation.simulation_documents),
            joinedload(Simulation.device_documents).joinedload(
                SimulationDeviceDocument.device
            ),
        )
        .order_by(Simulation.slug)
        .all()
    )
    devices = db.session.query(Device).order_by(Device.slug).all()

    for author in authors:
        add('public.view_author', author_id=author.id)

    for exercise in exercises:
        add(
            'public.laboratory_exercise',
            laboratory_exercise_slug=exercise.slug,
            lastmod=_sitemap_lastmod(exercise),
        )

    for simulation in simulations:
        lastmod = _sitemap_lastmod(simulation)
        add('public.simulation', simulation_slug=simulation.slug, lastmod=lastmod)

        for document in simulation.simulation_documents:
            if _markdown_document_source_available(document.doc_url):
                add(
                    'public.simulation_doc_md',
                    simulation_slug=simulation.slug,
                    doc_id=document.id,
                    title=slugify(document.title or 'documentation'),
                    lastmod=_sitemap_lastmod(document),
                )

        for document in simulation.device_documents:
            if _markdown_document_source_available(document.doc_url):
                add(
                    'public.simulation_device_doc_md',
                    simulation_slug=simulation.slug,
                    device_slug=document.device.slug,
                    doc_id=document.id,
                    name=slugify(document.name or 'documentation'),
                    lastmod=lastmod,
                )

    for device in devices:
        add(
            'public.device',
            device_slug=device.slug,
            lastmod=_sitemap_lastmod(device),
        )

    body = render_template(
        'public/sitemap.xml',
        entries=entries_by_url.values(),
    )
    return Response(
        body,
        content_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )

# This should be at app level, and if the template makes calls like url_for('.lessons') it will fail. Let's talk about this in the next meeting
# @public_blueprint.app_errorhandler(404)
# def page_not_found(error):
#     response = make_response(render_template("public/error.html", message=gettext("The page doesn't exist.")), 404)
#     response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
#     return response


@public_blueprint.route('/authors/<author_id>')
def view_author(author_id):
    author = db.session.query(Author).filter_by(id=author_id).first()
    if not author:
        return render_template("public/error.html", message=gettext("Author not found")), 404

    return render_template(
        "public/author.html",
        author=author,
        **page_metadata(
            title=f"{author.name} | REDTAIL Author",
            description=(
                f"Explore REDTAIL laboratory exercises and simulations contributed by "
                f"{author.name}."
            ),
            social_type="profile",
            structured_data=schema_graph(
                breadcrumb_schema(
                    (
                        ("Home", url_for('public.index')),
                        ("Authors", url_for('public.authors')),
                        (author.name, url_for('public.view_author', author_id=author.id)),
                    )
                ),
                {
                    "@type": "Person",
                    "@id": f"{absolute_public_url(request.path)}#person",
                    "name": author.name,
                    "url": absolute_public_url(request.path),
                    **({"sameAs": author.link} if author.link else {}),
                },
            ),
        ),
    )

@public_blueprint.route('/authors')
def authors():
    all_authors = db.session.query(Author).all()
    return render_template(
        'public/authors.html',
        authors=all_authors,
        **page_metadata(
            title="Authors and Contributors | REDTAIL",
            description=(
                "Meet the researchers and contributors creating REDTAIL remote laboratory "
                "simulations and teaching materials."
            ),
        ),
    )

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash(gettext("Please log in to access this page."), "warning")
            return redirect(url_for('login.login', next=request.full_path))

        if current_user.role != 'admin':
            flash(gettext("You must be an admin to view this page."), "danger")
            return redirect(url_for('public.index'))

        return f(*args, **kwargs)
    return decorated_function

@public_blueprint.route('/file_submission', methods=['GET', 'POST'])
@admin_required
def file_submission():
    seo_title = "Submit Teaching Materials | REDTAIL"
    seo_description = (
        "Submit and manage REDTAIL remote laboratory teaching materials."
    )
    canonical_url = page_metadata()["canonical_url"]
    exercises = db.session.query(LaboratoryExercise).filter_by(active=True).all()
    simulations = db.session.query(Simulation).all()
    authors = db.session.query(Author).all()
    categories = db.session.query(LaboratoryExerciseCategory).all()
    levels = db.session.query(LaboratoryExerciseLevel).all()
    frameworks = db.session.query(DeviceFramework).all()

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        title = (request.form.get('title') or '').strip()
        description = request.form.get('description')
        target_type = request.form.get('target_type')
        is_solution = request.form.get('is_solution') == 'on'

        if not uploaded_file or uploaded_file.filename == '':
            return render_template("public/file_submission.html", error=gettext("Please select a document to upload."), **locals())
        if not title:
            return render_template("public/file_submission.html", error=gettext("A Document Title is required."), **locals())

        simulation_target = None
        exercise = None
        exercise_mode = request.form.get('exercise_mode')
        new_name = (request.form.get('new_exercise_name') or '').strip()

        if target_type == 'simulation':
            sim_id = request.form.get('simulation_id', type=int)
            simulation_target = db.session.get(Simulation, sim_id) if sim_id else None
            if simulation_target is None:
                return render_template("public/file_submission.html", error=gettext("Please select a simulation."), **locals())
        elif target_type == 'exercise':
            if exercise_mode == 'new':
                if not new_name:
                    return render_template("public/file_submission.html", error=gettext("An exercise name is required."), **locals())
                if LaboratoryExercise.query.filter_by(slug=slugify(new_name)).first():
                    return render_template("public/file_submission.html", error=gettext("An exercise with that name already exists."), **locals())
            else:
                lab_exercise_id = request.form.get('laboratory_exercise_id', type=int)
                exercise = db.session.get(LaboratoryExercise, lab_exercise_id) if lab_exercise_id else None
                if exercise is None:
                    return render_template("public/file_submission.html", error=gettext("Select an exercise."), **locals())
        else:
            return render_template("public/file_submission.html", error=gettext("Select a valid document target."), **locals())

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        saved_paths = []
        old_upload_to_remove = None
        try:
            safe_filename = secure_filename(uploaded_file.filename)
            unique_filename = f"{uuid4().hex}_{safe_filename}"
            save_path = os.path.join(upload_folder, unique_filename)
            uploaded_file.save(save_path)
            saved_paths.append(save_path)
            doc_url = f"/uploads/{unique_filename}"

            if simulation_target is not None:
                new_doc = SimulationDoc(
                    simulation_id=simulation_target.id,
                    title=title,
                    description=description,
                    doc_url=doc_url,
                )
                db.session.add(new_doc)
            else:
                if exercise_mode == 'new':
                    slug = slugify(new_name)
                    cover_image_url = ""
                    cover_file = request.files.get('new_exercise_cover')
                    if cover_file and cover_file.filename != '':
                        safe_cover = secure_filename(cover_file.filename)
                        cover_filename = f"cover_{uuid4().hex}_{safe_cover}"
                        cover_path = os.path.join(upload_folder, cover_filename)
                        cover_file.save(cover_path)
                        saved_paths.append(cover_path)
                        cover_image_url = f"/uploads/{cover_filename}"

                    exercise = LaboratoryExercise(
                        name=new_name, slug=slug,
                        short_description=request.form.get('new_exercise_desc', ''),
                        long_description=request.form.get('new_exercise_long_desc', ''),
                        learning_goals=request.form.get('new_exercise_goals', ''),
                        cover_image_url=cover_image_url, active=True
                    )
                    db.session.add(exercise)
                    exercise.authors = Author.query.filter(
                        Author.id.in_(request.form.getlist('author_ids'))).all()
                    exercise.laboratory_exercise_categories = LaboratoryExerciseCategory.query.filter(
                        LaboratoryExerciseCategory.id.in_(request.form.getlist('category_ids'))).all()
                    exercise.levels = LaboratoryExerciseLevel.query.filter(
                        LaboratoryExerciseLevel.id.in_(request.form.getlist('level_ids'))).all()
                    exercise.device_frameworks = DeviceFramework.query.filter(
                        DeviceFramework.id.in_(request.form.getlist('framework_ids'))).all()
                    exercise.simulations = Simulation.query.filter(
                        Simulation.id.in_(request.form.getlist('simulation_ids'))).all()
                    db.session.flush()
                else:
                    cover_file = (
                        request.files.get('update_exercise_cover')
                        or request.files.get('new_exercise_cover')
                    )
                    if cover_file and cover_file.filename != '':
                        safe_cover = secure_filename(cover_file.filename)
                        cover_filename = f"cover_{uuid4().hex}_{safe_cover}"
                        cover_path = os.path.join(upload_folder, cover_filename)
                        cover_file.save(cover_path)
                        saved_paths.append(cover_path)
                        exercise.cover_image_url = f"/uploads/{cover_filename}"

                replace_doc_id = request.form.get('replace_doc_id', type=int)
                if replace_doc_id:
                    existing_doc = db.session.get(LaboratoryExerciseDoc, int(replace_doc_id))
                    if existing_doc is None or existing_doc.laboratory_exercise_id != exercise.id:
                        raise ValueError(gettext("The selected document does not belong to this exercise."))
                    if existing_doc.doc_url and existing_doc.doc_url.startswith('/uploads/'):
                        old_upload_to_remove = os.path.join(
                            upload_folder, existing_doc.doc_url.removeprefix('/uploads/'))
                    existing_doc.title = title
                    existing_doc.description = description
                    existing_doc.doc_url = doc_url
                    existing_doc.is_solution = is_solution
                else:
                    new_doc = LaboratoryExerciseDoc(
                        laboratory_exercise_id=exercise.id,
                        title=title, description=description,
                        doc_url=doc_url, is_solution=is_solution
                    )
                    db.session.add(new_doc)

            db.session.commit()
            if old_upload_to_remove and os.path.exists(old_upload_to_remove):
                try:
                    os.remove(old_upload_to_remove)
                except OSError:
                    logger.warning("Could not remove replaced upload %s", old_upload_to_remove, exc_info=True)
            return render_template("public/file_submission.html", success=gettext("Successfully updated!"), **locals())

        except Exception as e:
            db.session.rollback()
            for saved_path in saved_paths:
                try:
                    os.remove(saved_path)
                except FileNotFoundError:
                    pass
            return render_template("public/file_submission.html", error=str(e), **locals())

    return render_template("public/file_submission.html", **locals())

@public_blueprint.route('/replace_document/<doc_type>/<int:doc_id>', methods=['POST'])
@admin_required
def replace_document(doc_type, doc_id):
    if doc_type == 'exercise':
        doc = db.get_or_404(LaboratoryExerciseDoc, doc_id)
        redirect_url = url_for(
            '.laboratory_exercise',
            laboratory_exercise_slug=doc.laboratory_exercise.slug,
        )
    elif doc_type == 'simulation':
        doc = db.get_or_404(SimulationDoc, doc_id)
        redirect_url = url_for(
            '.simulation', simulation_slug=doc.simulation.slug)
    else:
        abort(400)

    new_file = request.files.get('new_file')
    new_title = request.form.get('new_title')
    old_upload_to_remove = None
    new_upload = None

    if new_file and new_file.filename != '':
        if doc.doc_url and doc.doc_url.startswith('/uploads/'):
            old_filename = doc.doc_url.replace('/uploads/', '')
            old_upload_to_remove = os.path.join(
                current_app.config['UPLOAD_FOLDER'], old_filename)

        safe_filename = secure_filename(new_file.filename)
        unique_filename = f"{uuid4().hex}_{safe_filename}"
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        new_upload = os.path.join(upload_folder, unique_filename)
        new_file.save(new_upload)

        doc.doc_url = f"/uploads/{unique_filename}"

    if new_title:
        doc.title = new_title

    try:
        db.session.commit()
        if old_upload_to_remove and os.path.exists(old_upload_to_remove):
            try:
                os.remove(old_upload_to_remove)
            except OSError:
                logger.warning(
                    "Could not remove replaced upload %s",
                    old_upload_to_remove,
                    exc_info=True,
                )
        flash(gettext("Document updated successfully!"), "success")
    except Exception as e:
        db.session.rollback()
        if new_upload:
            try:
                os.remove(new_upload)
            except FileNotFoundError:
                pass
        logger.error(f"Error replacing document: {e}")
        flash(gettext("An error occurred while updating the document."), "danger")

    return redirect(redirect_url)

@public_blueprint.route('/uploads/<path:filename>')
def serve_uploads(filename):
    if (
        _is_solution_document_path(f"/uploads/{filename}")
        and not _current_user_can_access_solutions()
    ):
        abort(404)

    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


@public_blueprint.route('/laboratory-exercises')
def laboratory_exercises():
    all_categories = LaboratoryExerciseCategory.query.all()
    all_levels = LaboratoryExerciseLevel.query.all()
    all_frameworks = DeviceFramework.query.all()

    # Create devices_by_id dictionary
    devices_by_id = {device.id: device for device in Device.query.all()}

    devices_to_frameworks = {}

    for device_framework in all_frameworks:
        devices_to_frameworks.setdefault(device_framework.device_id, []).append(device_framework)

    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id]
        }
        for device_id in devices_to_frameworks
    ]

    category_slug = request.args.get('category')
    level_slug = request.args.get('level')
    framework_slug = request.args.get('framework')

    laboratory_exercises_query = LaboratoryExercise.query.filter_by(active=True).options(
        joinedload(LaboratoryExercise.authors),
        joinedload(LaboratoryExercise.laboratory_exercise_categories),
        joinedload(LaboratoryExercise.laboratory_exercise_images),
        joinedload(LaboratoryExercise.laboratory_exercise_documents),
        joinedload(LaboratoryExercise.simulations),
        joinedload(LaboratoryExercise.levels)
    )

    if category_slug:
        category = LaboratoryExerciseCategory.query.filter_by(slug=category_slug).first()
        if category:
            laboratory_exercises_query = laboratory_exercises_query.filter(
                LaboratoryExercise.laboratory_exercise_categories.contains(category))
        else:
            category_slug = None

    if level_slug:
        level = LaboratoryExerciseLevel.query.filter_by(slug=level_slug).first()
        if level:
            laboratory_exercises_query = laboratory_exercises_query.filter(
                LaboratoryExercise.levels.contains(level))
        else:
            level_slug = None

    if framework_slug:
        framework = DeviceFramework.query.filter_by(slug=framework_slug).first()
        if framework:
            laboratory_exercises_query = laboratory_exercises_query.join(
                LaboratoryExercise.device_frameworks).filter(DeviceFramework.id == framework.id)
        else:
            framework_slug = None

    laboratory_exercises = laboratory_exercises_query.all()

    return render_template(
        'public/laboratory_exercises.html',
        laboratory_exercises=laboratory_exercises,
        devices=devices,
        devices_by_id=devices_by_id,
        all_categories=all_categories,
        all_levels=all_levels,
        all_frameworks=all_frameworks,
        selected_category=category_slug,
        selected_level=level_slug,
        selected_framework=framework_slug,
        **page_metadata(
            title="Remote Laboratory Exercises | REDTAIL",
            description=(
                "Browse classroom-ready remote laboratory exercises, lessons, and teaching "
                "materials connected to real hardware."
            ),
            canonical_path=url_for('public.laboratory_exercises'),
            include_canonical=not request.args,
        ),
    )

@public_blueprint.route('/laboratory-exercises/<laboratory_exercise_slug>')
def laboratory_exercise(laboratory_exercise_slug):
    laboratory_exercise = db.session.query(LaboratoryExercise).filter_by(slug=laboratory_exercise_slug, active=True).options(
        joinedload(LaboratoryExercise.authors),
        joinedload(LaboratoryExercise.laboratory_exercise_images),
        joinedload(LaboratoryExercise.laboratory_exercise_documents),
        joinedload(LaboratoryExercise.simulations),
        joinedload(LaboratoryExercise.laboratory_exercise_categories),
        joinedload(LaboratoryExercise.levels),
        joinedload(LaboratoryExercise.device_frameworks)
    ).first()

    if not laboratory_exercise:
        current_slug = LEGACY_EXERCISE_SLUGS.get(laboratory_exercise_slug)
        if current_slug:
            current_exercise = db.session.query(LaboratoryExercise).filter_by(
                slug=current_slug,
                active=True,
            ).first()
            if current_exercise:
                return redirect(
                    url_for(
                        'public.laboratory_exercise',
                        laboratory_exercise_slug=current_exercise.slug,
                    ),
                    code=301,
                )
        return render_template("public/error.html", message=gettext("Laboratory Exercise not found")), 404

    devices_by_id = {device.id: device for device in Device.query.all()}
    all_frameworks = DeviceFramework.query.filter(
        DeviceFramework.id.in_([framework.id for framework in laboratory_exercise.device_frameworks])
    ).all()

    # Group frameworks by device
    devices_to_frameworks = {}
    for framework in all_frameworks:
        devices_to_frameworks.setdefault(framework.device_id, []).append(framework)

    # Prepare devices with their frameworks
    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id]
        }
        for device_id in devices_to_frameworks
    ]

    verified_user = current_user.is_authenticated and getattr(current_user, "verified", True)

    return render_template(
        "public/laboratory_exercise.html",
        verified_user=verified_user,
        laboratory_exercise=laboratory_exercise,
        authors=laboratory_exercise.authors,
        last_updated=laboratory_exercise.last_updated,
        videos=laboratory_exercise.video_url,
        images=laboratory_exercise.laboratory_exercise_images,
        documents=laboratory_exercise.laboratory_exercise_documents,
        simulations=laboratory_exercise.simulations,
        categories=laboratory_exercise.laboratory_exercise_categories,
        devices=devices,
        learning_goals=laboratory_exercise.learning_goals,
        levels=laboratory_exercise.levels,
        **page_metadata(
            title=f"{laboratory_exercise.name} | REDTAIL Laboratory Exercise",
            description=laboratory_exercise.short_description,
            image_url=laboratory_exercise.cover_image_url,
            image_alt=f"{laboratory_exercise.name} laboratory exercise",
            social_type="article",
            structured_data=schema_graph(
                breadcrumb_schema(
                    (
                        ("Home", url_for('public.index')),
                        (
                            "Laboratory Exercises",
                            url_for('public.laboratory_exercises'),
                        ),
                        (
                            laboratory_exercise.name,
                            url_for(
                                'public.laboratory_exercise',
                                laboratory_exercise_slug=laboratory_exercise.slug,
                            ),
                        ),
                    )
                ),
                learning_resource_schema(
                    name=laboratory_exercise.name,
                    description=laboratory_exercise.short_description,
                    path=url_for(
                        'public.laboratory_exercise',
                        laboratory_exercise_slug=laboratory_exercise.slug,
                    ),
                    image_url=laboratory_exercise.cover_image_url,
                    resource_type="Laboratory exercise",
                    authors=laboratory_exercise.authors,
                    date_modified=laboratory_exercise.last_updated,
                    educational_levels=(level.name for level in laboratory_exercise.levels),
                    teaches=laboratory_exercise.learning_goals,
                ),
            ),
        ),
    )

@public_blueprint.route('/simulations')
def simulations():
    all_devices = Device.query.all()
    all_categories = SimulationCategory.query.all()
    all_frameworks = DeviceFramework.query.all()

    # Create devices_by_id dictionary
    devices_by_id = {device.id: device for device in all_devices}

    # Group frameworks by device for the sidebar organization
    devices_to_frameworks = {}
    for device_framework in all_frameworks:
        devices_to_frameworks.setdefault(device_framework.device_id, []).append(device_framework)

    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id]
        }
        for device_id in devices_to_frameworks
    ]

    device_id = request.args.get('device', type=int)
    category_slug = request.args.get('category')
    framework_slug = request.args.get('framework')

    simulations_query = db.session.query(Simulation).options(
        joinedload(Simulation.simulation_categories),
        joinedload(Simulation.simulation_documents),
        joinedload(Simulation.device_frameworks)
    )

    if device_id and device_id not in devices_by_id:
        device_id = None

    if device_id:
        simulations_query = simulations_query.join(Simulation.device_frameworks).join(DeviceFramework.device).filter(
            Device.id == device_id)

    if category_slug:
        category = SimulationCategory.query.filter_by(
            slug=category_slug).first()
        if category:
            simulations_query = simulations_query.join(
                Simulation.simulation_categories).filter(SimulationCategory.id == category.id)
        else:
            category_slug = None

    if framework_slug:
        framework = DeviceFramework.query.filter_by(
            slug=framework_slug).first()
        if framework:
            simulations_query = simulations_query.join(
                Simulation.device_frameworks).filter(DeviceFramework.id == framework.id)
        else:
            framework_slug = None

    simulations = simulations_query.all()

    return render_template(
        'public/simulations.html',
        simulations=simulations,
        devices=devices,
        devices_by_id=devices_by_id,
        all_devices=all_devices,
        all_categories=all_categories,
        all_frameworks=all_frameworks,
        selected_device=device_id,
        selected_category=category_slug,
        selected_framework=framework_slug,
        **page_metadata(
            title="Remote Laboratory Simulations and Digital Twins | REDTAIL",
            description=(
                "Explore REDTAIL simulations and digital twins connected to remotely "
                "accessible laboratory hardware."
            ),
            canonical_path=url_for('public.simulations'),
            include_canonical=not request.args,
        ),
    )

@public_blueprint.route('/simulations/<simulation_slug>')
def simulation(simulation_slug):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).options(
        joinedload(Simulation.laboratory_exercises),
        joinedload(Simulation.device_frameworks).joinedload(DeviceFramework.device),
        joinedload(Simulation.simulation_categories),
        joinedload(Simulation.simulation_documents),
        joinedload(Simulation.simulation_images),
        joinedload(Simulation.authors)
    ).first()

    if not simulation:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    # Organize frameworks by device for consistency with parent route
    devices_by_id = {}
    devices_to_frameworks = {}

    for framework in simulation.device_frameworks:
        device = framework.device
        devices_by_id[device.id] = device
        devices_to_frameworks.setdefault(device.id, []).append(framework)

    device_documents_by_device_id = {
        # device_id: [ document1, document2 ]
    }

    for document in simulation.device_documents:
        if _document_source_available(document.doc_url):
            device_documents_by_device_id.setdefault(document.device_id, []).append(document)

    any_device_documents = len(device_documents_by_device_id) > 0

    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id],
            "documents": device_documents_by_device_id.get(device_id, [])
        }
        for device_id in devices_to_frameworks
    ]

    return render_template(
        "public/simulation.html",
        any_device_documents=any_device_documents,
        simulation=simulation,
        laboratory_exercises=[
            exercise for exercise in simulation.laboratory_exercises if exercise.active
        ],
        devices=devices,
        devices_by_id=devices_by_id,
        categories=simulation.simulation_categories,
        documents=[
            document
            for document in simulation.simulation_documents
            if _document_source_available(document.doc_url)
        ],
        **page_metadata(
            title=f"{simulation.name} | Remote Laboratory Simulation | REDTAIL",
            description=simulation.description,
            image_url=simulation.cover_image_url,
            image_alt=f"{simulation.name} remote laboratory simulation",
            social_type="article",
            structured_data=schema_graph(
                breadcrumb_schema(
                    (
                        ("Home", url_for('public.index')),
                        ("Simulations", url_for('public.simulations')),
                        (
                            simulation.name,
                            url_for(
                                'public.simulation',
                                simulation_slug=simulation.slug,
                            ),
                        ),
                    )
                ),
                learning_resource_schema(
                    name=simulation.name,
                    description=simulation.description,
                    path=url_for(
                        'public.simulation',
                        simulation_slug=simulation.slug,
                    ),
                    image_url=simulation.cover_image_url,
                    resource_type="Simulation",
                    authors=simulation.authors,
                    date_modified=simulation.last_updated,
                ),
            ),
        ),
    )

@public_blueprint.route('/simulations/<simulation_slug>/docs/<int:doc_id>-<title>.md')
def simulation_doc_md(simulation_slug, doc_id: int, title: str):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).options(
        joinedload(Simulation.device_frameworks).joinedload(DeviceFramework.device),
        joinedload(Simulation.simulation_categories),
        joinedload(Simulation.authors)
    ).first()

    if not simulation:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    doc = db.session.query(SimulationDoc).filter_by(id=doc_id, simulation_id=simulation.id).first()
    if doc is None:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    if not doc.doc_url.lower().endswith('.md'):
        return render_template("public/error.html", message=gettext("Document is not Markdown")), 404

    # Organize frameworks by device for consistency with parent route
    devices_by_id = {}
    devices_to_frameworks = {}

    for framework in simulation.device_frameworks:
        device = framework.device
        devices_by_id[device.id] = device
        devices_to_frameworks.setdefault(device.id, []).append(framework)

    device_documents_by_device_id = {
        # device_id: [ document1, document2 ]
    }

    for document in simulation.device_documents:
        device_documents_by_device_id.setdefault(document.device_id, []).append(document)

    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id],
            "documents": device_documents_by_device_id.get(device_id, [])
        }
        for device_id in devices_to_frameworks
    ]

    response = _get_html(doc.doc_url)
    if not isinstance(response, str):
        return response

    return render_template(
        "public/simulation_md.html",
        simulation=simulation,
        doc=doc,
        html_content=response,
        categories=simulation.simulation_categories,
        devices=devices,
        **page_metadata(
            title=f"{doc.title} — {simulation.name} | REDTAIL",
            description=doc.description or f"Documentation for the {simulation.name} simulation.",
            canonical_path=url_for(
                'public.simulation_doc_md',
                simulation_slug=simulation.slug,
                doc_id=doc.id,
                title=slugify(doc.title or 'documentation'),
            ),
            image_url=simulation.cover_image_url,
            image_alt=f"{simulation.name} simulation documentation",
            social_type="article",
            structured_data=schema_graph(
                breadcrumb_schema(
                    (
                        ("Home", url_for('public.index')),
                        ("Simulations", url_for('public.simulations')),
                        (
                            simulation.name,
                            url_for(
                                'public.simulation',
                                simulation_slug=simulation.slug,
                            ),
                        ),
                        (
                            doc.title,
                            url_for(
                                'public.simulation_doc_md',
                                simulation_slug=simulation.slug,
                                doc_id=doc.id,
                                title=slugify(doc.title or 'documentation'),
                            ),
                        ),
                    )
                )
            ),
        ),
    )


def _legacy_simulation_document_redirect(simulation_slug, doc_id, endpoint):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).first()
    if simulation is None:
        abort(404)
    document = db.session.query(SimulationDoc).filter_by(
        id=doc_id,
        simulation_id=simulation.id,
    ).first()
    if document is None:
        abort(404)
    return redirect(
        url_for(
            endpoint,
            simulation_slug=simulation.slug,
            doc_id=document.id,
            title=document.slugified_title,
        ),
        code=301,
    )


@public_blueprint.route('/simulations/<simulation_slug>/docs/<int:doc_id>.md')
def legacy_simulation_doc_md(simulation_slug, doc_id):
    return _legacy_simulation_document_redirect(
        simulation_slug,
        doc_id,
        'public.simulation_doc_md',
    )


@public_blueprint.route('/simulations/<simulation_slug>/docs/<int:doc_id>.docx')
def legacy_simulation_doc_word(simulation_slug, doc_id):
    return _legacy_simulation_document_redirect(
        simulation_slug,
        doc_id,
        'public.simulation_doc_word',
    )


@public_blueprint.route('/simulations/<simulation_slug>/docs/<int:doc_id>-<title>.docx')
def simulation_doc_word(simulation_slug, doc_id: int, title):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).first()

    if not simulation:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    doc = db.session.query(SimulationDoc).filter_by(id=doc_id, simulation_id=simulation.id).first()
    if doc is None:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    if not doc.doc_url.lower().endswith('.md'):
        return render_template("public/error.html", message=gettext("Document is not Markdown")), 404

    title = f"{simulation.name}-{doc.title}.docx"

    return _get_word(doc.doc_url, title)

@public_blueprint.route('/simulations/<simulation_slug>/devices/<device_slug>/docs/<int:doc_id>-<name>.md')
def simulation_device_doc_md(simulation_slug: str, device_slug: str, doc_id: int, name):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).first()

    if not simulation:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    device = db.session.query(Device).filter_by(slug=device_slug).first()
    if not device:
        return render_template("public/error.html", message=gettext("Device not found")), 404

    doc = db.session.query(SimulationDeviceDocument).filter_by(id=doc_id, simulation_id=simulation.id, device_id=device.id).first()
    if doc is None:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    if not doc.doc_url.lower().endswith('.md'):
        return render_template("public/error.html", message=gettext("Document is not Markdown")), 404

    # Organize frameworks by device for consistency with parent route
    devices_by_id = {}
    devices_to_frameworks = {}

    for framework in simulation.device_frameworks:
        dev = framework.device
        devices_by_id[dev.id] = dev
        devices_to_frameworks.setdefault(dev.id, []).append(framework)

    device_documents_by_device_id = {
        # device_id: [ document1, document2 ]
    }

    for document in simulation.device_documents:
        device_documents_by_device_id.setdefault(document.device_id, []).append(document)

    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id],
            "documents": device_documents_by_device_id.get(device_id, [])
        }
        for device_id in devices_to_frameworks
    ]

    response = _get_html(doc.doc_url)
    if not isinstance(response, str):
        return response

    return render_template(
        "public/simulation_device_md.html",
        simulation=simulation,
        device=device,
        doc=doc,
        html_content=response,
        categories=simulation.simulation_categories,
        devices=devices,
        **page_metadata(
            title=f"{doc.name} — {simulation.name} | REDTAIL",
            description=(
                f"{device.name} mapping and documentation for the {simulation.name} simulation."
            ),
            canonical_path=url_for(
                'public.simulation_device_doc_md',
                simulation_slug=simulation.slug,
                device_slug=device.slug,
                doc_id=doc.id,
                name=slugify(doc.name or 'documentation'),
            ),
            image_url=simulation.cover_image_url,
            image_alt=f"{simulation.name} simulation documentation for {device.name}",
            social_type="article",
            structured_data=schema_graph(
                breadcrumb_schema(
                    (
                        ("Home", url_for('public.index')),
                        ("Simulations", url_for('public.simulations')),
                        (
                            simulation.name,
                            url_for(
                                'public.simulation',
                                simulation_slug=simulation.slug,
                            ),
                        ),
                        (
                            doc.name,
                            url_for(
                                'public.simulation_device_doc_md',
                                simulation_slug=simulation.slug,
                                device_slug=device.slug,
                                doc_id=doc.id,
                                name=slugify(doc.name or 'documentation'),
                            ),
                        ),
                    )
                )
            ),
        ),
    )


def _legacy_simulation_device_document_redirect(
    simulation_slug,
    device_slug,
    doc_id,
    endpoint,
):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).first()
    device = db.session.query(Device).filter_by(slug=device_slug).first()
    if simulation is None or device is None:
        abort(404)
    document = db.session.query(SimulationDeviceDocument).filter_by(
        id=doc_id,
        simulation_id=simulation.id,
        device_id=device.id,
    ).first()
    if document is None:
        abort(404)
    return redirect(
        url_for(
            endpoint,
            simulation_slug=simulation.slug,
            device_slug=device.slug,
            doc_id=document.id,
            name=document.slugified_name,
        ),
        code=301,
    )


@public_blueprint.route(
    '/simulations/<simulation_slug>/devices/<device_slug>/docs/<int:doc_id>.md'
)
def legacy_simulation_device_doc_md(simulation_slug, device_slug, doc_id):
    return _legacy_simulation_device_document_redirect(
        simulation_slug,
        device_slug,
        doc_id,
        'public.simulation_device_doc_md',
    )


@public_blueprint.route(
    '/simulations/<simulation_slug>/devices/<device_slug>/docs/<int:doc_id>.docx'
)
def legacy_simulation_device_doc_word(simulation_slug, device_slug, doc_id):
    return _legacy_simulation_device_document_redirect(
        simulation_slug,
        device_slug,
        doc_id,
        'public.simulation_device_doc_word',
    )

@public_blueprint.route('/simulations/<simulation_slug>/devices/<device_slug>/docs/<int:doc_id>-<name>.docx')
def simulation_device_doc_word(simulation_slug: str, device_slug: str, doc_id: int, name):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).first()

    if not simulation:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    device = db.session.query(Device).filter_by(slug=device_slug).first()
    if not device:
        return render_template("public/error.html", message=gettext("Device not found")), 404

    doc = db.session.query(SimulationDeviceDocument).filter_by(id=doc_id, simulation_id=simulation.id, device_id=device.id).first()
    if doc is None:
        return render_template("public/error.html", message=gettext("Simulation Device Document not found for %(device_name)s and %(simulation_name)s", simulation_name=simulation.name, device_name=device.name)), 404


    if not doc.doc_url.lower().endswith('.md'):
        return render_template("public/error.html", message=gettext("Document is not Markdown")), 404

    title = f"{simulation.name}-{device.name}-{doc.name}.docx"

    return _get_word(doc.doc_url, title)



@public_blueprint.route('/devices')
def devices():
    all_device_categories = db.session.query(DeviceCategory).all()
    all_frameworks = db.session.query(DeviceFramework).all()

    device_category_id = request.args.get('device_category', type=int)
    framework_slug = request.args.get('framework')

    devices_query = db.session.query(Device).options(
        joinedload(Device.device_categories),
        joinedload(Device.device_documents),
        joinedload(Device.simulations)
    )

    if device_category_id:
        category = db.session.get(DeviceCategory, device_category_id)
        if category:
            devices_query = devices_query.join(Device.device_categories).filter(
                DeviceCategory.id == category.id
            )
        else:
            device_category_id = None

    if framework_slug:
        framework = DeviceFramework.query.filter_by(
            slug=framework_slug).first()
        if framework:
            devices_query = devices_query.join(Device.device_frameworks).filter(
                DeviceFramework.id == framework.id)
        else:
            framework_slug = None

    devices = list(devices_query.all())

    return render_template(
        'public/devices.html',
        devices=devices,
        all_device_categories=all_device_categories,
        all_frameworks=all_frameworks,
        selected_device_category=device_category_id,
        selected_framework=framework_slug,
        **page_metadata(
            title="Remote Laboratory Hardware and Devices | REDTAIL",
            description=(
                "Browse real laboratory hardware supported by REDTAIL simulations and "
                "teaching materials."
            ),
            canonical_path=url_for('public.devices'),
            include_canonical=not request.args,
        ),
    )


@public_blueprint.route('/devices/<device_slug>')
def device(device_slug):
    device = db.session.query(Device).filter_by(slug=device_slug).options(
        joinedload(Device.device_documents),
        joinedload(Device.simulations),
        joinedload(Device.device_categories),
        joinedload(Device.device_frameworks)
    ).first()

    if not device:
        current_slug = LEGACY_DEVICE_SLUGS.get(device_slug)
        if current_slug:
            current_device = db.session.query(Device).filter_by(
                slug=current_slug
            ).first()
            if current_device:
                return redirect(
                    url_for('public.device', device_slug=current_device.slug),
                    code=301,
                )
        return render_template("public/error.html", message=gettext("Device not found")), 404

    return render_template(
        "public/device.html",
        device=device,
        documents=device.device_documents,
        simulations=device.simulations,
        categories=device.device_categories,
        frameworks=device.device_frameworks,
        **page_metadata(
            title=f"{device.name} Remote Laboratory Device | REDTAIL",
            description=device.description,
            image_url=device.cover_image_url,
            image_alt=f"{device.name} remote laboratory device",
            social_type="article",
            structured_data=schema_graph(
                breadcrumb_schema(
                    (
                        ("Home", url_for('public.index')),
                        ("Devices", url_for('public.devices')),
                        (
                            device.name,
                            url_for('public.device', device_slug=device.slug),
                        ),
                    )
                )
            ),
        ),
    )

@public_blueprint.route('/docs/markdown-viewer/<path:path>')
def md_viewer(path):
    is_solution = _is_solution_document_path(path)
    if is_solution and not _current_user_can_access_solutions():
        abort(404)

    response = _get_html(path)
    if not isinstance(response, str):
        return response
    metadata = page_metadata(
        title="REDTAIL Documentation",
        description="View REDTAIL remote laboratory documentation.",
    )
    if is_solution:
        metadata["seo_robots"] = "noindex, nofollow"
    rendered = make_response(
        render_template(
            "public/markdown-viewer.html",
            html_content=response,
            path=path,
            **metadata,
        )
    )
    if is_solution:
        rendered.headers["Cache-Control"] = "private, no-store"
        rendered.headers["X-Robots-Tag"] = "noindex, nofollow"
    return rendered

@public_blueprint.route('/docs/word-converter/<path:path>')
def word_converter(path):
    is_solution = _is_solution_document_path(path)
    if is_solution and not _current_user_can_access_solutions():
        abort(404)

    response = _get_word(path)
    if is_solution and isinstance(response, Response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response

def _get_word(path: str, filename: str = 'document.docx'):
    response = _get_md(path)
    if not isinstance(response, str):
        return response

    parsed = urlparse(path)
    is_url = parsed.scheme in ('http', 'https')

    input_temp_dir = None
    if is_url:
        base_url = path.rsplit('/', 1)[0] + '/'
        input_temp_dir = tempfile.mkdtemp(prefix='redtail-markdown-')
        md_path = os.path.join(input_temp_dir, 'document.md')

        # Download relative images
        def replace_image(match):
            alt_text, img_path = match.groups()
            if img_path.startswith(('http://', 'https://', '/')):
                return match.group(0)  # leave as-is
            # Download image
            img_url = urljoin(base_url, img_path)
            local_img_path = os.path.join(input_temp_dir, os.path.basename(img_path))
            try:
                img_data = requests.get(img_url, timeout=5)
                img_data.raise_for_status()
                with open(local_img_path, 'wb') as img_file:
                    img_file.write(img_data.content)
                return f'![{alt_text}]({os.path.basename(img_path)})'
            except Exception as e:
                print(f"Warning: failed to download {img_url}: {e}")
                return match.group(0)  # keep original

        # Replace image paths in Markdown
        updated_md = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image, response)

        # Write Markdown file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(updated_md)

        resource_path = input_temp_dir

    else:
        # Local file: use its directory as base for image lookup
        md_path = _resolve_local_document_path(path)
        if md_path is None:
            return "Access denied", 403
        resource_path = os.path.dirname(md_path)

    safe_download_name = secure_filename(filename) or 'document.docx'
    if not safe_download_name.lower().endswith('.docx'):
        safe_download_name += '.docx'
    output_temp_dir = tempfile.mkdtemp(prefix='redtail-docx-')
    docx_path = os.path.join(output_temp_dir, safe_download_name)

    try:
        pypandoc.convert_file(
            md_path,
            'docx',
            outputfile=docx_path,
            extra_args=['--resource-path=.:{}'.format(resource_path)]
        )
        return send_file(
            docx_path,
            as_attachment=True,
            download_name=safe_download_name,
        )
    finally:
        if input_temp_dir:
            shutil.rmtree(input_temp_dir, ignore_errors=True)
        shutil.rmtree(output_temp_dir, ignore_errors=True)


def _resolve_local_document_path(path: str):
    project_root = os.path.realpath(
        current_app.config['PROJECT_ROOT'] if has_app_context() else os.getcwd()
    )

    if path.startswith('/uploads/'):
        allowed_root = os.path.realpath(
            current_app.config['UPLOAD_FOLDER']
            if has_app_context()
            else os.path.join(project_root, 'redtail_repository', 'uploads')
        )
        abs_path = os.path.realpath(
            os.path.join(allowed_root, path.removeprefix('/uploads/'))
        )
    elif path.startswith('/public/'):
        allowed_root = project_root
        abs_path = os.path.realpath(os.path.join(project_root, path.lstrip('/')))
    else:
        allowed_root = project_root
        abs_path = os.path.realpath(
            path if os.path.isabs(path) else os.path.join(project_root, path)
        )

    try:
        within_allowed_root = (
            os.path.commonpath((allowed_root, abs_path)) == allowed_root
        )
    except ValueError:
        within_allowed_root = False
    return abs_path if within_allowed_root else None


def _resolved_upload_reference(path: str):
    if not path:
        return None

    upload_root = os.path.realpath(current_app.config['UPLOAD_FOLDER'])
    parsed = urlparse(path)
    reference = parsed.path if parsed.scheme in ('http', 'https') else path
    normalized_reference = reference.replace('\\', '/')

    if normalized_reference.startswith('/uploads/'):
        relative_path = normalized_reference.removeprefix('/uploads/')
        resolved_path = os.path.realpath(os.path.join(upload_root, relative_path))
    elif normalized_reference.startswith('uploads/'):
        relative_path = normalized_reference.removeprefix('uploads/')
        resolved_path = os.path.realpath(os.path.join(upload_root, relative_path))
    else:
        resolved_path = _resolve_local_document_path(reference)
        if resolved_path is None:
            return None

    try:
        within_upload_root = (
            os.path.commonpath((upload_root, resolved_path)) == upload_root
        )
    except ValueError:
        within_upload_root = False
    return resolved_path if within_upload_root else None


def _document_reference_key(path: str):
    upload_path = _resolved_upload_reference(path)
    if upload_path is not None:
        return "local", upload_path

    parsed = urlparse(path)
    if parsed.scheme in ('http', 'https'):
        return "remote", parsed._replace(fragment='').geturl()

    local_path = _resolve_local_document_path(path)
    return ("local", local_path) if local_path is not None else None


def _is_solution_document_path(path: str) -> bool:
    requested_reference = _document_reference_key(path)
    if requested_reference is None:
        return False

    solution_urls = (
        db.session.query(LaboratoryExerciseDoc.doc_url)
        .filter(LaboratoryExerciseDoc.is_solution.is_(True))
        .all()
    )
    return any(
        _document_reference_key(doc_url) == requested_reference
        for doc_url, in solution_urls
    )


def _current_user_can_access_solutions() -> bool:
    return current_user.is_authenticated and (
        getattr(current_user, 'verified', False)
        or getattr(current_user, 'role', None) == 'admin'
    )


def _document_source_available(path: str) -> bool:
    if not path:
        return False

    parsed = urlparse(path)
    if parsed.scheme in ('http', 'https'):
        if not has_app_context():
            return True
        return parsed.netloc in current_app.config['KNOWN_DOMAINS']

    abs_path = _resolve_local_document_path(path)
    return abs_path is not None and os.path.isfile(abs_path)


def _markdown_document_source_available(path: str) -> bool:
    return bool(
        path
        and path.lower().endswith('.md')
        and _document_source_available(path)
    )


def _get_md(path: str):
    # Ensure it ends with .md
    if not path.lower().endswith('.md'):
        return "Unsupported file type", 400

    # Handle known domains for URLs
    parsed = urlparse(path)
    if parsed.scheme in ('http', 'https'):
        if has_app_context():
            known_domains = current_app.config['KNOWN_DOMAINS']
        else:
            known_domains = tuple(
                d.strip()
                for d in (
                    os.environ.get('KNOWN_DOMAINS')
                    or "redtail.rhlab.ece.uw.edu"
                ).split(',')
                if d.strip()
            )
        domain = parsed.netloc
        if domain not in known_domains:
            return "Domain not allowed", 403

        try:
            req = requests.get(path, timeout=5)
            req.raise_for_status()
            return req.text
        except Exception as err:
            logger.warning(f"Could not retrieve {path}: {err}", exc_info=True)
            traceback.print_exc()
            return f"Path not found: {path}", 404

    # Handle local file access
    try:
        abs_path = _resolve_local_document_path(path)
        if abs_path is None:
            return "Access denied", 403

        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Could not find local file %s", path)
        return f"Could not find local file {path}", 404
    except Exception as err:
        logger.warning(f"Could not open local file {path}: {err}", exc_info=True)
        traceback.print_exc()
        return f"Could not open local file {path}", 500

def secure_image_paths(md_text, image_base_url):
    # Rewrite only local images (not starting with http, https, or /)
    return re.sub(
        r'!\[(.*?)\]\((?!https?://|/)(.*?)\)',
        lambda m: f'![{m.group(1)}]({image_base_url}{m.group(2)})',
        md_text
    )

def get_image_base_url(path):
    parsed = urlparse(path)

    if parsed.scheme in ('http', 'https'):
        base_path = os.path.dirname(parsed.path) + '/'
        return urlunparse((parsed.scheme, parsed.netloc, base_path, '', '', ''))
    else:
        directory = os.path.dirname(path).replace('\\', '/').strip('/')
        return f'/{directory}/' if directory else '/'

def _get_html(path: str):
    response = _get_md(path)
    if isinstance(response, str):
        image_base_url = get_image_base_url(path)
        safe_md = secure_image_paths(response, image_base_url)
        return markdown(safe_md, extensions=['extra'])
    return response

@public_blueprint.route('/public/<path:filename>')
def serve_public(filename: str):
    if current_app.debug or current_app.config['SERVE_PUBLIC_FILES']:
        return send_from_directory(current_app.config['PUBLIC_FOLDER'], filename)

    return "/public only works in development", 404
