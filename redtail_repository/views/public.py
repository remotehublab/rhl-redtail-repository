from flask import Blueprint, render_template

public_endpoint = Blueprint('public', __name__)

@public_endpoint.route('/')
def index():
    return render_template('public/index.html')