from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from ..models import Author, User, db

class AuthorModelView(ModelView):
    column_list = ['login', 'name']

    def __init__(self, *args, **kwargs):
        super().__init__(Author, db.session, *args, **kwargs)

class UserModelView(ModelView):
    column_list = ['login', 'name', 'author']

    def __init__(self, *args, **kwargs):
        super().__init__(User, db.session, *args, **kwargs)

admin = Admin(name='Admin', template_mode='bootstrap3')
admin.add_view(AuthorModelView(name="Authors", category="Users"))
admin.add_view(UserModelView(name="Users", category="Users"))