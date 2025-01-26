from flask import Blueprint, render_template

public_blueprint = Blueprint('public', __name__)

@public_blueprint.route('/')
def index():
    return render_template('public/index.html')


@public_blueprint.route('/lessons')
def lessons():
# TODO: Add calls to database to populate page
    return render_template('public/lessons.html')

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