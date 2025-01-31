from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from redtail_repository.models import User

class RegistrationForm(FlaskForm):
    login = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate(self, login):
        existing_user = User.query.filter_by(login=login.data).first()
        if existing_user:
            raise ValidationError('Username is already taken.')
