from pathlib import Path

import pytest

from redtail_repository import create_app, db


@pytest.fixture
def app(tmp_path: Path):
    public_folder = tmp_path / "public"
    private_folder = tmp_path / "private"
    upload_folder = tmp_path / "uploads"
    for folder in (public_folder, private_folder, upload_folder):
        folder.mkdir()

    application = create_app(
        "testing",
        {
            "PROJECT_ROOT": str(tmp_path),
            "PUBLIC_FOLDER": str(public_folder),
            "PRIVATE_FOLDER": str(private_folder),
            "UPLOAD_FOLDER": str(upload_folder),
            "KNOWN_DOMAINS": ("docs.example.test",),
        },
    )

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def catalog(app):
    from tests.data import seed_catalog

    return seed_catalog()


@pytest.fixture
def login_as(client):
    def _login(username: str, password: str = "test-password"):
        return client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    return _login
