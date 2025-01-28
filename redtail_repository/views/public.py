from flask import Blueprint, request, render_template

from redtail_repository import db
from redtail_repository.models import Lesson

public_blueprint = Blueprint('public', __name__)

@public_blueprint.route('/')
def index():
    return render_template('public/index.html')


@public_blueprint.route('/lessons')
def lessons():
# TODO: Add calls to database to populate page

    all_categories = [
        { 
            "name": "Digital Twin",
            "slug": "digital-twin",
            "id": 1,
        },
        {
            "name": "Simulation",
            "slug": "simulation",
            "id": 2,
        },
        {
            "name": "Real-world",
            "slug": "real-world",
            "id": 3,
        }
    ]

    all_categories_by_slug = { category['slug']: category for category in all_categories}

    lessons = [
        {
            "name": "Parking Lot",
            "categories": [
                1,
                2
            ]
        },
        {
            "name": "NES Controller",
            "categories": [
                1,
            ]
        }, 
        {
            "name": "Elevator",
            "categories": [
                3,
            ]
        }, 
        {
            "name": "Keypad",
            "categories": [
                2,
            ]
        }
    ]

    category = request.args.get('category')
    if category:
        # the user has requested a category
        category_id = (all_categories_by_slug.get(category) or {}).get('id')
        if category_id:
            lessons = [ lesson for lesson in lessons if category_id in lesson.get('categories', [])]

    
    # lessons = [ 
    #     {
    #         'name': lesson.name,
    #         'description': lesson.description,
    #     }
    #     for lesson in db.session.query(Lesson).filter_by(active=True).all()
    # ]
    # 
    return render_template('public/lessons.html', lessons=lessons, all_categories=all_categories)


@public_blueprint.route('/lessons/<lesson_slug>')
def lesson(lesson_slug):
    # human-friendly-slug
    # parking-log-{12sdf132}
    # lesson_slug.split('-')[-1]

    # TODO: 
    
    return render_template("public/lesson.html", lesson=lesson)

@public_blueprint.route('/simulations')
def simulations():
    # TODO: Add calls to database to populate page
    return render_template('public/simulations.html')

@public_blueprint.route('/devices')
def devices():
    # TODO: Add calls to database to populate page
    return render_template('public/devices.html')

# Remove from public once done testing
@public_blueprint.route('/register')
def register():
    # TODO: Add calls to database to populate page
    return render_template('public/register.html')