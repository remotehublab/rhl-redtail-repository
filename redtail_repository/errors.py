from flask import Flask, render_template
from flask_babel import gettext
from werkzeug.exceptions import HTTPException

from .seo import page_metadata


def _error_copy(status_code: int):
    return {
        403: (
            gettext("Access restricted"),
            gettext("You do not have permission to view this page."),
        ),
        404: (
            gettext("Page not found"),
            gettext("The page you requested may have moved or may no longer exist."),
        ),
        500: (
            gettext("Something went wrong"),
            gettext("We could not complete your request. Please try again later."),
        ),
    }[status_code]


def _error_message(error: HTTPException, fallback: str) -> str:
    description = str(error.description or "").strip()
    default_description = str(error.__class__.description or "").strip()
    if description and description != default_description:
        return description
    return fallback


def _render_error(error: HTTPException, status_code: int):
    title, fallback_message = _error_copy(status_code)
    message = _error_message(error, fallback_message)
    metadata = page_metadata(
        title=f"{title} | REDTAIL",
        description=message,
        include_canonical=False,
    )
    metadata["seo_robots"] = "noindex, noarchive"
    return (
        render_template(
            "public/error.html",
            status_code=status_code,
            error_title=title,
            message=message,
            **metadata,
        ),
        status_code,
    )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(error):
        return _render_error(error, 403)

    @app.errorhandler(404)
    def page_not_found(error):
        return _render_error(error, 404)

    @app.errorhandler(500)
    def internal_server_error(error):
        return _render_error(error, 500)
