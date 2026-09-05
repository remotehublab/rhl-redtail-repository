import atexit
import logging
import os
import shutil
import tempfile
from pathlib import Path

from redtail_repository import create_app, db
from tests.data import seed_catalog
from tests.error_routes import register_test_error_routes


def build_browser_app():
    runtime_root = Path(tempfile.mkdtemp(prefix="redtail-browser-tests-"))
    atexit.register(shutil.rmtree, runtime_root, ignore_errors=True)
    public_folder = runtime_root / "public"
    private_folder = runtime_root / "private"
    upload_folder = runtime_root / "uploads"
    for folder in (public_folder, private_folder, upload_folder):
        folder.mkdir()

    app = create_app(
        "testing",
        {
            "PROJECT_ROOT": str(runtime_root),
            "PUBLIC_FOLDER": str(public_folder),
            "PRIVATE_FOLDER": str(private_folder),
            "UPLOAD_FOLDER": str(upload_folder),
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{runtime_root / 'browser.sqlite'}",
            "KNOWN_DOMAINS": ("docs.example.test",),
            "PROPAGATE_EXCEPTIONS": False,
        },
    )
    register_test_error_routes(app)
    with app.app_context():
        db.create_all()
        seed_catalog()
    return app


if __name__ == "__main__":
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    build_browser_app().run(
        host="127.0.0.1",
        port=int(os.environ.get("REDTAIL_BROWSER_PORT", "5010")),
        debug=False,
        use_reloader=False,
    )
