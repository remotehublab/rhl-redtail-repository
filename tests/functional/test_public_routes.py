import pytest

from redtail_repository import db


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/authors",
        "/laboratory-exercises",
        "/simulations",
        "/devices",
        "/login",
        "/register",
    ],
)
def test_public_collection_pages_render(client, catalog, path):
    response = client.get(path)
    assert response.status_code == 200
    assert b"RedTail" in response.data


def test_author_pages_render_empty_populated_and_missing(client, catalog):
    listing = client.get("/authors")
    assert b"Example Author" in listing.data

    detail = client.get(f"/authors/{catalog.author.id}")
    assert detail.status_code == 200
    assert b"Example Author" in detail.data

    missing = client.get("/authors/99999")
    assert missing.status_code == 404
    assert b"Author not found" in missing.data


@pytest.mark.parametrize(
    "query",
    [
        "?category=fundamentals",
        "?level=introductory",
        "?framework=native",
        "?category=unknown&level=unknown&framework=unknown",
    ],
)
def test_laboratory_exercise_filters(client, catalog, query):
    response = client.get(f"/laboratory-exercises{query}")
    assert response.status_code == 200
    assert b"Test Exercise" in response.data
    assert b"Inactive Exercise" not in response.data


def test_laboratory_exercise_detail_and_visibility(client, catalog, login_as):
    anonymous = client.get("/laboratory-exercises/test-exercise")
    assert anonymous.status_code == 200
    assert b"Exercise Guide" in anonymous.data
    assert b"Exercise Solution" in anonymous.data
    assert b"Only available for verified instructors" in anonymous.data

    login_as("student-user")
    unverified = client.get("/laboratory-exercises/test-exercise")
    assert b"Only available for verified instructors" in unverified.data
    client.get("/logout")

    login_as("verified-instructor")
    verified = client.get("/laboratory-exercises/test-exercise")
    assert b"Exercise Solution" in verified.data

    assert client.get("/laboratory-exercises/missing").status_code == 404
    assert client.get("/laboratory-exercises/inactive-exercise").status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        "?device=1",
        "?category=digital-twin",
        "?framework=native",
        "?device=99999&category=unknown&framework=unknown",
    ],
)
def test_simulation_filters(client, catalog, query):
    response = client.get(f"/simulations{query}")
    assert response.status_code == 200
    if "device=99999" not in query:
        assert b"Test Simulation" in response.data


def test_simulation_detail_and_markdown_routes(client, catalog):
    detail = client.get("/simulations/test-simulation")
    assert detail.status_code == 200
    assert b"Test Simulation" in detail.data
    assert b"Board Guide" in detail.data

    markdown = client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-guide.md"
    )
    assert markdown.status_code == 200
    assert b"Simulation guide" in markdown.data

    device_markdown = client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board.md"
    )
    assert device_markdown.status_code == 200
    assert b"Device guide" in device_markdown.data


@pytest.mark.parametrize(
    "path",
    [
        "/simulations/missing",
        "/simulations/missing/docs/1-guide.md",
        "/simulations/test-simulation/docs/999-guide.md",
        "/simulations/missing/devices/test-board/docs/1-board.md",
        "/simulations/test-simulation/devices/missing/docs/1-board.md",
        "/simulations/test-simulation/devices/test-board/docs/999-board.md",
    ],
)
def test_simulation_not_found_states(client, catalog, path):
    assert client.get(path).status_code == 404


def test_non_markdown_documents_return_not_found(client, app, catalog):
    catalog.simulation_doc.doc_url = "public/docs/not-markdown.pdf"
    catalog.simulation_device_doc.doc_url = "public/docs/not-markdown.pdf"
    from redtail_repository import db

    db.session.commit()

    assert client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-guide.md"
    ).status_code == 404
    assert client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board.md"
    ).status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        "?device_category=1",
        "?framework=native",
        "?device_category=99999&framework=unknown",
    ],
)
def test_device_filters(client, catalog, query):
    response = client.get(f"/devices{query}")
    assert response.status_code == 200
    assert b"Test Board" in response.data


def test_device_detail_and_missing(client, catalog):
    response = client.get("/devices/test-board")
    assert response.status_code == 200
    assert b"Device Guide" in response.data
    assert client.get("/devices/missing").status_code == 404


def test_generic_markdown_viewer_and_public_file_route(client, app, catalog):
    markdown = client.get("/docs/markdown-viewer/public/docs/simulation.md")
    assert markdown.status_code == 200
    assert b"Simulation guide" in markdown.data

    public_file = client.get("/public/docs/simulation.md")
    assert public_file.status_code == 200
    assert b"Simulation guide" in public_file.data

    app.config["SERVE_PUBLIC_FILES"] = False
    assert client.get("/public/docs/simulation.md").status_code == 404


def test_word_routes_delegate_to_converter(client, catalog, monkeypatch):
    monkeypatch.setattr(
        "redtail_repository.views.public._get_word",
        lambda path, filename="document.docx": f"converted:{path}:{filename}",
    )

    generic = client.get("/docs/word-converter/public/docs/simulation.md")
    assert generic.status_code == 200
    assert b"converted:public/docs/simulation.md:document.docx" in generic.data

    simulation = client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-guide.docx"
    )
    assert simulation.status_code == 200
    assert b"Test Simulation-Simulation Guide.docx" in simulation.data

    device = client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board.docx"
    )
    assert device.status_code == 200
    assert b"Test Simulation-Test Board-Board Guide.docx" in device.data


def test_word_routes_cover_all_not_found_and_wrong_type_states(client, catalog):
    assert client.get("/simulations/missing/docs/1-guide.docx").status_code == 404
    assert client.get(
        "/simulations/test-simulation/docs/999-guide.docx"
    ).status_code == 404
    assert client.get(
        "/simulations/missing/devices/test-board/docs/1-board.docx"
    ).status_code == 404
    assert client.get(
        "/simulations/test-simulation/devices/missing/docs/1-board.docx"
    ).status_code == 404
    assert client.get(
        "/simulations/test-simulation/devices/test-board/docs/999-board.docx"
    ).status_code == 404

    catalog.simulation_doc.doc_url = "public/docs/not-markdown.pdf"
    catalog.simulation_device_doc.doc_url = "public/docs/not-markdown.pdf"
    db.session.commit()
    assert client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-guide.docx"
    ).status_code == 404
    assert client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board.docx"
    ).status_code == 404


def test_markdown_routes_preserve_reader_error_responses(
    client, catalog, monkeypatch
):
    monkeypatch.setattr(
        "redtail_repository.views.public._get_html", lambda _path: ("blocked", 403)
    )
    assert client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-guide.md"
    ).status_code == 403
    assert client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board.md"
    ).status_code == 403
    assert client.get("/docs/markdown-viewer/blocked.md").status_code == 403
