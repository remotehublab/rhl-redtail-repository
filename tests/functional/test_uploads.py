import io
from pathlib import Path

import pytest
from flask import Response

from redtail_repository import db
from redtail_repository.models import (
    LaboratoryExercise,
    LaboratoryExerciseDoc,
    SimulationDoc,
)
from redtail_repository.views import public as public_views


def upload(name: str = "guide.md", contents: bytes = b"# Uploaded guide"):
    return io.BytesIO(contents), name


def test_submission_access_is_limited_to_admins(client, catalog, login_as):
    anonymous = client.get("/file_submission")
    assert anonymous.status_code == 302
    assert "/login?next=" in anonymous.headers["Location"]

    login_as("verified-instructor")
    forbidden = client.get("/file_submission")
    assert forbidden.status_code == 302
    assert forbidden.headers["Location"] == "/"

    client.get("/logout")
    login_as("admin-user")
    allowed = client.get("/file_submission")
    assert allowed.status_code == 200
    assert b"Upload Document" in allowed.data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"title": "Guide", "target_type": "simulation"}, b"select a document"),
        (
            {"file": upload(), "title": "", "target_type": "simulation"},
            b"Document Title is required",
        ),
        (
            {"file": upload(), "title": "Guide", "target_type": "unknown"},
            b"valid document target",
        ),
        (
            {"file": upload(), "title": "Guide", "target_type": "simulation"},
            b"select a simulation",
        ),
        (
            {
                "file": upload(),
                "title": "Guide",
                "target_type": "exercise",
                "exercise_mode": "existing",
            },
            b"Select an exercise",
        ),
        (
            {
                "file": upload(),
                "title": "Guide",
                "target_type": "exercise",
                "exercise_mode": "new",
            },
            b"exercise name is required",
        ),
        (
            {
                "file": upload(),
                "title": "Guide",
                "target_type": "exercise",
                "exercise_mode": "new",
                "new_exercise_name": "Test Exercise",
            },
            b"already exists",
        ),
    ],
)
def test_submission_validation_does_not_write_files(
    client, app, catalog, login_as, data, expected
):
    login_as("admin-user")
    response = client.post(
        "/file_submission", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert expected.lower() in response.data.lower()
    assert list(Path(app.config["UPLOAD_FOLDER"]).iterdir()) == []


def test_admin_can_upload_a_simulation_document(client, app, catalog, login_as):
    login_as("admin-user")
    response = client.post(
        "/file_submission",
        data={
            "file": upload("simulation-guide.md"),
            "title": "New Simulation Guide",
            "description": "A new document",
            "target_type": "simulation",
            "simulation_id": str(catalog.simulation.id),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Successfully updated" in response.data
    document = SimulationDoc.query.filter_by(title="New Simulation Guide").one()
    assert document.simulation_id == catalog.simulation.id
    assert document.description == "A new document"
    saved = Path(app.config["UPLOAD_FOLDER"]) / document.doc_url.removeprefix(
        "/uploads/"
    )
    assert saved.read_bytes() == b"# Uploaded guide"


def test_admin_can_add_document_and_cover_to_existing_exercise(
    client, app, catalog, login_as
):
    login_as("admin-user")
    response = client.post(
        "/file_submission",
        data={
            "file": upload("solution.md", b"# New solution"),
            "update_exercise_cover": upload("cover.png", b"png-data"),
            "title": "Additional Solution",
            "description": "Instructor notes",
            "target_type": "exercise",
            "exercise_mode": "existing",
            "laboratory_exercise_id": str(catalog.exercise.id),
            "is_solution": "on",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    document = LaboratoryExerciseDoc.query.filter_by(title="Additional Solution").one()
    assert document.is_solution is True
    assert document.laboratory_exercise_id == catalog.exercise.id
    db.session.refresh(catalog.exercise)
    assert catalog.exercise.cover_image_url.startswith("/uploads/cover_")
    assert len(list(Path(app.config["UPLOAD_FOLDER"]).iterdir())) == 2


def test_uploaded_solutions_require_verified_access(
    client, app, catalog, login_as, monkeypatch
):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    private_root = Path(app.config["PRIVATE_FOLDER"])
    (upload_root / "public-guide.md").write_text("public", encoding="utf-8")
    (upload_root / "instructor-solution.md").write_text("solution", encoding="utf-8")
    (private_root / "private-solution.md").write_text(
        "private solution", encoding="utf-8"
    )
    catalog.exercise_doc.doc_url = "/uploads/public-guide.md"
    catalog.solution_doc.doc_url = (
        "https://redtail.example.test/uploads/instructor-solution.md"
    )
    private_solution = LaboratoryExerciseDoc(
        laboratory_exercise=catalog.exercise,
        title="Private Solution",
        doc_url="private/private-solution.md",
        is_solution=True,
    )
    db.session.add(private_solution)
    db.session.commit()

    public = client.get("/uploads/public-guide.md")
    anonymous_solution = client.get("/uploads/instructor-solution.md")
    anonymous_viewer = client.get(
        "/docs/markdown-viewer/uploads/instructor-solution.md"
    )
    anonymous_converter = client.get(
        "/docs/word-converter/uploads/instructor-solution.md"
    )
    anonymous_private_viewer = client.get(
        "/docs/markdown-viewer/private/private-solution.md"
    )

    assert public.status_code == 200
    assert public.get_data(as_text=True) == "public"
    assert public.headers["Cache-Control"] == "private, no-store"
    assert anonymous_solution.status_code == 404
    assert anonymous_viewer.status_code == 404
    assert anonymous_converter.status_code == 404
    assert anonymous_private_viewer.status_code == 404
    assert public_views._is_solution_document_path(
        "/uploads/nested/../instructor-solution.md"
    )
    assert public_views._is_solution_document_path(
        str(upload_root / "instructor-solution.md")
    )
    assert public_views._is_solution_document_path("private/private-solution.md")
    assert not public_views._is_solution_document_path("public/docs/exercise.md")

    login_as("student-user")
    unverified_solution = client.get("/uploads/instructor-solution.md")
    assert unverified_solution.status_code == 404
    client.get("/logout")

    login_as("verified-instructor")
    verified_solution = client.get("/uploads/instructor-solution.md")
    assert verified_solution.status_code == 200
    assert verified_solution.get_data(as_text=True) == "solution"
    assert verified_solution.headers["Cache-Control"] == "private, no-store"
    assert verified_solution.headers["X-Robots-Tag"] == "noindex, nofollow"

    verified_viewer = client.get(
        "/docs/markdown-viewer/uploads/instructor-solution.md"
    )
    assert verified_viewer.status_code == 200
    assert b"solution" in verified_viewer.data
    assert verified_viewer.headers["Cache-Control"] == "private, no-store"
    assert verified_viewer.headers["X-Robots-Tag"] == "noindex, nofollow"
    assert b'<meta name="robots" content="noindex, nofollow">' in verified_viewer.data

    verified_private_viewer = client.get(
        "/docs/markdown-viewer/private/private-solution.md"
    )
    assert verified_private_viewer.status_code == 200
    assert b"private solution" in verified_private_viewer.data
    assert verified_private_viewer.headers["Cache-Control"] == "private, no-store"

    def converted_word(_path):
        return Response(
            b"docx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

    monkeypatch.setattr(public_views, "_get_word", converted_word)
    verified_converter = client.get(
        "/docs/word-converter/uploads/instructor-solution.md"
    )
    assert verified_converter.status_code == 200
    assert verified_converter.headers["Cache-Control"] == "private, no-store"
    assert verified_converter.headers["X-Robots-Tag"] == "noindex, nofollow"

    client.get("/logout")
    catalog.admin.verified = False
    db.session.commit()
    login_as("admin-user")
    assert client.get("/uploads/instructor-solution.md").status_code == 200


def test_admin_can_create_a_fully_related_exercise(client, app, catalog, login_as):
    login_as("admin-user")
    response = client.post(
        "/file_submission",
        data={
            "file": upload("new-exercise.md"),
            "new_exercise_cover": upload("new-cover.png", b"cover"),
            "title": "New Exercise Guide",
            "target_type": "exercise",
            "exercise_mode": "new",
            "new_exercise_name": "A Brand New Exercise",
            "new_exercise_desc": "Short description",
            "new_exercise_long_desc": "Long description",
            "new_exercise_goals": "Test everything",
            "author_ids": [str(catalog.author.id)],
            "category_ids": [str(catalog.exercise_category.id)],
            "level_ids": [str(catalog.level.id)],
            "framework_ids": [str(catalog.framework.id)],
            "simulation_ids": [str(catalog.simulation.id)],
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    exercise = LaboratoryExercise.query.filter_by(slug="a-brand-new-exercise").one()
    assert exercise.short_description == "Short description"
    assert [author.id for author in exercise.authors] == [catalog.author.id]
    assert [category.id for category in exercise.laboratory_exercise_categories] == [
        catalog.exercise_category.id
    ]
    assert [level.id for level in exercise.levels] == [catalog.level.id]
    assert [framework.id for framework in exercise.device_frameworks] == [
        catalog.framework.id
    ]
    assert [simulation.id for simulation in exercise.simulations] == [
        catalog.simulation.id
    ]
    assert exercise.laboratory_exercise_documents[0].title == "New Exercise Guide"
    assert len(list(Path(app.config["UPLOAD_FOLDER"]).iterdir())) == 2


def test_submission_replaces_only_a_document_owned_by_the_exercise(
    client, app, catalog, login_as
):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    old_file = upload_root / "old.md"
    old_file.write_text("old", encoding="utf-8")
    catalog.exercise_doc.doc_url = "/uploads/old.md"
    other_exercise = LaboratoryExercise(
        name="Other Exercise",
        slug="other-exercise",
        short_description="Other",
        active=True,
    )
    other_doc = LaboratoryExerciseDoc(
        laboratory_exercise=other_exercise,
        title="Other Document",
        doc_url="public/docs/other.md",
    )
    db.session.add(other_doc)
    db.session.commit()

    login_as("admin-user")
    rejected = client.post(
        "/file_submission",
        data={
            "file": upload("wrong.md"),
            "title": "Wrong replacement",
            "target_type": "exercise",
            "exercise_mode": "existing",
            "laboratory_exercise_id": str(catalog.exercise.id),
            "replace_doc_id": str(other_doc.id),
        },
        content_type="multipart/form-data",
    )
    assert b"does not belong" in rejected.data
    assert old_file.exists()
    assert sorted(path.name for path in upload_root.iterdir()) == ["old.md"]

    replaced = client.post(
        "/file_submission",
        data={
            "file": upload("replacement.md", b"replacement"),
            "title": "Replaced Exercise Guide",
            "description": "Updated",
            "target_type": "exercise",
            "exercise_mode": "existing",
            "laboratory_exercise_id": str(catalog.exercise.id),
            "replace_doc_id": str(catalog.exercise_doc.id),
            "is_solution": "on",
        },
        content_type="multipart/form-data",
    )
    assert b"Successfully updated" in replaced.data
    db.session.refresh(catalog.exercise_doc)
    assert catalog.exercise_doc.title == "Replaced Exercise Guide"
    assert catalog.exercise_doc.is_solution is True
    assert not old_file.exists()
    assert len(list(upload_root.iterdir())) == 1


def test_submission_cleans_new_files_when_database_commit_fails(
    client, app, catalog, login_as, monkeypatch
):
    login_as("admin-user")

    def fail_commit():
        raise RuntimeError("database unavailable")

    def remove_then_report_missing(path):
        Path(path).unlink()
        raise FileNotFoundError(path)

    monkeypatch.setattr(db.session, "commit", fail_commit)
    monkeypatch.setattr(
        "redtail_repository.views.public.os.remove", remove_then_report_missing
    )
    response = client.post(
        "/file_submission",
        data={
            "file": upload("will-rollback.md"),
            "title": "Will Roll Back",
            "target_type": "simulation",
            "simulation_id": str(catalog.simulation.id),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"database unavailable" in response.data
    assert list(Path(app.config["UPLOAD_FOLDER"]).iterdir()) == []


def test_submission_keeps_success_when_old_upload_cleanup_fails(
    client, app, catalog, login_as, monkeypatch, caplog
):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    old_file = upload_root / "undeletable.md"
    old_file.write_text("old", encoding="utf-8")
    catalog.exercise_doc.doc_url = "/uploads/undeletable.md"
    db.session.commit()
    login_as("admin-user")

    def fail_remove(_path):
        raise OSError("permission denied")

    monkeypatch.setattr("redtail_repository.views.public.os.remove", fail_remove)
    response = client.post(
        "/file_submission",
        data={
            "file": upload("replacement.md"),
            "title": "Committed replacement",
            "target_type": "exercise",
            "exercise_mode": "existing",
            "laboratory_exercise_id": str(catalog.exercise.id),
            "replace_doc_id": str(catalog.exercise_doc.id),
        },
        content_type="multipart/form-data",
    )

    assert b"Successfully updated" in response.data
    assert old_file.exists()
    assert "Could not remove replaced upload" in caplog.text


@pytest.mark.parametrize("doc_type", ["exercise", "simulation"])
def test_replace_document_updates_file_and_title_after_commit(
    client, app, catalog, login_as, doc_type
):
    document = catalog.exercise_doc if doc_type == "exercise" else catalog.simulation_doc
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    old_file = upload_root / f"old-{doc_type}.md"
    old_file.write_text("old", encoding="utf-8")
    document.doc_url = f"/uploads/{old_file.name}"
    db.session.commit()

    login_as("admin-user")
    response = client.post(
        f"/replace_document/{doc_type}/{document.id}",
        data={
            "new_file": upload("replacement.md", b"replacement"),
            "new_title": "Replacement Title",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    db.session.refresh(document)
    assert document.title == "Replacement Title"
    assert document.doc_url.startswith("/uploads/")
    assert not old_file.exists()
    new_file = upload_root / document.doc_url.removeprefix("/uploads/")
    assert new_file.read_bytes() == b"replacement"


def test_replace_document_handles_bad_targets_and_missing_documents(
    client, catalog, login_as
):
    assert client.post(f"/replace_document/exercise/{catalog.exercise_doc.id}").status_code == 302

    login_as("admin-user")
    assert client.post("/replace_document/unknown/1").status_code == 400
    assert client.post("/replace_document/exercise/99999").status_code == 404
    assert client.post("/replace_document/simulation/99999").status_code == 404


def test_replace_document_rolls_back_and_cleans_new_file_on_commit_failure(
    client, app, catalog, login_as, monkeypatch
):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    old_file = upload_root / "old.md"
    old_file.write_text("old", encoding="utf-8")
    catalog.exercise_doc.doc_url = "/uploads/old.md"
    db.session.commit()
    old_url = catalog.exercise_doc.doc_url
    old_title = catalog.exercise_doc.title
    login_as("admin-user")

    def fail_commit():
        raise RuntimeError("database unavailable")

    def remove_then_report_missing(path):
        Path(path).unlink()
        raise FileNotFoundError(path)

    monkeypatch.setattr(db.session, "commit", fail_commit)
    monkeypatch.setattr(
        "redtail_repository.views.public.os.remove", remove_then_report_missing
    )
    response = client.post(
        f"/replace_document/exercise/{catalog.exercise_doc.id}",
        data={
            "new_file": upload("new.md"),
            "new_title": "Not committed",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert old_file.exists()
    assert sorted(path.name for path in upload_root.iterdir()) == ["old.md"]
    db.session.refresh(catalog.exercise_doc)
    assert catalog.exercise_doc.doc_url == old_url
    assert catalog.exercise_doc.title == old_title


def test_replace_document_keeps_success_when_old_upload_cleanup_fails(
    client, app, catalog, login_as, monkeypatch, caplog
):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    old_file = upload_root / "undeletable.md"
    old_file.write_text("old", encoding="utf-8")
    catalog.exercise_doc.doc_url = "/uploads/undeletable.md"
    db.session.commit()
    login_as("admin-user")

    def fail_remove(_path):
        raise OSError("permission denied")

    monkeypatch.setattr("redtail_repository.views.public.os.remove", fail_remove)
    response = client.post(
        f"/replace_document/exercise/{catalog.exercise_doc.id}",
        data={"new_file": upload("replacement.md")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert old_file.exists()
    assert "Could not remove replaced upload" in caplog.text


def test_uploaded_files_are_served_from_the_configured_folder(
    client, app, catalog
):
    upload_root = Path(app.config["UPLOAD_FOLDER"])
    (upload_root / "served.md").write_text("served", encoding="utf-8")
    assert client.get("/uploads/served.md").data == b"served"
    assert client.get("/uploads/missing.md").status_code == 404
