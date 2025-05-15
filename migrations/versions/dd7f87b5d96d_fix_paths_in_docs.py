"""Fix paths in docs

Revision ID: dd7f87b5d96d
Revises: 7f4db1d102db
Create Date: 2025-05-15 12:02:06.961306

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, MetaData, update


# revision identifiers, used by Alembic.
revision = 'dd7f87b5d96d'
down_revision = '7f4db1d102db'
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
        .values(doc_url=sa.func.replace(sim_doc_table.c.doc_url, '/images/docs/', '/docs/'))
    )

    # Update simulation_device_document
    conn.execute(
        update(sim_dev_doc_table)
        .values(doc_url=sa.func.replace(sim_dev_doc_table.c.doc_url, '/images/docs/', '/docs/'))
    )


def downgrade():
    pass

