from typing import Optional
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babel import lazy_gettext
from flask_login import login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from redtail_repository import db, login_manager
from redtail_repository.models import User
from redtail_repository.seo import page_metadata


def is_safe_local_redirect(target: Optional[str]) -> bool:
    if not target:
        return False
    parsed = urlsplit(target)
    return (
        not parsed.scheme
        and not parsed.netloc
        and target.startswith('/')
        and not target.startswith('//')
    )

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
    login_error = None

    if form.validate_on_submit():
        user: Optional[User] = db.session.query(User).filter_by(login=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get('next')
            if is_safe_local_redirect(next):
                return redirect(next)

            next_url = request.args.get('url')
            if is_safe_local_redirect(next_url):
                return redirect(next_url)

            return redirect(url_for('public.index'))

        login_error = lazy_gettext('Invalid username or password')

    return render_template(
        'login/login.html',
        form=form,
        login_error=login_error,
        **page_metadata(
            title="Log in | REDTAIL",
            description="Log in to access the REDTAIL features available to your account.",
        ),
    )

# Check state once logged in and allow for a logout button
@login_blueprint.route('/logout')
def logout():
    logout_user()

    url = request.args.get('url')
    if is_safe_local_redirect(url):
        return redirect(url)

    return redirect(url_for('public.index'))

class RegistrationForm(FlaskForm):
    login = StringField(lazy_gettext('Username'), validators=[DataRequired(), Length(min=4, max=25)])
    name = StringField(lazy_gettext('Full Name'), validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(lazy_gettext('Confirm Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(lazy_gettext('Register'))

    def validate(self, extra_validators=None):
        initial_validation = super(RegistrationForm, self).validate(extra_validators)

        if not initial_validation:
            return False
        existing_user = User.query.filter_by(login=self.login.data).first()

        if existing_user:
            self.login.errors.append(lazy_gettext('Username is already taken.'))
            return False
        return True

@login_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        new_user = User(
            login=form.login.data,
            name=form.name.data,
            verified=False,
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("You registered and are now logged in. Welcome!", "success")

        return redirect(url_for('public.index'))

    return render_template(
        'login/register.html',
        form=form,
        **page_metadata(
            title="Register | REDTAIL",
            description="Create a REDTAIL account to access remote laboratory resources.",
        ),
    )
