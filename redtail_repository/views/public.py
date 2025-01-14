from flask import Blueprint, render_template

public_blueprint = Blueprint('public', __name__)

@public_blueprint.route('/')
def index():
    return render_template('public/index.html')


@public_blueprint.route('/lessons')
def lessons():
    lessons = [
        {
            'name': "Parking lot lesson 1"
        },
        {
            'name': "Parking lot lesson 2"
        },
    ]

    return render_template('public/lessons.html', lessons=lessons)