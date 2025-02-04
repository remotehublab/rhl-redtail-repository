from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from redtail_repository.models import User
from flask_babel import lazy_gettext

class RegistrationForm(FlaskForm):
    login = StringField(lazy_gettext('Username'), validators=[DataRequired(), Length(min=4, max=25)])
    name = StringField(lazy_gettext('Full Name'), validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField(lazy_gettext('Password'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(lazy_gettext('Confirm Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(lazy_gettext('Register'))

    def validate(self, login):
        existing_user = User.query.filter_by(login=login.data).first()
        if existing_user:
            raise ValidationError(lazy_gettext('Username is already taken.'))
