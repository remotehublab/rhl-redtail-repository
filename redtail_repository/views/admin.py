from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from ..models import Author, User, db
from wtforms import PasswordField
from wtforms.validators import DataRequired

class AuthedModelMixIn:
    def is_accessible(self):
        # Allow access only if the user is authenticated and has the 'admin' role
        return current_user.is_authenticated and current_user.role == 'admin'

class AuthorModelView(AuthedModelMixIn, ModelView):
    column_list = ['login', 'name']

    def __init__(self, *args, **kwargs):
        super().__init__(Author, db.session, *args, **kwargs)

class UserModelView(AuthedModelMixIn, ModelView):
    column_list = ['login', 'name', 'author']

    form_columns = ['login', 'name', 'author', 'password']

    form_extra_fields = {
        'password': PasswordField('Password')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(User, db.session, *args, **kwargs)

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.password.validators = [DataRequired()]
        return form

    def on_model_change(self, form, model: User, is_created: bool):
        if form.password.data:
            model.set_password(form.password.data)

        return super().on_model_change(form, model, is_created)


admin = Admin(name='Admin', template_mode='bootstrap3')
admin.add_view(AuthorModelView(name="Authors", category="Users"))
admin.add_view(UserModelView(name="Users", category="Users"))