import os.path
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_login import current_user

from wtforms import PasswordField
from wtforms.validators import DataRequired

from ..models import (
    Author, User, LaboratoryExercise, LaboratoryExerciseImage, LaboratoryExerciseDoc,
    Simulation, Device, LaboratoryExerciseCategory, LaboratoryExerciseLevel,
    DeviceCategory, SimulationCategory, DeviceDoc, SimulationDoc,
    DeviceFramework, SimulationDeviceDocument, SimulationImage,
    device_simulation_association, author_laboratory_exercise_association,
    laboratory_exercise_simulation_association, laboratory_exercise_device_framework_association,
    device_category_association, simulation_category_association, 
    laboratory_exercise_level_association, simulation_framework_association,
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

class ConnectedAuthorModelView(AuthedModelMixIn, ModelView):
    column_list = ['login', 'name']

    def get_query(self):
        return super().get_query().join(User).filter(User.author_id == Author.id)

    def get_count_query(self):
        return super().get_count_query().join(User).filter(User.author_id == Author.id)

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

class LaboratoryExerciseVideoForm(InlineFormAdmin):
    pass

class LaboratoryExerciseImageForm(InlineFormAdmin):
    pass

class LaboratoryExerciseDocsForm(InlineFormAdmin):
    pass

class SimulationDocForm(InlineFormAdmin):
    pass

class DeviceDocForm(InlineFormAdmin):
    pass

class SimulationImageForm(InlineFormAdmin):
    pass

class LaboratoryExerciseModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'short_description', 'long_description', 'active',
        'cover_image_url', 'video_url', 'learning_goals', 'levels',
        'last_updated',
        'authors', 'simulations', 'laboratory_exercise_categories',
        'device_frameworks','laboratory_exercise_images', 'laboratory_exercise_documents'
    ]

    column_searchable_list = ['name', 'slug', 'short_description', 'long_description', 'learning_goals', 'authors.name']
    column_filters = ['name', 'slug', 'short_description', 'long_description', 'learning_goals', 'active', 'levels', 'last_updated']

    form_columns = [
        'id', 'name', 'slug', 'short_description', 'active',
        'cover_image_url', 'long_description', 'learning_goals', 'levels',
        'authors', 'simulations', 'laboratory_exercise_categories',
        'device_frameworks',
        'laboratory_exercise_images', 'laboratory_exercise_documents'
    ]

    inline_models = [
        LaboratoryExerciseImageForm(LaboratoryExerciseImage),
        LaboratoryExerciseDocsForm(LaboratoryExerciseDoc),
    ]

    def _format_categories(view, context, model, name):
        return ", ".join(category.name for category in model.laboratory_exercise_categories) if model.laboratory_exercise_categories else "No Categories"

    column_formatters = {'laboratory_exercise_categories': _format_categories}

    def __init__(self, *args, **kwargs):
        super().__init__(LaboratoryExercise, db.session, *args, **kwargs)

class LaboratoryExerciseImagesModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'laboratory_exercise_id', 'laboratory_exercise',
        'title', 'image_url', 'description', 'last_updated'
    ]
    form_columns = [
        'id', 'laboratory_exercise_id', 'laboratory_exercise',
        'title', 'image_url', 'description', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LaboratoryExerciseImage, db.session, *args, **kwargs)

class LaboratoryExerciseDocsModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'laboratory_exercise_id', 'laboratory_exercise',
        'title', 'doc_url', 'description', 'is_solution', 'last_updated'
    ]
    form_columns = [
        'id', 'laboratory_exercise_id', 'laboratory_exercise',
        'title', 'doc_url', 'description', 'is_solution', 'last_updated'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LaboratoryExerciseDoc, db.session, *args, **kwargs)

class LaboratoryExerciseLevelModelView(AuthedModelMixIn, ModelView):
    column_list = ['id', 'name', 'slug', 'last_updated', 'laboratory_exercises']
    form_columns = ['name', 'slug', 'laboratory_exercises']

    def __init__(self, *args, **kwargs):
        super().__init__(LaboratoryExerciseLevel, db.session, *args, **kwargs)

class LaboratoryExerciseCategoryModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'last_updated',
        'laboratory_exercises'
    ]
    form_columns = [
        'id', 'name', 'slug', 'last_updated',
        'laboratory_exercises'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(LaboratoryExerciseCategory, db.session, *args, **kwargs)

class SimulationModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'id', 'name', 'slug', 'authors', 'description',
        'cover_image_url', 'video_url', 'last_updated',
        'laboratory_exercises', 'devices', 'simulation_images',
        'simulation_categories', 'simulation_device_categories',
        'device_frameworks',
        'simulation_documents', 
    ]
    form_columns = [
        'id', 'name', 'slug', 'authors', 'description',
        'cover_image_url', 
        'laboratory_exercises', 'devices', 'simulation_images',
        'simulation_categories', 'simulation_device_categories',
        'device_frameworks',
        'simulation_documents', 
    ]

    inline_models = [
        SimulationDocForm(SimulationDoc),
        SimulationImageForm(SimulationImage),
        SimulationDeviceDocument,
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
        'simulations', 'device_categories', 'device_frameworks',
        'device_documents'
    ]
    form_columns = [
        'id', 'slug', 'name', 'description',
        'cover_image_url', 'simulations', 'device_categories', 'device_frameworks',
        'device_documents'
    ]

    inline_models = [
        DeviceDocForm(DeviceDoc),
        DeviceFramework,
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

class SimulationDeviceDocumentModelView(AuthedModelMixIn, ModelView):
    column_list = [
        'simulation',
        'device', 'name', 'doc_url'
    ]
    form_columns = [
        'simulation',
        'device', 'name', 'doc_url'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(SimulationDeviceDocument, db.session, *args, **kwargs)

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


# A FileAdmin that only lets admins in
class FileBrowser(AuthedModelMixIn, FileAdmin):
    pass

# compute the absolute paths to your two folders
public_path  = os.path.join(os.path.abspath('.'), 'public')
private_path = os.path.join(os.path.abspath('.'), 'private')

admin = Admin(name='Admin', template_mode='bootstrap3')
admin.add_view(AuthorModelView(name="Author", category="User"))
admin.add_view(ConnectedAuthorModelView(name="Connected Authors", category="User", endpoint="connected_authors"))
admin.add_view(UserModelView(name="User", category="User"))

admin.add_view(LaboratoryExerciseModelView(name="Laboratory Exercise", category="Laboratory Exercise"))
admin.add_view(LaboratoryExerciseImagesModelView(name="Laboratory Exercise Image", category="Laboratory Exercise"))
admin.add_view(LaboratoryExerciseDocsModelView(name="Laboratory Exercise Document", category="Laboratory Exercise"))

admin.add_view(SimulationModelView(name="Simulation", category="Simulation"))
admin.add_view(SimulationDocModelView(name="Simulation Document", category="Simulation"))
admin.add_view(SimulationCategoryModelView(name="Simulation Category", category="Category"))
admin.add_view(SimulationDeviceDocumentModelView(name="Simulation Device Document", category="Simulation"))

admin.add_view(DeviceModelView(name="Device", category="Device"))
admin.add_view(DeviceDocModelView(name="Device Document", category="Device"))

admin.add_view(LaboratoryExerciseCategoryModelView(name="Laboratory Exercise Category", category="Category"))
admin.add_view(DeviceCategoryModelView(name="Device Category", category="Category"))
admin.add_view(LaboratoryExerciseLevelModelView(name="Laboratory Exercise Level", category="Category"))

admin.add_view(
    FileBrowser(
        public_path,
        '/public/',
        name='Public Files',
        endpoint="files/public",
        category='Files'
    )
)
admin.add_view(
    FileBrowser(
        private_path,
        '/private/',
        name='Private Files',
        endpoint="files/private",
        category='Files'
    )
)