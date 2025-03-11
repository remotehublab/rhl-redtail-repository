from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user

from wtforms import PasswordField
from wtforms.validators import DataRequired

from ..models import (
    Author, User, Lesson, LessonVideo, LessonImage, LessonDoc, 
    Simulation, Device, LessonCategory, SupportedDevice, LessonLevel,
    DeviceCategory, SimulationCategory, DeviceDoc, SimulationDoc,
    DeviceFramework,
    device_simulation_association, lesson_device_association,
    supported_device_lesson, supported_device_simulation,
    author_lesson_association, lesson_simulation_association, 
    device_category_association, simulation_category_association, 
    device_framework_association, lesson_level_association, 
    lesson_device_framework_association, simulation_framework_association,
    db
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

class SimulationDocForm(InlineFormAdmin):
    pass

class DeviceDocForm(InlineFormAdmin):
    pass

class LessonModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'short_description', 'active',
        'cover_image_url', 'long_description', 'learning_goals', 'levels',
        'last_updated',
        'authors', 'devices', 'simulations', 'supported_devices', 'lesson_categories',
        'device_frameworks',
        'videos', 'images', 'lesson_documents'
    ]

    column_searchable_list = ['name', 'slug', 'short_description', 'long_description', 'learning_goals', 'authors.name']
    column_filters = ['name', 'slug', 'short_description', 'long_description', 'learning_goals', 'active', 'levels', 'last_updated']

    form_columns = [
        'id', 'name', 'slug', 'short_description', 'active',
        'cover_image_url', 'long_description', 'learning_goals', 'levels',
        'authors', 'devices', 'simulations', 'supported_devices', 'lesson_categories',
        'device_frameworks',
        'videos', 'images', 'lesson_documents'
    ]

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

class LessonVideosModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'lesson_id', 'lesson',
        'title', 'video_url', 'description', 'last_updated'
    ]
    form_columns = [
        'id', 'lesson_id', 'lesson',
        'title', 'video_url', 'description', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LessonVideo, db.session, *args, **kwargs)

class LessonImagesModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'lesson_id', 'lesson',
        'title', 'image_url', 'description', 'last_updated'
    ]
    form_columns = [
        'id', 'lesson_id', 'lesson',
        'title', 'image_url', 'description', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LessonImage, db.session, *args, **kwargs)

class LessonDocsModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'lesson_id', 'lesson',
        'title', 'doc_url', 'description', 'is_solution', 'last_updated'
    ]
    form_columns = [
        'id', 'lesson_id', 'lesson',
        'title', 'doc_url', 'description', 'is_solution', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LessonDoc, db.session, *args, **kwargs)

class LessonLevelModelView(AuthedModelMixIn, ModelView):
    column_list = ['id', 'name', 'slug', 'last_updated', 'lessons']
    form_columns = ['name', 'slug', 'lessons']

    def __init__(self, *args, **kwargs):
        super().__init__(LessonLevel, db.session, *args, **kwargs)

class SimulationModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'description',
        'cover_image_url', 'last_updated',
        'lessons', 'devices', 'supported_devices',
        'simulation_categories', 'simulation_device_categories',
        'device_frameworks',
        'simulation_documents', 
    ]
    form_columns = [
        'id', 'name', 'slug', 'description',
        'cover_image_url',
        'lessons', 'devices', 'supported_devices',
        'simulation_categories', 'simulation_device_categories',
        'device_frameworks',
        'simulation_documents', 
    ]

    inline_models = [
        SimulationDocForm(SimulationDoc)
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(Simulation, db.session, *args, **kwargs)

class SimulationDocModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'simulation_id', 'simulation',
        'title', 'doc_url', 'description', 'last_updated'
    ]
    form_columns = [
        'id', 'simulation_id', 'simulation',
        'title', 'doc_url', 'description', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(SimulationDoc, db.session, *args, **kwargs)


class SimulationCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'last_updated', 'simulations'
    ]
    form_columns = [
        'id', 'name', 'slug', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(SimulationCategory, db.session, *args, **kwargs)

class DeviceModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'slug', 'name', 'description',
        'cover_image_url', 'last_updated',
        'lessons', 'simulations', 'device_categories', 'device_frameworks',
        'device_documents'
    ]
    form_columns = [
        'id', 'slug', 'name', 'description',
        'cover_image_url', 'lessons', 'simulations', 'device_categories', 'device_frameworks',
        'device_documents'
    ]

    inline_models = [
        DeviceDocForm(DeviceDoc)
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(Device, db.session, *args, **kwargs)

class DeviceDocModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'device_id', 'device',
        'doc_url', 'title', 'description', 'last_updated'
    ]
    form_columns = [
        'id', 'device_id', 'device',
        'doc_url', 'title', 'description', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(DeviceDoc, db.session, *args, **kwargs)

class SupportedDeviceModelView(AuthedModelMixIn, ModelView):
    column_list = ['name', 'lessons', 'simulations']
    form_columns = ['name', 'lessons', 'simulations']

    def __init__(self, *args, **kwargs):
        super().__init__(SupportedDevice, db.session, *args, **kwargs)

# Category Views
class LessonCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'last_updated',
        'lessons'
    ]
    form_columns = [
        'id', 'name', 'slug', 'last_updated',
        'lessons'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LessonCategory, db.session, *args, **kwargs)

class SimulationCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'last_updated', 'simulations'
    ]
    form_columns = [
        'id', 'name', 'slug', 'last_updated', 'simulations'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(SimulationCategory, db.session, *args, **kwargs)

class DeviceCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'last_updated',
        'devices', 'simulations'
    ]
    form_columns = [
        'id', 'name', 'slug', 'last_updated',
        'devices', 'simulations'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(DeviceCategory, db.session, *args, **kwargs)

class DeviceFrameworkModelView(AuthedModelMixIn, ModelView):
    column_list = ['id', 'name', 'slug', 'last_updated', 'devices', 'simulations']
    form_columns = ['name', 'slug', 'devices', 'simulations']

    def __init__(self, *args, **kwargs):
        super().__init__(DeviceFramework, db.session, *args, **kwargs)

admin = Admin(name='Admin', template_mode='bootstrap3')
admin.add_view(AuthorModelView(name="Author", category="User"))
admin.add_view(UserModelView(name="User", category="User"))

admin.add_view(LessonModelView(name="Lesson", category="Lesson"))
admin.add_view(LessonVideosModelView(name="Lesson Video", category="Lesson"))
admin.add_view(LessonImagesModelView(name="Lesson Image", category="Lesson"))
admin.add_view(LessonDocsModelView(name="Lesson Document", category="Lesson"))

admin.add_view(SimulationModelView(name="Simulation", category="Simulation"))
admin.add_view(SimulationDocModelView(name="Simulation Document", category="Simulation"))
admin.add_view(SimulationCategoryModelView(name="Simulation Category", category="Category"))


admin.add_view(DeviceModelView(name="Device", category="Device"))
admin.add_view(DeviceDocModelView(name="Device Document", category="Device"))
admin.add_view(SupportedDeviceModelView(name="Supported Device", category="Device"))
admin.add_view(DeviceFrameworkModelView(name="Device Framework", category="Device"))

admin.add_view(LessonCategoryModelView(name="Lesson Category", category="Category"))
admin.add_view(DeviceCategoryModelView(name="Device Category", category="Category"))
admin.add_view(LessonLevelModelView(name="Lesson Level", category="Category"))