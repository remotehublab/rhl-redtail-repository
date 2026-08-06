from pathlib import Path

import pytest
import requests
import responses

from redtail_repository.views import public


def test_image_path_rewriting_and_base_urls():
    markdown = "![one](image.png) ![two](/root.png) ![three](https://example.test/a.png)"
    rewritten = public.secure_image_paths(markdown, "/docs/")
    assert "![one](/docs/image.png)" in rewritten
    assert "![two](/root.png)" in rewritten
    assert "![three](https://example.test/a.png)" in rewritten

    assert public.get_image_base_url("public/docs/guide.md") == "/public/docs/"
    assert public.get_image_base_url("/uploads/guide.md") == "/uploads/"
    assert (
        public.get_image_base_url("https://docs.example.test/guides/guide.md")
        == "https://docs.example.test/guides/"
    )


def test_get_md_validates_extensions_and_local_boundaries(app, tmp_path):
    root = Path(app.config["PROJECT_ROOT"])
    valid = root / "guide.md"
    valid.write_text("# Guide", encoding="utf-8")
    assert public._get_md("guide.md") == "# Guide"
    uploads = Path(app.config["UPLOAD_FOLDER"])
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / "uploaded.md").write_text("# Uploaded", encoding="utf-8")
    assert public._get_md("/uploads/uploaded.md") == "# Uploaded"
    assert public._get_md("guide.txt") == ("Unsupported file type", 400)

    outside = tmp_path.parent / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    assert public._get_md(str(outside)) == ("Access denied", 403)

    missing, status = public._get_md("missing.md")
    assert status == 404
    assert "Could not find local file" in missing


def test_get_md_rejects_symlink_escape(app, tmp_path):
    root = Path(app.config["PROJECT_ROOT"])
    outside = tmp_path.parent / "secret.md"
    outside.write_text("secret", encoding="utf-8")
    link = root / "link.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not available")
    assert public._get_md("link.md") == ("Access denied", 403)


def test_get_md_denies_path_when_common_root_cannot_be_compared(app, monkeypatch):
    monkeypatch.setattr(
        public.os.path,
        "commonpath",
        lambda _paths: (_ for _ in ()).throw(ValueError("different drives")),
    )
    assert public._get_md("guide.md") == ("Access denied", 403)


def test_document_source_availability_and_public_path_resolution(app):
    public_doc = Path(app.config["PROJECT_ROOT"]) / "public" / "docs" / "guide.md"
    public_doc.parent.mkdir(parents=True, exist_ok=True)
    public_doc.write_text("# Public guide", encoding="utf-8")

    assert public._resolve_local_document_path("/public/docs/guide.md") == str(
        public_doc
    )
    assert public._document_source_available("/public/docs/guide.md")
    assert not public._document_source_available("")
    assert public._document_source_available("https://docs.example.test/guide.md")
    assert not public._document_source_available("https://evil.test/guide.md")


def test_upload_reference_resolution_is_normalized_and_bounded(app, monkeypatch):
    upload = Path(app.config["UPLOAD_FOLDER"]) / "solution.md"
    upload.write_text("solution", encoding="utf-8")

    assert public._resolved_upload_reference("/uploads/solution.md") == str(upload)
    assert public._resolved_upload_reference("uploads/solution.md") == str(upload)
    assert public._resolved_upload_reference(
        "https://redtail.example.test/uploads/solution.md"
    ) == str(upload)
    assert public._resolved_upload_reference(str(upload)) == str(upload)
    assert public._resolved_upload_reference("") is None
    assert public._resolved_upload_reference("/outside-redtail/guide.md") is None
    assert public._document_reference_key(
        "https://docs.example.test/guide.md#section"
    ) == ("remote", "https://docs.example.test/guide.md")
    assert not public._is_solution_document_path("/outside-redtail/guide.md")

    monkeypatch.setattr(
        public.os.path,
        "commonpath",
        lambda _paths: (_ for _ in ()).throw(ValueError("different drives")),
    )
    assert public._resolved_upload_reference("/uploads/solution.md") is None


def test_document_source_availability_allows_remote_without_app_context():
    assert public._document_source_available("https://remote.example.test/guide.md")


def test_get_md_reports_unexpected_local_read_errors(app, monkeypatch):
    guide = Path(app.config["PROJECT_ROOT"]) / "guide.md"
    guide.write_text("# Guide", encoding="utf-8")

    def denied_open(*_args, **_kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(public, "open", denied_open, raising=False)
    message, status = public._get_md("guide.md")
    assert status == 500
    assert "Could not open local file" in message


@responses.activate
def test_get_md_remote_allowlist_success_and_failure(app):
    allowed = "https://docs.example.test/guide.md"
    responses.get(allowed, body="# Remote", status=200)
    assert public._get_md(allowed) == "# Remote"

    assert public._get_md("https://evil.test/guide.md") == ("Domain not allowed", 403)

    failing = "https://docs.example.test/failing.md"
    responses.get(failing, body="failure", status=500)
    message, status = public._get_md(failing)
    assert status == 404
    assert failing in message


@responses.activate
def test_get_md_remote_uses_environment_allowlist_without_an_app(monkeypatch):
    allowed = "https://environment.example.test/guide.md"
    monkeypatch.setenv("KNOWN_DOMAINS", "environment.example.test")
    responses.get(allowed, body="# Environment remote", status=200)
    assert public._get_md(allowed) == "# Environment remote"


def test_get_html_converts_markdown_and_preserves_errors(app, monkeypatch):
    monkeypatch.setattr(public, "_get_md", lambda _path: "# Heading\n\n![x](image.png)")
    html = public._get_html("public/docs/guide.md")
    assert "<h1>Heading</h1>" in html
    assert 'src="/public/docs/image.png"' in html

    monkeypatch.setattr(public, "_get_md", lambda _path: ("bad", 400))
    assert public._get_html("bad.txt") == ("bad", 400)


def test_get_word_converts_local_markdown_and_cleans_output(app, tmp_path, monkeypatch):
    markdown = Path(app.config["PROJECT_ROOT"]) / "guide.md"
    markdown.write_text("# Guide", encoding="utf-8")
    def convert_file(_source, _format, *, outputfile, extra_args):
        assert extra_args
        assert Path(outputfile).name == "redtail-I_O-test.docx"
        Path(outputfile).write_bytes(b"docx-data")

    monkeypatch.setattr(public.pypandoc, "convert_file", convert_file)
    with app.test_request_context("/"):
        response = public._get_word("guide.md", "redtail-I/O-test.docx")
        assert response.status_code == 200
        response.direct_passthrough = False
        assert response.get_data() == b"docx-data"
        assert "attachment" in response.headers["Content-Disposition"]

    assert "redtail-I_O-test.docx" in response.headers["Content-Disposition"]


def test_get_word_adds_docx_extension_to_safe_download_name(app, monkeypatch):
    markdown = Path(app.config["PROJECT_ROOT"]) / "guide.md"
    markdown.write_text("# Guide", encoding="utf-8")

    def convert_file(_source, _format, *, outputfile, extra_args):
        assert extra_args
        assert Path(outputfile).name == "download.docx"
        Path(outputfile).write_bytes(b"docx-data")

    monkeypatch.setattr(public.pypandoc, "convert_file", convert_file)
    with app.test_request_context("/"):
        response = public._get_word("guide.md", "download")
        response.direct_passthrough = False
        assert response.get_data() == b"docx-data"
        assert "download.docx" in response.headers["Content-Disposition"]


@responses.activate
def test_get_word_downloads_relative_remote_images(app, monkeypatch):
    markdown_url = "https://docs.example.test/guide.md"
    image_url = "https://docs.example.test/images/picture.png"
    responses.get(markdown_url, body="![Picture](images/picture.png)", status=200)
    responses.get(image_url, body=b"image", status=200)

    def convert_file(source, _format, *, outputfile, extra_args):
        assert Path(source).read_text(encoding="utf-8") == "![Picture](picture.png)"
        assert extra_args
        Path(outputfile).write_bytes(b"remote-docx")

    monkeypatch.setattr(public.pypandoc, "convert_file", convert_file)
    with app.test_request_context("/"):
        response = public._get_word(markdown_url, "remote-redtail-test.docx")
        response.direct_passthrough = False
        assert response.get_data() == b"remote-docx"


@responses.activate
def test_get_word_keeps_failed_or_absolute_remote_images(app, monkeypatch):
    markdown_url = "https://docs.example.test/guide.md"
    responses.get(
        markdown_url,
        body="![Relative](missing.png) ![Absolute](/root.png) ![Remote](https://cdn.test/a.png)",
        status=200,
    )
    responses.get(
        "https://docs.example.test/missing.png",
        body=requests.ConnectionError("offline"),
    )

    def convert_file(source, _format, *, outputfile, extra_args):
        text = Path(source).read_text(encoding="utf-8")
        assert "missing.png" in text
        assert "/root.png" in text
        assert "https://cdn.test/a.png" in text
        Path(outputfile).write_bytes(b"docx")

    monkeypatch.setattr(public.pypandoc, "convert_file", convert_file)
    with app.test_request_context("/"):
        assert public._get_word(markdown_url, "failed-image-test.docx").status_code == 200


def test_get_word_returns_get_md_error_without_conversion(app, monkeypatch):
    monkeypatch.setattr(public, "_get_md", lambda _path: ("bad", 400))
    assert public._get_word("bad.txt") == ("bad", 400)


def test_get_word_rechecks_local_path_boundary_before_conversion(app, monkeypatch):
    monkeypatch.setattr(public, "_get_md", lambda _path: "# Guide")
    monkeypatch.setattr(public, "_resolve_local_document_path", lambda _path: None)
    assert public._get_word("guide.md") == ("Access denied", 403)
