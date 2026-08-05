from types import SimpleNamespace

from redtail_repository.models import User
from redtail_repository.views.admin import (
    LaboratoryExerciseModelView,
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
