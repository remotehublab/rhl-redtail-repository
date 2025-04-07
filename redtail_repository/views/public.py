from flask import Blueprint, request, render_template, abort, redirect, url_for, make_response
from sqlalchemy.orm import joinedload
from flask_babel import gettext

from redtail_repository import db
from redtail_repository.models import (
    Lesson, LessonCategory, Simulation, Device, SimulationCategory, User, Author, SupportedDevice,
    DeviceCategory, DeviceFramework, LessonLevel
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


@public_blueprint.route('/lessons')
def lessons():
    all_categories = LessonCategory.query.all()
    all_supported_devices = SupportedDevice.query.all()
    all_levels = LessonLevel.query.all()
    all_frameworks = DeviceFramework.query.all()

    category_slug = request.args.get('category')
    supported_device_id = request.args.get('supported_device')
    level_slug = request.args.get('level')
    framework_slug = request.args.get('framework')

    lessons_query = Lesson.query.filter_by(active=True).options(
        joinedload(Lesson.authors),
        joinedload(Lesson.supported_devices),
        joinedload(Lesson.lesson_categories),
        joinedload(Lesson.videos),
        joinedload(Lesson.images),
        joinedload(Lesson.lesson_documents),
        joinedload(Lesson.simulations),
        joinedload(Lesson.levels)
    )

    if category_slug:
        category = LessonCategory.query.filter_by(slug=category_slug).first()
        if category:
            lessons_query = lessons_query.filter(
                Lesson.lesson_categories.contains(category))

    if supported_device_id:
        lessons_query = lessons_query.join(Lesson.supported_devices).filter(
            SupportedDevice.id == supported_device_id)

    if level_slug:
        level = LessonLevel.query.filter_by(slug=level_slug).first()
        if level:
            lessons_query = lessons_query.filter(Lesson.levels.contains(level))

    if framework_slug:
        framework = DeviceFramework.query.filter_by(
            slug=framework_slug).first()
        if framework:
            lessons_query = lessons_query.join(Lesson.device_frameworks).filter(
                DeviceFramework.id == framework.id)

    lessons = lessons_query.all()

    return render_template(
        'public/lessons.html',
        lessons=lessons,
        all_categories=all_categories,
        all_supported_devices=all_supported_devices,
        all_levels=all_levels,
        all_frameworks=all_frameworks,
        selected_category=category_slug,
        selected_supported_device=supported_device_id,
        selected_level=level_slug,
        selected_framework=framework_slug
    )


@public_blueprint.route('/lessons/<lesson_slug>')
def lesson(lesson_slug):
    lesson = db.session.query(Lesson).filter_by(slug=lesson_slug, active=True).options(
        joinedload(Lesson.authors),
        joinedload(Lesson.videos),
        joinedload(Lesson.images),
        joinedload(Lesson.lesson_documents),
        joinedload(Lesson.simulations),
        joinedload(Lesson.lesson_categories),
        joinedload(Lesson.supported_devices),
        joinedload(Lesson.levels)
    ).first()

    if not lesson:
        return render_template("public/error.html", message=gettext("Lesson not found")), 404

    return render_template(
        "public/lesson.html",
        lesson=lesson,
        authors=lesson.authors,
        last_updated=lesson.last_updated,
        videos=lesson.videos,
        images=lesson.images,
        documents=lesson.lesson_documents,
        simulations=lesson.simulations,
        categories=lesson.lesson_categories,
        supported_devices=lesson.supported_devices,
        learning_goals=lesson.learning_goals,
        levels=lesson.levels,
        foo="<b>this is bold</b><script>alert('foo');</script>",
    )


@public_blueprint.route('/simulations')
def simulations():
    all_supported_devices = SupportedDevice.query.all()
    all_categories = SimulationCategory.query.all()
    all_frameworks = DeviceFramework.query.all()

    supported_device_id = request.args.get('supported_device', type=int)
    category_slug = request.args.get('category')
    framework_slug = request.args.get('framework')

    simulations_query = db.session.query(Simulation).options(
        joinedload(Simulation.supported_devices),
        joinedload(Simulation.simulation_categories),
        joinedload(Simulation.simulation_documents),
        joinedload(Simulation.device_frameworks)
    )

    if supported_device_id:
        simulations_query = simulations_query.join(Simulation.supported_devices).filter(
            SupportedDevice.id == supported_device_id)

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
        all_supported_devices=all_supported_devices,
        all_categories=all_categories,
        all_frameworks=all_frameworks,
        selected_supported_device=supported_device_id,
        selected_category=category_slug,
        selected_framework=framework_slug
    )


@public_blueprint.route('/simulations/<simulation_slug>')
def simulation(simulation_slug):
    simulation = db.session.query(Simulation).filter_by(slug=simulation_slug).options(
        joinedload(Simulation.lessons),
        joinedload(Simulation.devices).joinedload(Device.device_frameworks),
        joinedload(Simulation.supported_devices),
        joinedload(Simulation.simulation_categories),
        joinedload(Simulation.simulation_documents)
    ).first()

    if not simulation:
        return render_template("public/error.html", message=gettext("Simulation not found")), 404

    return render_template(
        "public/simulation.html",
        simulation=simulation,
        lessons=simulation.lessons,
        devices=simulation.devices,
        supported_devices=simulation.supported_devices,
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
        joinedload(Device.lessons),
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
        joinedload(Device.lessons),
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
        lessons=device.lessons,
        simulations=device.simulations,
        categories=device.device_categories,
        frameworks=device.device_frameworks
    )
