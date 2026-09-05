import logging

import pytest

from redtail_repository.views.public import _document_response


@pytest.mark.parametrize(
    ("path", "status_code", "heading", "message"),
    [
        (
            "/_test/errors/403",
            403,
            "Access restricted",
            "You do not have permission to view this page.",
        ),
        (
            "/missing-page",
            404,
            "Page not found",
            "The page you requested may have moved or may no longer exist.",
        ),
    ],
)
def test_error_pages_are_branded_and_recoverable(
    client, path, status_code, heading, message
):
    response = client.get(path)
    body = response.data.decode()

    assert response.status_code == status_code
    assert f"<title>{heading} | REDTAIL</title>" in body
    assert f'<p class="error-code" aria-hidden="true">{status_code}</p>' in body
    assert f'<h1 id="error-title">{heading}</h1>' in body
    assert message in body
    assert 'href="/">Go to home</a>' in body
    assert 'href="/laboratory-exercises">Browse exercises</a>' in body
    assert 'href="/simulations">Explore simulations</a>' in body
    assert '<meta name="robots" content="noindex, noarchive">' in body
    assert '<link rel="canonical"' not in body
    assert response.headers["Cache-Control"] == (
        "no-store, no-cache, must-revalidate"
    )
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["X-Robots-Tag"] == "noindex, noarchive"


def test_route_specific_not_found_uses_shared_error_presentation(client, catalog):
    response = client.get("/authors/99999")
    body = response.data.decode()

    assert response.status_code == 404
    assert '<h1 id="error-title">Page not found</h1>' in body
    assert "Author not found." in body
    assert 'class="error-actions"' in body


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (403, "This document cannot be accessed."),
        (404, "The requested document could not be found."),
        (500, "We could not load this document. Please try again later."),
    ],
)
def test_document_reader_errors_use_safe_shared_pages(
    client, monkeypatch, status_code, message
):
    monkeypatch.setattr(
        "redtail_repository.views.public._get_html",
        lambda _path: ("private filesystem detail", status_code),
    )

    response = client.get("/docs/markdown-viewer/blocked.md")
    body = response.data.decode()

    assert response.status_code == status_code
    assert message in body
    assert "private filesystem detail" not in body
    assert response.headers["Cache-Control"] == (
        "no-store, no-cache, must-revalidate"
    )


def test_document_reader_preserves_non_error_and_unsupported_responses():
    assert _document_response("document body") == "document body"
    assert _document_response(("unsupported", 400)) == ("unsupported", 400)


def test_unexpected_server_error_is_logged_without_leaking_details(client, caplog):
    with caplog.at_level(logging.ERROR):
        response = client.get("/_test/errors/500")
    body = response.data.decode()

    assert response.status_code == 500
    assert '<h1 id="error-title">Something went wrong</h1>' in body
    assert "We could not complete your request. Please try again later." in body
    assert "private test exception" not in body
    assert "Traceback" not in body
    assert response.headers["Cache-Control"] == (
        "no-store, no-cache, must-revalidate"
    )
    assert any(
        "Exception on /_test/errors/500" in record.message
        for record in caplog.records
    )
