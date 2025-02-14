from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user

from wtforms import PasswordField
from wtforms.validators import DataRequired

from ..models import (
    Author, User, Lesson, LessonVideo, LessonImage, LessonDoc, 
    Simulation, Device, LessonCategory, SupportedDevice, 
    DeviceCategory, SimulationCategory, 
    device_simulation_association, lesson_device_association,
    supported_device_lesson, supported_device_simulation,
    author_lesson_association, lesson_simulation_association, 
    device_category_association, simulation_category_association, db
)

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

class LessonModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'authors', 'last_updated', 'short_description', 'lesson_categories', 'devices', 'simulations', 'supported_devices']
    form_columns = ['lesson_categories', 'name', 'slug', 'authors', 'short_description', 'devices', 'simulations', 'supported_devices']

    inline_models = [
        LessonVideoForm(LessonVideo),
        LessonImageForm(LessonImage),
        LessonDocsForm(LessonDoc),
    ]

    def _format_categories(view, context, model, name):
        return ", ".join(category.name for category in model.lesson_categories) if model.lesson_categories else "No Categories"

    column_formatters = {'lesson_categories': _format_categories}

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
        super().__init__(LessonVideo, db.session, *args, **kwargs)

class LessonImagesModelView(AuthedModelMixIn, ModelView):
    column_list = ['lesson', 'title', 'image_url', 'description']
    form_columns = ['lesson', 'title', 'image_url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonImage, db.session, *args, **kwargs)

class LessonDocsModelView(AuthedModelMixIn, ModelView):
    column_list = ['lesson', 'title', 'doc_url', 'description']
    form_columns = ['lesson', 'title', 'doc_url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonDoc, db.session, *args, **kwargs)

class SimulationModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'description', 'lessons', 'devices', 'simulation_categories']
    form_columns = ['name', 'description', 'lessons', 'devices', 'simulation_categories']

    def __init__(self, *args, **kwargs):
        super().__init__(Simulation, db.session, *args, **kwargs)

class SimulationCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'slug', 'simulations']
    form_columns = ['name', 'slug']

    def __init__(self, *args, **kwargs):
        super().__init__(SimulationCategory, db.session, *args, **kwargs)

class DeviceModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'description', 'lessons', 'simulations', 'device_categories']
    form_columns = ['name', 'description', 'lessons', 'simulations', 'device_categories']

    def __init__(self, *args, **kwargs):
        super().__init__(Device, db.session, *args, **kwargs)
    
class DeviceCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'slug', 'devices']
    form_columns = ['name', 'slug']

    def __init__(self, *args, **kwargs):
        super().__init__(DeviceCategory, db.session, *args, **kwargs)

class SupportedDeviceModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'lessons', 'simulations']
    form_columns = ['name', 'lessons', 'simulations']

    def __init__(self, *args, **kwargs):
        super().__init__(SupportedDevice, db.session, *args, **kwargs)

admin = Admin(name='Admin', template_mode='bootstrap3')
admin.add_view(AuthorModelView(name="Author", category="User"))
admin.add_view(UserModelView(name="User", category="User"))

admin.add_view(LessonModelView(name="Lesson", category="Lesson"))
admin.add_view(LessonVideosModelView(name="Lesson Video", category="Lesson"))
admin.add_view(LessonImagesModelView(name="Lesson Image", category="Lesson"))
admin.add_view(LessonDocsModelView(name="Lesson Document", category="Lesson"))

admin.add_view(SimulationModelView(name="Simulation", category="Simulation"))

admin.add_view(DeviceModelView(name="Device", category="Device"))
admin.add_view(SupportedDeviceModelView(name="Supported Device", category="Device"))

admin.add_view(LessonCategoryModelView(name="Lesson Category", category="Category"))
admin.add_view(SimulationCategoryModelView(name="Simulation Category", category="Category"))
admin.add_view(DeviceCategoryModelView(name="Device Category", category="Category"))
