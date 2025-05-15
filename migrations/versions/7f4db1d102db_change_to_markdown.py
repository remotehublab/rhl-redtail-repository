"""Change to markdown

Revision ID: 7f4db1d102db
Revises: 8dcc12e424b1
Create Date: 2025-05-15 01:12:32.674386

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy import Table, MetaData, update


# revision identifiers, used by Alembic.
revision = '7f4db1d102db'
down_revision = '8dcc12e424b1'
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
        .where(sim_doc_table.c.doc_url.like('%.pdf'))
        .values(doc_url=sa.func.replace(sim_doc_table.c.doc_url, '.pdf', '.md'))
    )

    # Update simulation_device_document
    conn.execute(
        update(sim_dev_doc_table)
        .where(sim_dev_doc_table.c.doc_url.like('%.pdf'))
        .values(doc_url=sa.func.replace(sim_dev_doc_table.c.doc_url, '.pdf', '.md'))
    )
    


def downgrade():
    pass
