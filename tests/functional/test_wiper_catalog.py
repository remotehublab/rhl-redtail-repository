from pathlib import Path
from shutil import copy2

import pytest

from migrations.versions.c3f1e8a9d2b4_add_wiper_simulations import (
    AUTHOR_LOGINS,
    CATEGORY_SLUGS,
    FRAMEWORK_SLUGS,
    WIPER_SIMULATIONS,
    _ensure_wiper_catalog,
)
from redtail_repository import db
from redtail_repository.models import (
    Author,
    Device,
    DeviceFramework,
    Simulation,
    SimulationCategory,
    SimulationDeviceDocument,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _seed_wiper_dependencies():
    authors = [
        Author(login="deusto", name="University of Deusto"),
        Author(login="giovannalani", name="Giovanna Lani"),
    ]
    categories = [
        SimulationCategory(name="Simulation", slug="simulation"),
        SimulationCategory(name="Real World", slug="real-world"),
    ]
    fpga = Device(
        name="Altera DE1-SoC",
        slug="fpga-de1-soc",
        description="FPGA development board.",
    )
    stm32 = Device(
        name="STM32 Nucleo WB55RG",
        slug="stm32-nucleo-wb55rg",
        description="Microcontroller development board.",
    )
    frameworks = [
        DeviceFramework(
            name="SystemVerilog",
            slug="fpga-de1-soc-system-verilog",
            device=fpga,
        ),
        DeviceFramework(
            name="Mbed OS",
            slug="stm32-nucleo-wb55rg-mbedos",
            device=stm32,
        ),
    ]
    db.session.add_all([*authors, *categories, fpga, stm32, *frameworks])
    db.session.commit()
    return fpga


def _run_catalog_migration():
    _ensure_wiper_catalog(db.session.connection())
    db.session.commit()
    db.session.expire_all()


def _copy_wiper_assets(app):
    public_root = Path(app.config["PUBLIC_FOLDER"])
    for definition in WIPER_SIMULATIONS:
        cover_relative = Path(definition["cover_image_url"].removeprefix("/public/"))
        cover_target = public_root / cover_relative
        cover_target.parent.mkdir(parents=True, exist_ok=True)
        copy2(REPOSITORY_ROOT / "public" / cover_relative, cover_target)

        for _, document_path in definition["documents"].values():
            document_relative = Path(document_path).relative_to("public")
            document_target = public_root / document_relative
            document_target.parent.mkdir(parents=True, exist_ok=True)
            copy2(REPOSITORY_ROOT / document_path, document_target)


def test_wiper_catalog_migration_reuses_existing_rows_and_is_idempotent(app):
    fpga = _seed_wiper_dependencies()
    existing = Simulation(
        name="Wiper",
        slug="legacy-wiper",
        description="",
        cover_image_url=None,
    )
    existing_mapping = SimulationDeviceDocument(
        simulation=existing,
        device=fpga,
        name="I/O mapping for Altera DE1-SoC",
        doc_url="public/docs/obsolete-wiper-mapping.md",
    )
    db.session.add_all([existing, existing_mapping])
    db.session.commit()
    existing_id = existing.id

    _run_catalog_migration()
    _run_catalog_migration()

    simulations = Simulation.query.filter(
        Simulation.slug.in_([item["slug"] for item in WIPER_SIMULATIONS])
    ).all()
    assert len(simulations) == 2
    assert Simulation.query.filter_by(name="Wiper", slug="wiper").one().id == existing_id

    for definition in WIPER_SIMULATIONS:
        simulation = Simulation.query.filter_by(slug=definition["slug"]).one()
        assert simulation.description == definition["description"]
        assert simulation.cover_image_url == definition["cover_image_url"]
        assert {author.login for author in simulation.authors} == set(AUTHOR_LOGINS)
        assert {category.slug for category in simulation.simulation_categories} == set(
            CATEGORY_SLUGS
        )
        assert {device.slug for device in simulation.devices} == set(
            definition["documents"]
        )
        assert {framework.slug for framework in simulation.device_frameworks} == set(
            FRAMEWORK_SLUGS
        )
        assert {
            document.device.slug: (document.name, document.doc_url)
            for document in simulation.device_documents
        } == definition["documents"]
        assert all(
            document.created_at is not None and document.updated_at is not None
            for document in simulation.device_documents
        )
        assert all(
            document.uploaded_by_user_id is None
            and document.updated_by_user_id is None
            for document in simulation.device_documents
        )

    assert SimulationDeviceDocument.query.filter(
        SimulationDeviceDocument.simulation_id.in_(simulation.id for simulation in simulations)
    ).count() == 4


def test_wiper_catalog_migration_fails_before_creating_partial_rows(app):
    with pytest.raises(RuntimeError, match="author.login='deusto' is missing"):
        _run_catalog_migration()

    db.session.rollback()
    assert Simulation.query.filter(
        Simulation.slug.in_([item["slug"] for item in WIPER_SIMULATIONS])
    ).count() == 0


def test_wiper_pages_and_mapping_documents_render(client, app):
    _seed_wiper_dependencies()
    _run_catalog_migration()
    _copy_wiper_assets(app)

    collection = client.get("/simulations")
    assert collection.status_code == 200
    assert b"Wiper" in collection.data
    assert b"Wiper 2-Bit" in collection.data

    for definition in WIPER_SIMULATIONS:
        detail = client.get(f"/simulations/{definition['slug']}")
        assert detail.status_code == 200
        assert definition["name"].encode() in detail.data
        assert b"I/O mapping for Altera DE1-SoC" in detail.data
        assert b"I/O mapping for STM32 Nucleo WB55RG" in detail.data

        simulation = Simulation.query.filter_by(slug=definition["slug"]).one()
        for document in simulation.device_documents:
            path = (
                f"/simulations/{simulation.slug}/devices/{document.device.slug}/docs/"
                f"{document.id}-{document.slugified_name}.md"
            )
            rendered = client.get(path)
            assert rendered.status_code == 200
            assert b"Runtime signal" in rendered.data


def test_wiper_cover_images_are_present_and_high_resolution_assets():
    for definition in WIPER_SIMULATIONS:
        image_path = REPOSITORY_ROOT / definition["cover_image_url"].removeprefix("/")
        assert image_path.is_file()
        assert image_path.stat().st_size > 100_000
