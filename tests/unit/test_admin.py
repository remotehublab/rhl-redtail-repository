from types import SimpleNamespace

from flask_login import login_user

from redtail_repository.models import User
from redtail_repository.views.admin import (
    DeviceDocModelView,
    LaboratoryExerciseModelView,
    SimulationDeviceDocumentForm,
    UserModelView,
)


def test_user_admin_form_requires_and_hashes_password(app):
    with app.test_request_context("/admin/user/new/"):
        view = UserModelView()
        form = view.create_form()
        assert form.password.validators

        user = User(login="admin-created", name="Admin Created", verified=False)
        view.on_model_change(
            SimpleNamespace(password=SimpleNamespace(data="secure-password")),
            user,
            True,
        )
        assert user.check_password("secure-password")

        password_hash = user.password_hash
        view.on_model_change(
            SimpleNamespace(password=SimpleNamespace(data="")), user, False
        )
        assert user.password_hash == password_hash


def test_exercise_admin_category_formatter_handles_both_states(catalog):
    formatter = LaboratoryExerciseModelView._format_categories
    assert formatter(None, None, catalog.exercise, None) == "Fundamentals"
    catalog.exercise.laboratory_exercise_categories = []
    assert formatter(None, None, catalog.exercise, None) == "No Categories"


def test_admin_views_attribute_direct_and_inline_material_changes(app, catalog):
    with app.test_request_context("/admin/"):
        login_user(catalog.admin)

        direct_view = DeviceDocModelView()
        direct_view.on_model_change(None, catalog.device_doc, True)
        assert catalog.device_doc.uploaded_by_user_id == catalog.admin.id
        assert catalog.device_doc.updated_by_user_id == catalog.admin.id

        inline_view = SimulationDeviceDocumentForm(
            catalog.simulation_device_doc.__class__
        )
        catalog.simulation_device_doc.mark_created_by(catalog.instructor)
        inline_view.on_model_change(None, catalog.simulation_device_doc, False)
        assert (
            catalog.simulation_device_doc.uploaded_by_user_id
            == catalog.instructor.id
        )
        assert catalog.simulation_device_doc.updated_by_user_id == catalog.admin.id
