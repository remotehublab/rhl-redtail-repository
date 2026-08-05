from types import SimpleNamespace

import redtail_repository
from redtail_repository import create_app, get_locale


def test_create_app_applies_overrides_before_extensions(tmp_path):
    public = tmp_path / "web"
    private = tmp_path / "restricted"
    uploads = tmp_path / "uploads"
    for folder in (public, private, uploads):
        folder.mkdir()

    app = create_app(
        "testing",
        {
            "PUBLIC_FOLDER": str(public),
            "PRIVATE_FOLDER": str(private),
            "UPLOAD_FOLDER": str(uploads),
        },
    )

    assert app.testing
    assert app.config["PUBLIC_FOLDER"] == str(public)
    assert "admin" in app.extensions
    assert app.url_map.is_endpoint_expecting("public.simulation", "simulation_slug")


def test_create_app_works_without_overrides():
    app = create_app("testing")
    assert app.testing
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"


def test_locale_defaults_to_english_outside_request(app):
    redtail_repository.SUPPORTED_TRANSLATIONS = None
    with app.app_context():
        assert get_locale() == "en"


def test_locale_query_session_and_accept_language(app, monkeypatch):
    translations = [
        SimpleNamespace(language="es", territory=None),
        SimpleNamespace(language="pt", territory="BR"),
    ]
    monkeypatch.setattr(redtail_repository.babel, "list_translations", lambda: translations)
    redtail_repository.SUPPORTED_TRANSLATIONS = None

    with app.test_request_context("/?locale=es"):
        assert get_locale() == "es"

    with app.test_request_context("/", headers={"Accept-Language": "pt-BR,es;q=0.8"}):
        assert get_locale() == "pt_BR"

    with app.test_request_context("/?locale=xx"):
        from flask import session

        session["locale"] = "es"
        assert get_locale() == "es"


def test_language_listing_is_cached_and_tolerates_display_name_failure(app, monkeypatch):
    class Translation:
        language = "zz"
        territory = None

        def get_display_name(self, _language):
            raise RuntimeError("no display name")

    monkeypatch.setattr(redtail_repository.babel, "list_translations", lambda: [Translation()])
    redtail_repository.SUPPORTED_LANGUAGES = None

    with app.test_request_context("/"):
        context = next(
            processor()
            for processor in app.template_context_processors[None]
            if "list_languages" in processor()
        )
        first = context["list_languages"]()
        second = context["list_languages"]()

    assert first is second
    assert first["zz"] == "zz"
