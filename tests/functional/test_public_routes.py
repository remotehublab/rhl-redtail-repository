import json
import re
import struct
from pathlib import Path
from xml.etree import ElementTree

import pytest

from redtail_repository import db
from redtail_repository.models import SimulationDeviceDocument, SimulationDoc


def _assert_metadata(response, *, title, description, canonical):
    html = response.get_data(as_text=True)
    assert f"<title>{title}</title>" in html
    assert f'<meta name="description" content="{description}">' in html
    if canonical is None:
        assert '<link rel="canonical"' not in html
    else:
        assert f'<link rel="canonical" href="{canonical}">' in html


def _structured_data(response):
    match = re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        response.get_data(as_text=True),
        flags=re.DOTALL,
    )
    assert match is not None
    return json.loads(match.group(1))


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
    assert b"REDTAIL" in response.data


@pytest.mark.parametrize(
    ("path", "title", "description", "canonical"),
    [
        (
            "/",
            "REDTAIL | Remote Laboratory Simulations and Teaching Materials",
            "Explore REDTAIL simulations, digital twins, and teaching materials connected "
            "to real remote laboratory hardware.",
            "https://redtail.example.test/",
        ),
        (
            "/laboratory-exercises?category=fundamentals",
            "Remote Laboratory Exercises | REDTAIL",
            "Browse classroom-ready remote laboratory exercises, lessons, and teaching "
            "materials connected to real hardware.",
            None,
        ),
        (
            "/simulations?category=digital-twin",
            "Remote Laboratory Simulations and Digital Twins | REDTAIL",
            "Explore REDTAIL simulations and digital twins connected to remotely accessible "
            "laboratory hardware.",
            None,
        ),
        (
            "/devices?framework=native",
            "Remote Laboratory Hardware and Devices | REDTAIL",
            "Browse real laboratory hardware supported by REDTAIL simulations and teaching "
            "materials.",
            None,
        ),
        (
            "/login?next=/devices",
            "Log in | REDTAIL",
            "Log in to access the REDTAIL features available to your account.",
            "https://redtail.example.test/login",
        ),
        (
            "/register",
            "Register | REDTAIL",
            "Create a REDTAIL account to access remote laboratory resources.",
            "https://redtail.example.test/register",
        ),
    ],
)
def test_page_specific_collection_and_account_metadata(
    client, catalog, path, title, description, canonical
):
    response = client.get(path)
    assert response.status_code == 200
    _assert_metadata(
        response,
        title=title,
        description=description,
        canonical=canonical,
    )


@pytest.mark.parametrize(
    ("path", "title", "description", "canonical"),
    [
        (
            "/laboratory-exercises/test-exercise",
            "Test Exercise | REDTAIL Laboratory Exercise",
            "A deterministic laboratory exercise.",
            "https://redtail.example.test/laboratory-exercises/test-exercise",
        ),
        (
            "/simulations/test-simulation",
            "Test Simulation | Remote Laboratory Simulation | REDTAIL",
            "A deterministic simulation.",
            "https://redtail.example.test/simulations/test-simulation",
        ),
        (
            "/devices/test-board",
            "Test Board Remote Laboratory Device | REDTAIL",
            "A deterministic test device.",
            "https://redtail.example.test/devices/test-board",
        ),
        (
            "/authors/1",
            "Example Author | REDTAIL Author",
            "Explore REDTAIL laboratory exercises and simulations contributed by Example Author.",
            "https://redtail.example.test/authors/1",
        ),
    ],
)
def test_page_specific_detail_metadata(
    client, catalog, path, title, description, canonical
):
    response = client.get(path)
    assert response.status_code == 200
    _assert_metadata(
        response,
        title=title,
        description=description,
        canonical=canonical,
    )


def test_document_canonical_uses_stable_title_slug(client, catalog):
    response = client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-arbitrary.md"
    )

    assert response.status_code == 200
    _assert_metadata(
        response,
        title="Simulation Guide — Test Simulation | REDTAIL",
        description="Simulation documentation",
        canonical=(
            "https://redtail.example.test/simulations/test-simulation/docs/"
            f"{catalog.simulation_doc.id}-simulation-guide.md"
        ),
    )


def test_robots_points_to_sitemap_without_blocking_noindex_pages(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.content_type == "text/plain; charset=utf-8"
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert response.get_data(as_text=True) == (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://redtail.example.test/sitemap.xml\n"
    )
    assert "Disallow: /login" not in response.get_data(as_text=True)


def test_sitemap_lists_only_canonical_indexable_catalog_urls(client, catalog):
    docs_root = Path(client.application.config["PUBLIC_FOLDER"]) / "docs"
    (docs_root / "word-only.docx").write_bytes(b"docx")
    simulation_docx = SimulationDoc(
        simulation=catalog.simulation,
        title="Word Only",
        doc_url="public/docs/word-only.docx",
    )
    device_docx = SimulationDeviceDocument(
        simulation=catalog.simulation,
        device=catalog.device,
        name="Word Mapping",
        doc_url="public/docs/word-only.docx",
    )
    query_string_doc = SimulationDoc(
        simulation=catalog.simulation,
        title="Versioned Markdown",
        doc_url="https://docs.example.test/guide.md?download=1",
    )
    db.session.add_all((simulation_docx, device_docx, query_string_doc))
    db.session.commit()

    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.content_type == "application/xml; charset=utf-8"
    assert response.headers["Cache-Control"] == "public, max-age=3600"

    root = ElementTree.fromstring(response.data)
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {
        element.text for element in root.findall("sitemap:url/sitemap:loc", namespace)
    }

    assert "https://redtail.example.test/" in locations
    assert "https://redtail.example.test/authors/1" in locations
    assert "https://redtail.example.test/laboratory-exercises/test-exercise" in locations
    assert "https://redtail.example.test/simulations/test-simulation" in locations
    assert "https://redtail.example.test/devices/test-board" in locations
    assert (
        "https://redtail.example.test/simulations/test-simulation/docs/"
        f"{catalog.simulation_doc.id}-simulation-guide.md"
    ) in locations
    assert (
        "https://redtail.example.test/simulations/test-simulation/devices/test-board/"
        f"docs/{catalog.simulation_device_doc.id}-board-guide.md"
    ) in locations
    assert not any("?" in location for location in locations)
    assert not any("/login" in location for location in locations)
    assert not any("/register" in location for location in locations)
    assert not any("inactive-exercise" in location for location in locations)
    assert not any(f"docs/{simulation_docx.id}-word-only.md" in location for location in locations)
    assert not any(f"docs/{device_docx.id}-word-mapping.md" in location for location in locations)
    assert not any(
        f"docs/{query_string_doc.id}-versioned-markdown.md" in location
        for location in locations
    )

    lastmods = {
        element.text
        for element in root.findall("sitemap:url/sitemap:lastmod", namespace)
    }
    assert "2024-01-15" in lastmods


@pytest.mark.parametrize(
    "path",
    [
        "/laboratory-exercises?category=fundamentals",
        "/simulations?category=digital-twin",
        "/devices?framework=native",
        "/login",
        "/register",
        "/docs/markdown-viewer/public/docs/simulation.md",
    ],
)
def test_filtered_and_account_pages_are_noindex_follow(client, catalog, path):
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["X-Robots-Tag"] == "noindex, follow"
    assert b'<meta name="robots" content="noindex, follow">' in response.data
    if "?" in path:
        assert b'<link rel="canonical"' not in response.data
        assert b'<meta property="og:url"' not in response.data


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/laboratory-exercises",
        "/simulations",
        "/devices",
        "/simulations/test-simulation",
    ],
)
def test_primary_public_pages_remain_indexable(client, catalog, path):
    response = client.get(path)

    assert response.status_code == 200
    assert "X-Robots-Tag" not in response.headers
    assert b'<meta name="robots"' not in response.data


def test_admin_and_error_responses_are_excluded_from_search(
    client, catalog, login_as
):
    login_as("admin-user")
    admin = client.get("/admin/")
    assert admin.status_code == 200
    assert admin.headers["X-Robots-Tag"] == "noindex, nofollow"

    missing = client.get("/missing-page")
    assert missing.status_code == 404
    assert missing.headers["X-Robots-Tag"] == "noindex, noarchive"
    assert b'<link rel="canonical" href="">' not in missing.data
    assert b'<meta property="og:url" content="">' not in missing.data
    assert b'<meta property="og:image" content="">' not in missing.data


@pytest.mark.parametrize("path", ["/lessons", "/laboratory_exercise"])
def test_legacy_exercise_collections_redirect_permanently(client, catalog, path):
    response = client.get(path)

    assert response.status_code == 301
    assert response.headers["Location"] == "/laboratory-exercises"


def test_legacy_author_and_same_slug_exercise_redirect_permanently(client, catalog):
    author = client.get(f"/author/{catalog.author.id}")
    exercise = client.get("/lessons/test-exercise")

    assert author.status_code == 301
    assert author.headers["Location"] == f"/authors/{catalog.author.id}"
    assert exercise.status_code == 301
    assert exercise.headers["Location"] == "/laboratory-exercises/test-exercise"


def test_verified_renamed_exercise_and_device_slugs_redirect(client, catalog):
    catalog.exercise.slug = "stm32-parking-lot-intermediate-level-keil-studio"
    catalog.device.slug = "stm32-nucleo-wb55rg"
    db.session.commit()

    exercise = client.get(
        "/laboratory-exercises/parking-lot-stm32-nucleo-wb55rg-stm32cubemx"
    )
    lesson = client.get(
        "/lessons/parking-lot-stm32-nucleo-wb55rg-stm32cubemx"
    )
    device = client.get("/devices/stm32-wb55rg")

    expected_exercise = (
        "/laboratory-exercises/stm32-parking-lot-intermediate-level-keil-studio"
    )
    assert exercise.status_code == 301
    assert exercise.headers["Location"] == expected_exercise
    assert lesson.status_code == 301
    assert lesson.headers["Location"] == expected_exercise
    assert device.status_code == 301
    assert device.headers["Location"] == "/devices/stm32-nucleo-wb55rg"


def test_legacy_document_urls_redirect_to_stable_slugged_urls(client, catalog):
    simulation_doc = client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}.md"
    )
    simulation_word = client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}.docx"
    )
    device_doc = client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}.md"
    )
    device_word = client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}.docx"
    )

    expected_simulation = (
        "/simulations/test-simulation/docs/"
        f"{catalog.simulation_doc.id}-simulation-guide"
    )
    expected_device = (
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board-guide"
    )
    assert simulation_doc.status_code == 301
    assert simulation_doc.headers["Location"] == f"{expected_simulation}.md"
    assert simulation_word.status_code == 301
    assert simulation_word.headers["Location"] == f"{expected_simulation}.docx"
    assert device_doc.status_code == 301
    assert device_doc.headers["Location"] == f"{expected_device}.md"
    assert device_word.status_code == 301
    assert device_word.headers["Location"] == f"{expected_device}.docx"


@pytest.mark.parametrize(
    "path",
    [
        "/author/99999",
        "/lessons/unknown-exercise",
        "/simulations/missing/docs/1.md",
        "/simulations/test-simulation/docs/99999.md",
        "/simulations/missing/devices/test-board/docs/1.md",
        "/simulations/test-simulation/devices/missing/docs/1.md",
        "/simulations/test-simulation/devices/test-board/docs/99999.md",
    ],
)
def test_unknown_legacy_urls_remain_not_found(client, catalog, path):
    response = client.get(path)

    assert response.status_code == 404
    assert response.headers["X-Robots-Tag"] == "noindex, noarchive"


def test_homepage_social_metadata_and_organization_schema(client, catalog):
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<meta property="og:site_name" content="REDTAIL">' in html
    assert '<meta property="og:type" content="website">' in html
    assert (
        '<meta property="og:image" content="https://redtail.example.test/static/img/'
        'redtail-social-card.png">'
    ) in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="630">' in html

    graph = _structured_data(response)["@graph"]
    assert {node["@type"] for node in graph} == {
        "ResearchOrganization",
        "WebSite",
    }
    organization = next(
        node for node in graph if node["@type"] == "ResearchOrganization"
    )
    assert organization["name"] == "Remote Hub Lab"
    assert organization["parentOrganization"]["name"] == "University of Washington"
    assert organization["logo"] == (
        "https://redtail.example.test/static/img/remote_hub_lab.png"
    )


def test_detail_social_image_breadcrumbs_and_learning_resource_schema(client, catalog):
    response = client.get("/laboratory-exercises/test-exercise")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<meta property="og:type" content="article">' in html
    assert (
        '<meta property="og:image" content="https://redtail.example.test/static/img/'
        'NES.png">'
    ) in html
    assert (
        '<meta property="og:image:alt" content="Test Exercise laboratory exercise">'
    ) in html
    assert '<meta property="og:image:width"' not in html
    assert '<meta property="og:image:height"' not in html

    graph = _structured_data(response)["@graph"]
    breadcrumb = next(node for node in graph if node["@type"] == "BreadcrumbList")
    resource = next(node for node in graph if node["@type"] == "LearningResource")

    assert [item["name"] for item in breadcrumb["itemListElement"]] == [
        "Home",
        "Laboratory Exercises",
        "Test Exercise",
    ]
    assert resource["learningResourceType"] == "Laboratory exercise"
    assert resource["educationalLevel"] == ["Introductory"]
    assert resource["teaches"] == "Learn deterministic testing."
    assert resource["author"][0]["name"] == "Example Author"
    assert all(node.get("@type") != "Course" for node in graph)


def test_author_and_simulation_structured_data_match_page_entities(client, catalog):
    author = client.get(f"/authors/{catalog.author.id}")
    simulation = client.get("/simulations/test-simulation")

    author_graph = _structured_data(author)["@graph"]
    person = next(node for node in author_graph if node["@type"] == "Person")
    assert person["name"] == "Example Author"
    assert person["sameAs"] == "https://example.test/author"

    simulation_graph = _structured_data(simulation)["@graph"]
    resource = next(
        node for node in simulation_graph if node["@type"] == "LearningResource"
    )
    assert resource["learningResourceType"] == "Simulation"
    assert resource["url"] == (
        "https://redtail.example.test/simulations/test-simulation"
    )


def test_social_card_is_a_1200_by_630_png(client):
    response = client.get("/static/img/redtail-social-card.png")

    assert response.status_code == 200
    assert response.content_type == "image/png"
    assert response.data.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", response.data[16:24])
    assert (width, height) == (1200, 630)


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
    assert b"Instructor approval is required" in anonymous.data
    assert b"Contact the REDTAIL team about access" in anonymous.data
    assert b"Already approved? Log in" in anonymous.data

    login_as("student-user")
    unverified = client.get("/laboratory-exercises/test-exercise")
    assert b"Instructor approval is required" in unverified.data
    assert b"Contact the REDTAIL team about access" in unverified.data
    assert b"Already approved? Log in" not in unverified.data
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
    assert device_markdown.data.count(b"<h1") == 1
    assert b'class="table-scroll"' in device_markdown.data
    assert b'role="region"' in device_markdown.data
    assert b'tabindex="0"' in device_markdown.data
    assert b'<h2>Device guide</h2>' in device_markdown.data


def test_simulation_detail_hides_inactive_exercises_and_missing_documents(
    client, catalog
):
    catalog.inactive_exercise.simulations.append(catalog.simulation)
    catalog.simulation_doc.doc_url = "public/docs/missing-simulation.md"
    catalog.simulation_device_doc.doc_url = "public/docs/missing-device.md"
    db.session.commit()

    detail = client.get("/simulations/test-simulation")

    assert detail.status_code == 200
    assert b"Inactive Exercise" not in detail.data
    assert b"Simulation Guide" not in detail.data
    assert b"Board Guide" not in detail.data


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
        "redtail_repository.views.public._get_html",
        lambda _path, **_kwargs: ("blocked", 403),
    )
    assert client.get(
        f"/simulations/test-simulation/docs/{catalog.simulation_doc.id}-guide.md"
    ).status_code == 403
    assert client.get(
        "/simulations/test-simulation/devices/test-board/docs/"
        f"{catalog.simulation_device_doc.id}-board.md"
    ).status_code == 403
    assert client.get("/docs/markdown-viewer/blocked.md").status_code == 403


INSTRUCTOR_MAILTO = "mailto:rhlab@uw.edu?subject=REDTAIL%20instructor%20inquiry"


def test_home_page_exposes_instructor_contact_paths(client, catalog):
    response = client.get("/")
    assert response.status_code == 200
    body = response.data.decode()

    assert "https://rhlab.ece.uw.edu/join-us/" not in body
    # instructor panel, closing CTA, and the sitewide footer link
    assert body.count(f'href="{INSTRUCTOR_MAILTO}"') == 3
    assert f'href="{INSTRUCTOR_MAILTO}" target' not in body
    assert "rhlab@uw.edu · Remote Hub Lab, University of Washington" in body

    for label in (
        "Explore laboratory exercises",
        "Browse simulations",
        "Explore the simulation library",
        "View the source on GitHub",
        "Browse current exercises",
        "Email the REDTAIL team",
        "Work with us",
        "Register",
    ):
        assert label in body

    assert 'href="#support"' in body
    assert "For instructors and collaborators" in body
    assert "Bring remote hardware into your course." in body
    assert "Create an instructor account" not in body
    assert "verified academic account" not in body
    assert "instructor-only solution materials" not in body


def test_account_pages_describe_instructor_access_accurately(client, catalog):
    register_body = client.get("/register").data.decode()
    login_body = client.get("/login").data.decode()

    assert "Instructor access is arranged separately" in register_body
    assert "Email the REDTAIL team about instructor access" in register_body
    assert f'href="{INSTRUCTOR_MAILTO}"' in register_body
    assert "Use your academic email" not in register_body
    assert "laboratory solutions" not in register_body
    assert "manage REDTAIL laboratory resources" not in login_body


@pytest.mark.parametrize("path", ["/", "/simulations", "/devices", "/login"])
def test_footer_contact_link_is_sitewide(client, catalog, path):
    body = client.get(path).data.decode()
    assert f'href="{INSTRUCTOR_MAILTO}"' in body
    assert "https://rhlab.ece.uw.edu/join-us/" not in body
    assert (
        "href='https://rhlab.ece.uw.edu/' target='_blank' rel='noopener noreferrer'"
        in body
    )
    assert (
        "href='https://labsland.com/' target='_blank' rel='noopener noreferrer'"
        in body
    )
    assert "Developed by" in body
    assert "RHLab at the University of Washington" in body
