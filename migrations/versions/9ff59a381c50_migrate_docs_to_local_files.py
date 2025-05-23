"""Migrate docs to local files

Revision ID: 9ff59a381c50
Revises: dd7f87b5d96d
Create Date: 2025-05-23 11:46:26.980737

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, MetaData, update


# revision identifiers, used by Alembic.
revision = '9ff59a381c50'
down_revision = 'dd7f87b5d96d'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    meta = MetaData()

    sim_doc_table           = Table('simulation_doc', meta, autoload_with=conn)
    sim_dev_doc_table       = Table('simulation_device_document', meta, autoload_with=conn)

    # Update simulation_doc
    conn.execute(
        update(sim_doc_table)
        .values(doc_url=sa.func.replace(sim_doc_table.c.doc_url, 'https://redtail.rhlab.ece.uw.edu/', ''))
    )

    # Update simulation_device_document
    conn.execute(
        update(sim_dev_doc_table)
        .values(doc_url=sa.func.replace(sim_dev_doc_table.c.doc_url, 'https://redtail.rhlab.ece.uw.edu/', ''))
    )


def downgrade():
    pass
