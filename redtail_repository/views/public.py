from flask import Blueprint, render_template

public_blueprint = Blueprint('public', __name__)

@public_blueprint.route('/')
def index():
    return render_template('public/index.html')


@public_blueprint.route('/lessons')
def lessons():
    lessons = [
        {
            'name': "Parking Lot Lesson 1",
            'video': "some link",
            'images': "some photos",
            'docs': "some docs"
        },
        {
            'name': "Parking Lot Lesson 2",
            'video': "another link",
            'images': "another photo",
            'docs': "another docs"
        },
    ]

    return render_template('public/lessons.html', lessons=lessons)