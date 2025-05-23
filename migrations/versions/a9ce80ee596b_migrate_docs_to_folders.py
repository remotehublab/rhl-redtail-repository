"""Migrate docs to folders

Revision ID: a9ce80ee596b
Revises: d5454cbb1e7d
Create Date: 2025-05-23 11:51:01.774745

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, MetaData, select, update
import os


# revision identifiers, used by Alembic.
revision = 'a9ce80ee596b'
down_revision = 'd5454cbb1e7d'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    meta = MetaData()
    meta.reflect(bind=conn)

    sim_doc_table = meta.tables['simulation_doc']
    sim_dev_doc_table = meta.tables['simulation_device_document']

    # --- Update simulation_doc ---
    result = conn.execute(select(sim_doc_table.c.id, sim_doc_table.c.doc_url))
    for row in result:
        doc_url = row.doc_url
        if not doc_url.startswith('public/docs/simulations/'):
            continue
        filename = os.path.basename(doc_url)
        name = filename.removesuffix('.md')
        new_path = f'public/docs/simulations/{name}/{filename}'
        conn.execute(
            update(sim_doc_table)
            .where(sim_doc_table.c.id == row.id)
            .values(doc_url=new_path)
        )

    # --- Update simulation_device_document ---
    result = conn.execute(select(sim_dev_doc_table.c.id, sim_dev_doc_table.c.doc_url))
    for row in result:
        doc_url = row.doc_url
        if not doc_url.startswith('public/docs/simulations/'):
            continue

        filename = os.path.basename(doc_url)
        name = filename.removesuffix('.md')
        parts = name.split('-')

        # Remove 3-part device suffix (e.g., '-fpga-de1-soc' or '-stm32-nucleo-wb55rg')
        if len(parts) >= 4:
            base = '-'.join(parts[:-3])
        else:
            base = parts[0]  # fallback for unexpected format

        new_path = f'public/docs/simulations/{base}/devices/{filename}'
        conn.execute(
            update(sim_dev_doc_table)
            .where(sim_dev_doc_table.c.id == row.id)
            .values(doc_url=new_path)
        )

def downgrade():
    pass
