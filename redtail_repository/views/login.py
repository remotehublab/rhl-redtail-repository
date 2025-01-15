from flask import Blueprint
from flask_login import login_user, logout_user
from flask_wtf import FlaskForm

from wtforms import PasswordField, BooleanField, EmailField

from flask_babel import lazy_gettext

from redtail_repository import login_manager

class LoginForm(FlaskForm):
    email = EmailField(lazy_gettext('Email'))
    password = PasswordField(lazy_gettext('Password'))
    remember_me = BooleanField(lazy_gettext('Remember me'))

login_blueprint = Blueprint('login', __name__)

@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        login_user(form.user, remember=form.remember_me.data)
        return 'Logged in'

    return 'Login Page'

@login_blueprint.route('/logout')
def logout():
    logout_user()
    return 'Logout Page'