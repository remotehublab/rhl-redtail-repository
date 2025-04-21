"""Delete existing data

Revision ID: 8455c1b607cf
Revises: 85d323cc9b39
Create Date: 2025-04-21 11:40:08.125494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8455c1b607cf'
down_revision = '85d323cc9b39'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData()

    # 1) Clear all association tables first
    assoc_tables = [
        'lesson_device_framework_association',
        'simulation_framework_association',
        'simulation_device_category_association',
        'simulation_category_association',
        'device_category_association',
        'lesson_category_association',
        'lesson_level_association',
        'device_simulation',    # table name defined as 'device_simulation'
        'lesson_simulation',
        'lesson_device',
        'author_lesson',
    ]
    for name in assoc_tables:
        tbl = sa.Table(name, meta, autoload_with=conn)
        conn.execute(tbl.delete())

    # 2) Null out any User→Author foreign‐keys so we can delete all authors
    user_tbl = sa.Table('user', meta, autoload_with=conn)
    conn.execute(
        user_tbl.update()
        .values(author_id=None)
    )

    # 3) Delete all “child” rows (docs, images, videos, device frameworks)
    child_tables = [
        'simulation_device_document',
        'simulation_doc',
        'lesson_image',
        'lesson_video',
        'lesson_doc',
        'device_framework',
    ]
    for name in child_tables:
        tbl = sa.Table(name, meta, autoload_with=conn)
        conn.execute(tbl.delete())

    # 4) Finally delete the main domain rows
    main_tables = ['lesson', 'simulation', 'device', 'author']
    for name in main_tables:
        tbl = sa.Table(name, meta, autoload_with=conn)
        conn.execute(tbl.delete())


def downgrade():
    # Data deletion is irreversible
    pass

