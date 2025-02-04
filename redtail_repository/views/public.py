from flask import Blueprint, request, render_template, abort, redirect, url_for, make_response
from sqlalchemy.orm import joinedload
from flask_babel import gettext

from redtail_repository import db
from redtail_repository.models import Lesson, LessonCategory, Simulation, Device, User, Author
from redtail_repository.views.registration import RegistrationForm

public_blueprint = Blueprint('public', __name__)

@public_blueprint.route('/')
def index():
    return render_template('public/index.html')

@public_blueprint.app_errorhandler(404)
def page_not_found(error):
    response = make_response(render_template("public/error.html", message=gettext("The page doesn't exist.")), 404)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response

@public_blueprint.route('/author/<author_id>')
def view_author(author_id):
    author = db.session.query(Author).filter_by(id=author_id).first()
    if not author:
        return render_template("public/error.html", message=gettext("Author not found")), 404

    return render_template("public/author.html", author=author)

@public_blueprint.route('/lessons')
def lessons():
# TODO: Add calls to database to populate page
    all_categories = LessonCategory.query.all()
    category_slug = request.args.get('category')
    lessons_query = Lesson.query.filter_by(active=True).options(joinedload(Lesson.authors))

    if category_slug:
        category = LessonCategory.query.filter_by(slug=category_slug).first()
        if category:
            lessons_query = lessons_query.filter_by(category_id=category.id)

    lessons = lessons_query.all()

    return render_template(
        'public/lessons.html',
        lessons=lessons,
        all_categories=all_categories
    )

@public_blueprint.route('/lessons/<lesson_slug>')
def lesson(lesson_slug):
    lesson = db.session.query(Lesson).filter_by(slug=lesson_slug, active=True).options(
        joinedload(Lesson.authors),
        joinedload(Lesson.videos),
        joinedload(Lesson.images),
        joinedload(Lesson.documents),
        joinedload(Lesson.simulations)
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
        documents=lesson.documents,
        simulations=lesson.simulations
    )

@public_blueprint.route('/simulations')
def simulations():
    # TODO: Add calls to database to populate page
    simulations = db.session.query(Simulation).all()

    return render_template('public/simulations.html', simulations=simulations)

@public_blueprint.route('/devices')
def devices():
    # TODO: Add calls to database to populate page
    devices = db.session.query(Device).all()

    return render_template('public/devices.html', devices=devices)

# Remove from public once done testing
@public_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        new_user = User(
            login=form.login.data,
            name=form.name.data
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('public.index'))

    return render_template('public/register.html', form=form)
