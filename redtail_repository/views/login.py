from typing import Optional
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from flask_wtf import FlaskForm

from wtforms import PasswordField, BooleanField, StringField

from flask_babel import lazy_gettext

from redtail_repository import login_manager, db
from redtail_repository.models import User

@login_manager.user_loader
def user_loader(user_id: str):
    user = db.session.query(User).filter_by(id=int(user_id)).first()
    return user

class LoginForm(FlaskForm):
    username = StringField(lazy_gettext('Username'))
    password = PasswordField(lazy_gettext('Password'))
    remember_me = BooleanField(lazy_gettext('Remember me'))

login_blueprint = Blueprint('login', __name__)

@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user: Optional[User] = db.session.query(User).filter_by(login=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get('next')
            if next and next.startswith('/'):
                return redirect(next)

            return redirect(url_for('public.index'))

        form.username.errors.append(lazy_gettext('Invalid username or password'))
        form.password.errors.append(lazy_gettext('Invalid username or password'))

    return render_template('login/login.html', form=form)

# Check state once logged in and allow for a logout button
@login_blueprint.route('/logout')
def logout():
    logout_user()

    next = request.args.get('next')
    if next and next.startswith('/'):
        return redirect(next)

    return redirect(url_for('public.index'))