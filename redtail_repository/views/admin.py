from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user

from wtforms import PasswordField
from wtforms.validators import DataRequired

from ..models import Author, User, Lesson, LessonVideos, LessonImages, LessonDocs, Simulations, Devices, LessonCategory
from ..models import device_simulation_association, lesson_device_association
from ..models import author_lesson_association, lesson_simulation_association, db

class AuthedModelMixIn:
    def is_accessible(self):
        # Allow access only if the user is authenticated and has the 'admin' role
        return current_user.is_authenticated and current_user.role == 'admin'

class AuthorModelView(AuthedModelMixIn, ModelView):
    column_list = ['login', 'name']

    def __init__(self, *args, **kwargs):
        super().__init__(Author, db.session, *args, **kwargs)

class UserModelView(AuthedModelMixIn, ModelView):
    column_list = ['login', 'name', 'author', 'role', 'verified']

    form_columns = ['login', 'password', 'name', 'author', 'role', 'verified']

    form_choices = {
        'role': [
            ('admin', 'Admin'),
            ('instructor', 'Instructor')
        ]
    }

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
    
class LessonVideoForm(InlineFormAdmin):
    pass

class LessonImageForm(InlineFormAdmin):
    pass

class LessonDocsForm(InlineFormAdmin):
    pass

class DeviceForm(InlineFormAdmin):
    pass

class LessonModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'short_description', 'category', 'authors', 'devices', 'simulations']
    form_columns = ['name', 'short_description', 'category', 'authors', 'devices', 'simulations']

    inline_models = [
        # You can use an InlineFormAdmin if you want to customize the form (e.g., descriptions or whatever)
        LessonVideoForm(LessonVideos),
        LessonImageForm(LessonImages),
        LessonDocsForm(LessonDocs),
        DeviceForm(Devices)
    ]

    def _format_category(view, context, model, name):
        """Display the category name instead of an object reference."""
        return model.category.name if model.category else "No Category"

    column_formatters = {
        'category': _format_category  # Use the function instead of lambda
    }

    def __init__(self, *args, **kwargs):
        super().__init__(Lesson, db.session, *args, **kwargs)

class LessonCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'slug', 'lessons']
    form_columns = ['name', 'slug']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonCategory, db.session, *args, **kwargs)

class LessonVideosModelView(AuthedModelMixIn, ModelView):
    column_list = ['lesson', 'title', 'video_url', 'description']
    form_columns = ['lesson', 'title', 'video_url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonVideos, db.session, *args, **kwargs)

class LessonImagesModelView(AuthedModelMixIn, ModelView):
    column_list = ['lesson', 'title', 'image_url', 'description']
    form_columns = ['lesson', 'title', 'image_url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonImages, db.session, *args, **kwargs)

class LessonDocsModelView(AuthedModelMixIn, ModelView):
    column_list = ['lesson', 'title', 'doc_url', 'description']
    form_columns = ['lesson', 'title', 'doc_url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonDocs, db.session, *args, **kwargs)

class SimulationModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'description', 'lessons', 'devices']
    form_columns = ['name', 'description', 'lessons', 'devices']

    def __init__(self, *args, **kwargs):
        super().__init__(Simulations, db.session, *args, **kwargs)

class DeviceModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'description', 'lessons', 'simulations']
    form_columns = ['name', 'description', 'lessons', 'simulations']

    def __init__(self, *args, **kwargs):
        super().__init__(Devices, db.session, *args, **kwargs)

admin = Admin(name='Admin', template_mode='bootstrap3')
admin.add_view(AuthorModelView(name="Authors", category="Users"))
admin.add_view(UserModelView(name="Users", category="Users"))

admin.add_view(LessonModelView(name="Lessons", category="Lessons"))
admin.add_view(LessonCategoryModelView(name="Lesson Categories", category="Lessons"))
admin.add_view(LessonVideosModelView(name="Lesson Videos", category="Lessons"))
admin.add_view(LessonImagesModelView(name="Lesson Images", category="Lessons"))
admin.add_view(LessonDocsModelView(name="Lesson Documents", category="Lessons"))

admin.add_view(SimulationModelView(name="Simulations", category="Simulations"))

admin.add_view(DeviceModelView(name="Devices", category="Devices"))
