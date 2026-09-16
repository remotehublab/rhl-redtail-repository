"""Exercise the real Airport Markdown through the existing public document routes."""

import re
from pathlib import Path
from shutil import copytree

import pytest

from redtail_repository import db
from redtail_repository.models import Device, Simulation, SimulationDeviceDocument, SimulationDoc

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "public/docs/simulations/airport-wind-station"


@pytest.mark.parametrize(
    ("filename", "pins"),
    [
        (
            "airport-wind-station-fpga-de1-soc.md",
            [
                "V_GPIO[28]",
                "V_GPIO[29]",
                "V_GPIO[30]",
                "V_GPIO[23]",
                "V_GPIO[24]",
                "V_GPIO[26]",
                "V_GPIO[27]",
                "V_GPIO[32]",
                "V_GPIO[34]",
                "V_GPIO[31]",
            ],
        ),
        (
            "airport-wind-station-stm32-nucleo-wb55rg.md",
            ["PC13", "PA6", "PB9", "PB8", "PC12", "PC4", "PD0", "PD1", "PB0", "PB1"],
        ),
    ],
)
def test_airport_mapping_preserves_the_five_physical_slots(filename, pins):
    text = (DOCS / "devices" / filename).read_text()
    rows = [
        line for line in text.splitlines() if line.startswith(tuple(f"| {i} |" for i in range(5)))
    ]
    assert len(rows) == 10
    for index, (row, pin) in enumerate(zip(rows, pins, strict=True)):
        assert row.startswith(f"| {index % 5} |")
        assert f"`{pin}`" in row
    assert "not the controller reset" in rows[0]
    assert "Drive low" in rows[6]
    assert "Zhiyun (ZZ) Zhang" in text
    assert "Luis Rodríguez Gil" in text


def test_airport_usage_guide_explains_access_resets_and_credits():
    text = (DOCS / "guide.md").read_text()
    for expected in (
        "access supplied by their instructor",
        "Restart activity",
        "Controller reset",
        "does **not** reset",
        "reserved `00`",
        "without\n  waiting",
        "Reduce motion",
        "Zhiyun (ZZ) Zhang",
        "Luis Rodríguez Gil",
        "Professor Rania Hussein",
        "2336745",
    ):
        assert expected in text
    assert (ROOT / "public/images/simulations/airport-wind-station.jpg").stat().st_size > 50_000


def test_airport_resources_work_in_offline_word_exports():
    for path in DOCS.rglob("*.md"):
        text = path.read_text()
        for image in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
            assert not image.startswith("/"), "Pandoc needs a file-relative image"
            assert (path.parent / image).resolve().is_file()
        for link in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", text):
            assert link.startswith(("https://", "mailto:")), "Offline links need full URLs"


def test_airport_documentation_renders_anonymously(client, app):
    copytree(DOCS, Path(app.config["PUBLIC_FOLDER"]) / "docs/simulations/airport-wind-station")
    sim = Simulation(
        name="Airport Wind Station", slug="airport-wind-station", description="Wind control"
    )
    guide = SimulationDoc(
        simulation=sim,
        title="Airport Wind Station — Usage Guide",
        doc_url="public/docs/simulations/airport-wind-station/guide.md",
    )
    db.session.add_all([sim, guide])
    mappings = []
    for slug, name in (
        ("fpga-de1-soc", "Altera DE1-SoC"),
        ("stm32-nucleo-wb55rg", "STM32 Nucleo WB55RG"),
    ):
        device = Device(name=name, slug=slug, description=name)
        mapping = SimulationDeviceDocument(
            simulation=sim,
            device=device,
            name=f"I/O mapping for {name}",
            doc_url=f"public/docs/simulations/airport-wind-station/devices/airport-wind-station-{slug}.md",
        )
        db.session.add_all([device, mapping])
        mappings.append(mapping)
    db.session.commit()
    guide_url = f"/simulations/{sim.slug}/docs/{guide.id}-{guide.slugified_title}.md"
    response = client.get(guide_url)
    assert response.status_code == 200
    assert "Zhiyun (ZZ) Zhang" in response.text
    assert "<table" in response.text
    assert (
        "/public/docs/simulations/airport-wind-station/../../../images/simulations/airport-wind-station.jpg"
        in response.text
    )
    for mapping in mappings:
        url = f"/simulations/{sim.slug}/devices/{mapping.device.slug}/docs/{mapping.id}-{mapping.slugified_name}.md"
        response = client.get(url)
        assert response.status_code == 200
        assert "Fixed slot" in response.text
        assert "not the controller reset" in response.text
