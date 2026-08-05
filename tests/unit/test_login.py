import pytest

from redtail_repository import db
from redtail_repository.models import User
from redtail_repository.views.login import is_safe_local_redirect


@pytest.mark.parametrize("target", ["/", "/simulations", "/path?query=yes"])
def test_safe_local_redirects(target):
    assert is_safe_local_redirect(target)


@pytest.mark.parametrize(
    "target", [None, "", "simulations", "//evil.test", "https://evil.test", "javascript:x"]
)
def test_unsafe_redirects_are_rejected(target):
    assert not is_safe_local_redirect(target)


def test_registration_validates_and_logs_user_in(client, app):
    response = client.post(
        "/register",
        data={
            "login": "new-user",
            "name": "New User",
            "password": "new-password",
            "confirm_password": "new-password",
        },
    )
    assert response.status_code == 302
    assert response.location == "/"
    with app.app_context():
        user = User.query.filter_by(login="new-user").one()
        assert user.check_password("new-password")
        assert user.verified is False


def test_registration_rejects_invalid_and_duplicate_users(client, app):
    invalid = client.post(
        "/register",
        data={
            "login": "x",
            "name": "N",
            "password": "short",
            "confirm_password": "different",
        },
    )
    assert invalid.status_code == 200
    assert b"Field must be between 4 and 25 characters long" in invalid.data

    with app.app_context():
        existing = User(login="existing", name="Existing User", verified=False)
        existing.set_password("password")
        db.session.add(existing)
        db.session.commit()

    duplicate = client.post(
        "/register",
        data={
            "login": "existing",
            "name": "Existing Again",
            "password": "password",
            "confirm_password": "password",
        },
    )
    assert duplicate.status_code == 200
    assert b"Username is already taken" in duplicate.data


def test_login_logout_and_redirect_handling(client, catalog):
    bad = client.post("/login", data={"username": "admin-user", "password": "bad"})
    assert bad.status_code == 200
    assert b"Invalid username or password" in bad.data

    good = client.post(
        "/login?next=/simulations",
        data={"username": "admin-user", "password": "test-password"},
    )
    assert good.status_code == 302
    assert good.location == "/simulations"

    logout = client.get("/logout?url=/devices")
    assert logout.status_code == 302
    assert logout.location == "/devices"

    client.get("/logout")
    legacy = client.post(
        "/login?url=/devices",
        data={"username": "admin-user", "password": "test-password"},
    )
    assert legacy.status_code == 302
    assert legacy.location == "/devices"


def test_login_never_redirects_to_external_host(client, catalog):
    response = client.post(
        "/login?next=//evil.test",
        data={"username": "admin-user", "password": "test-password"},
    )
    assert response.status_code == 302
    assert response.location == "/"

    response = client.get("/logout?url=https://evil.test")
    assert response.location == "/"
