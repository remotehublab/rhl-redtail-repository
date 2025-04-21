"""Add metadata to the lesson

Revision ID: 7719a626bae2
Revises: b860ddb11de4
Create Date: 2025-04-21 15:28:25.574915

"""
import datetime
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Table, MetaData

# revision identifiers, used by Alembic.
revision = '7719a626bae2'
down_revision = 'b860ddb11de4'
branch_labels = None
depends_on = None



def upgrade():
    conn = op.get_bind()
    meta = MetaData()

    # Reflect necessary tables
    lesson_table                    = Table('lesson', meta, autoload_with=conn)
    lesson_category_table           = Table('lesson_category', meta, autoload_with=conn)
    lesson_category_assoc           = Table('lesson_category_association', meta, autoload_with=conn)
    lesson_level_table              = Table('lesson_level', meta, autoload_with=conn)
    lesson_level_assoc              = Table('lesson_level_association', meta, autoload_with=conn)
    device_framework_table          = Table('device_framework', meta, autoload_with=conn)
    lesson_device_framework_assoc   = Table('lesson_device_framework_association', meta, autoload_with=conn)
    simulation_table                = Table('simulation', meta, autoload_with=conn)
    lesson_simulation_assoc         = Table('lesson_simulation', meta, autoload_with=conn)

    # 1) Lookup the lesson
    lesson_id = conn.execute(
        sa.select(lesson_table.c.id)
          .where(lesson_table.c.slug == 'parking-lot-stm32-nucleo-wb55rg-stm32cubemx')
    ).scalar_one()

    # a) Associate Real‑World & Simulation categories
    sim_cat_id  = conn.execute(
        sa.select(lesson_category_table.c.id)
          .where(lesson_category_table.c.slug == 'simulation')
    ).scalar_one()
    real_cat_id = conn.execute(
        sa.select(lesson_category_table.c.id)
          .where(lesson_category_table.c.slug == 'real-world')
    ).scalar_one()

    conn.execute(lesson_category_assoc.insert(), [
        {'lesson_id': lesson_id, 'category_id': sim_cat_id},
        {'lesson_id': lesson_id, 'category_id': real_cat_id},
    ])

    # b) Create "Basic" level and assign it
    conn.execute(
        lesson_level_table.insert().values(
            name='Basic',
            slug='basic',
            last_updated=datetime.datetime(2025, 1, 1)
        )
    )
    basic_level_id = conn.execute(
        sa.select(lesson_level_table.c.id)
          .where(lesson_level_table.c.slug == 'basic')
    ).scalar_one()

    conn.execute(
        lesson_level_assoc.insert().values(
            lesson_id=lesson_id,
            level_id=basic_level_id
        )
    )

    # c) Add STM32CubeMX & Online IDE frameworks
    fw1_id = conn.execute(
        sa.select(device_framework_table.c.id)
          .where(device_framework_table.c.slug == 'stm32-nucleo-wb55rg-stm32cubemx')
    ).scalar_one()
    fw2_id = conn.execute(
        sa.select(device_framework_table.c.id)
          .where(device_framework_table.c.slug == 'stm32-nucleo-wb55rg-stm32cubemx-online')
    ).scalar_one()

    conn.execute(lesson_device_framework_assoc.insert(), [
        {'lesson_id': lesson_id, 'framework_id': fw1_id},
        {'lesson_id': lesson_id, 'framework_id': fw2_id},
    ])

    # d) Associate with the Parking Lot simulation
    parking_sim_id = conn.execute(
        sa.select(simulation_table.c.id)
          .where(simulation_table.c.slug == 'parking-lot')
    ).scalar_one()

    conn.execute(
        lesson_simulation_assoc.insert().values(
            lesson_id=lesson_id,
            simulation_id=parking_sim_id
        )
    )


def downgrade():
    conn = op.get_bind()
    meta = MetaData()

    lesson_table                  = Table('lesson', meta, autoload_with=conn)
    lesson_category_assoc         = Table('lesson_category_association', meta, autoload_with=conn)
    lesson_level_table            = Table('lesson_level', meta, autoload_with=conn)
    lesson_level_assoc            = Table('lesson_level_association', meta, autoload_with=conn)
    lesson_device_framework_assoc = Table('lesson_device_framework_association', meta, autoload_with=conn)
    simulation_table              = Table('simulation', meta, autoload_with=conn)
    lesson_simulation_assoc       = Table('lesson_simulation', meta, autoload_with=conn)

    # Find IDs again
    lesson_id = conn.execute(
        sa.select(lesson_table.c.id)
          .where(lesson_table.c.slug == 'parking-lot-stm32-nucleo-wb55rg-stm32cubemx')
    ).scalar_one_or_none()
    if not lesson_id:
        return

    # d) Remove lesson–simulation link
    parking_sim_id = conn.execute(
        sa.select(simulation_table.c.id)
          .where(simulation_table.c.slug == 'parking-lot')
    ).scalar_one()
    conn.execute(
        lesson_simulation_assoc.delete().where(
            sa.and_(
                lesson_simulation_assoc.c.lesson_id == lesson_id,
                lesson_simulation_assoc.c.simulation_id == parking_sim_id
            )
        )
    )

    # c) Remove the two framework links
    for fw_slug in (
        'stm32-nucleo-wb55rg-stm32cubemx',
        'stm32-nucleo-wb55rg-stm32cubemx-online'
    ):
        fw_id = conn.execute(
            sa.select(device_framework_table.c.id)
              .where(device_framework_table.c.slug == fw_slug)
        ).scalar_one()
        conn.execute(
            lesson_device_framework_assoc.delete().where(
                sa.and_(
                    lesson_device_framework_assoc.c.lesson_id == lesson_id,
                    lesson_device_framework_assoc.c.framework_id == fw_id
                )
            )
        )

    # b) Remove the Basic level association and the level row itself
    basic_level_id = conn.execute(
        sa.select(lesson_level_table.c.id)
          .where(lesson_level_table.c.slug == 'basic')
    ).scalar_one_or_none()
    if basic_level_id:
        conn.execute(
            lesson_level_assoc.delete().where(
                sa.and_(
                    lesson_level_assoc.c.lesson_id == lesson_id,
                    lesson_level_assoc.c.level_id == basic_level_id
                )
            )
        )
        conn.execute(
            lesson_level_table.delete().where(
                lesson_level_table.c.id == basic_level_id
            )
        )

    # a) Remove category associations
    for cat_slug in ('simulation', 'real-world'):
        cat_id = conn.execute(
            sa.select(lesson_category_table.c.id)
              .where(lesson_category_table.c.slug == cat_slug)
        ).scalar_one()
        conn.execute(
            lesson_category_assoc.delete().where(
                sa.and_(
                    lesson_category_assoc.c.lesson_id == lesson_id,
                    lesson_category_assoc.c.category_id == cat_id
                )
            )
        )
