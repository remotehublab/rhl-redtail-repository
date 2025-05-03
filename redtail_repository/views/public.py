from flask import Blueprint, request, render_template, abort, redirect, url_for, make_response
from sqlalchemy.orm import joinedload
from flask_babel import gettext
from flask_login import current_user

from redtail_repository import db
from redtail_repository.models import (
    LaboratoryExercise, LaboratoryExerciseCategory, LaboratoryExerciseLevel,
    Simulation, Device, SimulationCategory, User, Author,
    DeviceCategory, DeviceFramework
)

public_blueprint = Blueprint('public', __name__)


@public_blueprint.route('/')
def index():
    return render_template('public/index.html')

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

    return render_template("public/author.html", author=author)

@public_blueprint.route('/authors')
def authors():
    all_authors = db.session.query(Author).all()
    return render_template('public/authors.html', authors=all_authors)

@public_blueprint.route('/laboratory-exercises')
def laboratory_exercises():
    all_categories = LaboratoryExerciseCategory.query.all()
    all_levels = LaboratoryExerciseLevel.query.all()
    all_frameworks = DeviceFramework.query.all()

    # Create devices_by_id dictionary
    devices_by_id = {device.id: device for device in Device.query.all()}

    # What's this for? @todo
    devices_to_frameworks = {
        # device.id: [ device frameworks ]
    }

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

    if level_slug:
        level = LaboratoryExerciseLevel.query.filter_by(slug=level_slug).first()
        if level:
            laboratory_exercises_query = laboratory_exercises_query.filter(
                LaboratoryExercise.levels.contains(level))

    if framework_slug:
        framework = DeviceFramework.query.filter_by(slug=framework_slug).first()
        if framework:
            laboratory_exercises_query = laboratory_exercises_query.join(
                LaboratoryExercise.device_frameworks).filter(DeviceFramework.id == framework.id)

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
        selected_framework=framework_slug
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

    if current_user.is_authenticated and getattr(current_user, "verified", True):
        documents = laboratory_exercise.laboratory_exercise_documents
    else:
        documents = [doc for doc in laboratory_exercise.laboratory_exercise_documents if not doc.is_solution]

    return render_template(
        "public/laboratory_exercise.html",
        laboratory_exercise=laboratory_exercise,
        authors=laboratory_exercise.authors,
        last_updated=laboratory_exercise.last_updated,
        videos=laboratory_exercise.video_url,
        images=laboratory_exercise.laboratory_exercise_images,
        documents=documents,
        simulations=laboratory_exercise.simulations,
        categories=laboratory_exercise.laboratory_exercise_categories,
        devices=devices,
        learning_goals=laboratory_exercise.learning_goals,
        levels=laboratory_exercise.levels,
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

    if device_id:
        simulations_query = simulations_query.join(Simulation.device_frameworks).join(DeviceFramework.device).filter(
            Device.id == device_id)

    if category_slug:
        category = SimulationCategory.query.filter_by(
            slug=category_slug).first()
        if category:
            simulations_query = simulations_query.join(
                Simulation.simulation_categories).filter(SimulationCategory.id == category.id)

    if framework_slug:
        framework = DeviceFramework.query.filter_by(
            slug=framework_slug).first()
        if framework:
            simulations_query = simulations_query.join(
                Simulation.device_frameworks).filter(DeviceFramework.id == framework.id)

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
        selected_framework=framework_slug
    )

@public_blueprint.route('/simulations/<simulation_slug>')
def simulation(simulation_slug):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).options(
        joinedload(Simulation.laboratory_exercises),
        joinedload(Simulation.device_frameworks).joinedload(DeviceFramework.device),
        joinedload(Simulation.simulation_categories),
        joinedload(Simulation.simulation_documents)
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

    devices = [
        {
            "device": devices_by_id[device_id],
            "frameworks": devices_to_frameworks[device_id]
        }
        for device_id in devices_to_frameworks
    ]

    return render_template(
        "public/simulation.html",
        simulation=simulation,
        laboratory_exercises=simulation.laboratory_exercises,
        devices=devices,
        devices_by_id=devices_by_id,
        categories=simulation.simulation_categories,
        documents=simulation.simulation_documents
    )


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
        category = DeviceCategory.query.get(device_category_id)
        if category:
            devices_query = devices_query.join(Device.device_categories).filter(
                DeviceCategory.id == category.id
            )

    if framework_slug:
        framework = DeviceFramework.query.filter_by(
            slug=framework_slug).first()
        if framework:
            devices_query = devices_query.join(Device.device_frameworks).filter(
                DeviceFramework.id == framework.id)

    devices = list(devices_query.all())

    for device in devices:
        print([cat.name for cat in device.device_categories])

    return render_template(
        'public/devices.html',
        devices=devices,
        all_device_categories=all_device_categories,
        all_frameworks=all_frameworks,
        selected_device_category=device_category_id,
        selected_framework=framework_slug
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
        return render_template("public/error.html", message=gettext("Device not found")), 404

    return render_template(
        "public/device.html",
        device=device,
        documents=device.device_documents,
        simulations=device.simulations,
        categories=device.device_categories,
        frameworks=device.device_frameworks
    )
