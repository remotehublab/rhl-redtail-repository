"""Add Wiper simulations and device mappings

Revision ID: c3f1e8a9d2b4
Revises: b8c0d9f4a1e2
Create Date: 2026-08-22 17:05:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c3f1e8a9d2b4"
down_revision = "b8c0d9f4a1e2"
branch_labels = None
depends_on = None


WIPER_SIMULATIONS = (
    {
        "name": "Wiper",
        "slug": "wiper",
        "description": (
            "Control a vehicle windshield wiper using rain and position sensors "
            "with manual and park inputs."
        ),
        "cover_image_url": "/public/images/simulations/wiper.jpg",
        "documents": {
            "fpga-de1-soc": (
                "I/O mapping for Altera DE1-SoC",
                "public/docs/simulations/wiper/devices/wiper-fpga-de1-soc.md",
            ),
            "stm32-nucleo-wb55rg": (
                "I/O mapping for STM32 Nucleo WB55RG",
                "public/docs/simulations/wiper/devices/"
                "wiper-stm32-nucleo-wb55rg.md",
            ),
        },
    },
    {
        "name": "Wiper 2-Bit",
        "slug": "wiper-2-bit",
        "description": (
            "Control a vehicle windshield wiper with two-bit direction commands, "
            "rain and position sensors, and manual and park inputs."
        ),
        "cover_image_url": "/public/images/simulations/wiper-2-bit.jpg",
        "documents": {
            "fpga-de1-soc": (
                "I/O mapping for Altera DE1-SoC",
                "public/docs/simulations/wiper-2-bit/devices/"
                "wiper-2-bit-fpga-de1-soc.md",
            ),
            "stm32-nucleo-wb55rg": (
                "I/O mapping for STM32 Nucleo WB55RG",
                "public/docs/simulations/wiper-2-bit/devices/"
                "wiper-2-bit-stm32-nucleo-wb55rg.md",
            ),
        },
    },
)

AUTHOR_LOGINS = ("deusto", "giovannalani")
CATEGORY_SLUGS = ("simulation", "real-world")
FRAMEWORK_SLUGS = (
    "fpga-de1-soc-system-verilog",
    "stm32-nucleo-wb55rg-mbedos",
)


def _first_id(connection, table, column, value):
    return connection.execute(
        sa.select(table.c.id).where(column == value)
    ).scalar_one_or_none()


def _required_id(connection, table, column, value):
    record_id = _first_id(connection, table, column, value)
    if record_id is None:
        raise RuntimeError(
            f"Cannot add the Wiper catalog: {table.name}.{column.name}={value!r} "
            "is missing"
        )
    return record_id


def _ensure_association(connection, table, values):
    conditions = [table.c[key] == value for key, value in values.items()]
    exists = connection.execute(
        sa.select(sa.literal(1)).select_from(table).where(*conditions).limit(1)
    ).scalar_one_or_none()
    if exists is None:
        connection.execute(table.insert().values(**values))


def _ensure_simulation(connection, table, definition):
    row = connection.execute(
        sa.select(
            table.c.id,
            table.c.slug,
            table.c.description,
            table.c.cover_image_url,
        ).where(table.c.slug == definition["slug"])
    ).first()
    if row is None:
        row = connection.execute(
            sa.select(
                table.c.id,
                table.c.slug,
                table.c.description,
                table.c.cover_image_url,
            ).where(table.c.name == definition["name"])
        ).first()

    if row is None:
        connection.execute(
            table.insert().values(
                name=definition["name"],
                slug=definition["slug"],
                description=definition["description"],
                cover_image_url=definition["cover_image_url"],
                last_updated=sa.func.now(),
            )
        )
        return _first_id(connection, table, table.c.slug, definition["slug"])

    updates = {}
    if row.slug != definition["slug"]:
        updates["slug"] = definition["slug"]
    if not row.description:
        updates["description"] = definition["description"]
    if not row.cover_image_url:
        updates["cover_image_url"] = definition["cover_image_url"]
    if updates:
        updates["last_updated"] = sa.func.now()
        connection.execute(table.update().where(table.c.id == row.id).values(**updates))
    return row.id


def _ensure_device_document(
    connection, table, simulation_id, device_id, name, doc_url
):
    rows = connection.execute(
        sa.select(table.c.id, table.c.name, table.c.doc_url).where(
            table.c.simulation_id == simulation_id,
            table.c.device_id == device_id,
        )
    ).all()
    if any(row.doc_url == doc_url for row in rows):
        return

    named_row = next((row for row in rows if row.name == name), None)
    if named_row is not None:
        values = {"doc_url": doc_url}
        if "updated_at" in table.c:
            values["updated_at"] = sa.func.now()
        connection.execute(
            table.update().where(table.c.id == named_row.id).values(**values)
        )
        return

    connection.execute(
        table.insert().values(
            simulation_id=simulation_id,
            device_id=device_id,
            name=name,
            doc_url=doc_url,
        )
    )


def _ensure_wiper_catalog(connection):
    metadata = sa.MetaData()
    simulation = sa.Table("simulation", metadata, autoload_with=connection)
    author = sa.Table("author", metadata, autoload_with=connection)
    author_simulation = sa.Table(
        "author_simulation", metadata, autoload_with=connection
    )
    device = sa.Table("device", metadata, autoload_with=connection)
    device_simulation = sa.Table(
        "device_simulation", metadata, autoload_with=connection
    )
    framework = sa.Table("device_framework", metadata, autoload_with=connection)
    simulation_framework = sa.Table(
        "simulation_framework_association", metadata, autoload_with=connection
    )
    category = sa.Table("simulation_category", metadata, autoload_with=connection)
    simulation_category = sa.Table(
        "simulation_category_association", metadata, autoload_with=connection
    )
    device_document = sa.Table(
        "simulation_device_document", metadata, autoload_with=connection
    )

    author_ids = [
        _required_id(connection, author, author.c.login, login)
        for login in AUTHOR_LOGINS
    ]
    category_ids = [
        _required_id(connection, category, category.c.slug, slug)
        for slug in CATEGORY_SLUGS
    ]
    devices = {
        slug: _required_id(connection, device, device.c.slug, slug)
        for slug in {slug for item in WIPER_SIMULATIONS for slug in item["documents"]}
    }
    framework_ids = [
        _required_id(connection, framework, framework.c.slug, slug)
        for slug in FRAMEWORK_SLUGS
    ]

    for definition in WIPER_SIMULATIONS:
        simulation_id = _ensure_simulation(connection, simulation, definition)
        for author_id in author_ids:
            _ensure_association(
                connection,
                author_simulation,
                {"author_id": author_id, "simulation_id": simulation_id},
            )
        for category_id in category_ids:
            _ensure_association(
                connection,
                simulation_category,
                {"simulation_id": simulation_id, "category_id": category_id},
            )
        for device_id in devices.values():
            _ensure_association(
                connection,
                device_simulation,
                {"device_id": device_id, "simulation_id": simulation_id},
            )
        for framework_id in framework_ids:
            _ensure_association(
                connection,
                simulation_framework,
                {"simulation_id": simulation_id, "framework_id": framework_id},
            )
        for device_slug, (name, doc_url) in definition["documents"].items():
            device_id = devices.get(device_slug)
            if device_id is not None:
                _ensure_device_document(
                    connection,
                    device_document,
                    simulation_id,
                    device_id,
                    name,
                    doc_url,
                )


def upgrade():
    _ensure_wiper_catalog(op.get_bind())


def downgrade():
    # This migration can reuse pre-existing catalog rows. Without adding a
    # provenance column, a downgrade cannot distinguish those rows from rows it
    # inserted, so preserving catalog data is safer than deleting user data.
    pass
