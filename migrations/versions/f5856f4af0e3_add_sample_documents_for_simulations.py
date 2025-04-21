"""Add sample documents for simulations

Revision ID: f5856f4af0e3
Revises: df02d6e62a01
Create Date: 2025-04-21 15:14:24.930634

"""
import datetime
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Table, MetaData

# revision identifiers, used by Alembic.
revision = 'f5856f4af0e3'
down_revision = 'df02d6e62a01'
branch_labels = None
depends_on = None




def upgrade():
    conn = op.get_bind()
    meta = MetaData()

    simulation_table        = Table('simulation', meta, autoload_with=conn)
    sim_doc_table           = Table('simulation_doc', meta, autoload_with=conn)
    sim_dev_doc_table       = Table('simulation_device_document', meta, autoload_with=conn)
    device_sim_assoc        = Table('device_simulation', meta, autoload_with=conn)
    device_table            = Table('device', meta, autoload_with=conn)

    slugs = [
        'parking-lot', 'keypad', 'butterfly', 'nes-controller',
        'joystick', 'door', 'watertank', 'ledmatrix', 'morse'
    ]

    for slug in slugs:
        # fetch simulation id & name
        row = conn.execute(
            sa.select(simulation_table.c.id, simulation_table.c.name)
              .where(simulation_table.c.slug == slug)
        ).first()
        if not row:
            continue
        sim_id, sim_name = row.id, row.name

        # a) add a SimulationDoc
        doc_url = f'http://redtail.rhlab.ece.uw.edu/public/images/docs/simulations/{slug}.pdf'
        conn.execute(
            sim_doc_table.insert().values(
                simulation_id=sim_id,
                doc_url=doc_url,
                title=f'{sim_name} documentation',
                description='General explanation of how this simulation work',
                last_updated=datetime.datetime(2025, 1, 1)
            )
        )

        # b) for each associated device, add a SimulationDeviceDocument
        dev_rows = conn.execute(
            sa.select(device_sim_assoc.c.device_id)
              .where(device_sim_assoc.c.simulation_id == sim_id)
        ).all()
        for dr in dev_rows:
            dev_id = dr.device_id
            dev = conn.execute(
                sa.select(device_table.c.slug, device_table.c.name)
                  .where(device_table.c.id == dev_id)
            ).first()
            if not dev:
                continue
            dev_slug, dev_name = dev.slug, dev.name
            sd_doc_url = (
                f'http://redtail.rhlab.ece.uw.edu/public/images/docs/simulations/'
                f'{slug}-{dev_slug}.pdf'
            )
            conn.execute(
                sim_dev_doc_table.insert().values(
                    simulation_id=sim_id,
                    device_id=dev_id,
                    name=f'I/O mapping for {dev_name}',
                    doc_url=sd_doc_url
                )
            )


def downgrade():
    conn = op.get_bind()
    meta = MetaData()

    simulation_table    = Table('simulation', meta, autoload_with=conn)
    sim_doc_table       = Table('simulation_doc', meta, autoload_with=conn)
    sim_dev_doc_table   = Table('simulation_device_document', meta, autoload_with=conn)

    slugs = [
        'parking-lot', 'keypad', 'butterfly', 'nes-controller',
        'joystick', 'door', 'watertank', 'ledmatrix', 'morse'
    ]

    for slug in slugs:
        row = conn.execute(
            sa.select(simulation_table.c.id)
              .where(simulation_table.c.slug == slug)
        ).first()
        if not row:
            continue
        sim_id = row.id

        # remove all device‐mapping docs for this simulation
        conn.execute(
            sim_dev_doc_table.delete()
              .where(sim_dev_doc_table.c.simulation_id == sim_id)
        )
        # remove the simulation doc
        conn.execute(
            sim_doc_table.delete()
              .where(sim_doc_table.c.simulation_id == sim_id)
        )
