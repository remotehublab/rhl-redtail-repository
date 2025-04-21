"""Add example data for Lessons

Revision ID: b860ddb11de4
Revises: f5856f4af0e3
Create Date: 2025-04-21 15:24:58.031469

"""
import datetime
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Table, MetaData

# revision identifiers, used by Alembic.
revision = 'b860ddb11de4'
down_revision = 'f5856f4af0e3'
branch_labels = None
depends_on = None



def upgrade():
    conn = op.get_bind()
    meta = MetaData()

    # Reflect tables
    author_table               = Table('author', meta, autoload_with=conn)
    lesson_table               = Table('lesson', meta, autoload_with=conn)
    author_lesson_assoc        = Table('author_lesson', meta, autoload_with=conn)
    lesson_doc_table           = Table('lesson_doc', meta, autoload_with=conn)

    # 1) Insert new author Luis Rodriguez Gil
    conn.execute(
        author_table.insert().values(
            login='luisrodriguezgil',
            name='Luis Rodriguez Gil (LabsLand)',
            link='https://labsland.com'
        )
    )

    # 2) Insert the lesson
    conn.execute(
        lesson_table.insert().values(
            name='Parking Lot (STM32 Nucleo WB55RG with STM32CubeMX)',
            slug='parking-lot-stm32-nucleo-wb55rg-stm32cubemx',
            short_description='Using the parking lot with the Nucleo WB55RG',
            long_description=(
                'Activity to conduct on the 3D smart parking model controlled with the real STM32 device. '
                'Design and implement a smart parking system logic using the STM Nucleo-WB55RG board in a remote lab setting. '
                'This interactive activity, hosted on LabsLand’s STM Nucleo-WB55RG remote laboratory, provides an immersive '
                'experience through a 3D virtual model of a parking system, which is controlled and interacts bidirectionally '
                'with the real STM device. You will develop your logic using C programming in an easy-to-use online IDE, '
                'without the need for physical hardware.'
            ),
            active=True,
            cover_image_url=(
                'https://redtail.rhlab.ece.uw.edu/public/images/lessons/'
                'parking-lot-stm32-nucleo-wb55rg.jpg'
            ),
            learning_goals='Interact with basic I/O',
            last_updated=datetime.datetime(2025, 1, 1),
        )
    )

    # 3) Fetch IDs
    lesson_id = conn.execute(
        sa.select(lesson_table.c.id)
          .where(lesson_table.c.slug == 'parking-lot-stm32-nucleo-wb55rg-stm32cubemx')
    ).scalar_one()

    author_labsland_id = conn.execute(
        sa.select(author_table.c.id)
          .where(author_table.c.login == 'labsland')
    ).scalar_one()
    author_luis_id = conn.execute(
        sa.select(author_table.c.id)
          .where(author_table.c.login == 'luisrodriguezgil')
    ).scalar_one()

    # 4) Associate authors with the lesson
    conn.execute(
        author_lesson_assoc.insert(),
        [
            {'author_id': author_labsland_id, 'lesson_id': lesson_id},
            {'author_id': author_luis_id,      'lesson_id': lesson_id},
        ]
    )

    # 5) Insert lesson documents
    docs = [
        {
            'lesson_id': lesson_id,
            'doc_url': 'https://labsland.com/pub/docs/experiments/stm32/Smart_Parking_Design_Activity_3D.docx',
            'title': 'Word document',
            'description': None,
            'is_solution': False,
            'last_updated': datetime.datetime(2025, 1, 1),
        },
        {
            'lesson_id': lesson_id,
            'doc_url': 'https://labsland.com/pub/docs/experiments/stm32/Smart_Parking_Design_Activity_3D.docx',
            'title': 'Solution',
            'description': None,
            'is_solution': True,
            'last_updated': datetime.datetime(2025, 1, 1),
        },
    ]
    conn.execute(lesson_doc_table.insert(), docs)


def downgrade():
    conn = op.get_bind()
    meta = MetaData()

    author_table         = Table('author', meta, autoload_with=conn)
    lesson_table         = Table('lesson', meta, autoload_with=conn)
    author_lesson_assoc  = Table('author_lesson', meta, autoload_with=conn)
    lesson_doc_table     = Table('lesson_doc', meta, autoload_with=conn)

    # Fetch the lesson ID
    lesson_id = conn.execute(
        sa.select(lesson_table.c.id)
          .where(lesson_table.c.slug == 'parking-lot-stm32-nucleo-wb55rg-stm32cubemx')
    ).scalar_one_or_none()

    if lesson_id:
        # 1) Remove lesson documents
        conn.execute(
            lesson_doc_table.delete()
              .where(lesson_doc_table.c.lesson_id == lesson_id)
        )

        # 2) Remove author associations
        conn.execute(
            author_lesson_assoc.delete()
              .where(author_lesson_assoc.c.lesson_id == lesson_id)
        )

        # 3) Delete the lesson
        conn.execute(
            lesson_table.delete()
              .where(lesson_table.c.id == lesson_id)
        )

    # 4) Delete the new author
    conn.execute(
        author_table.delete()
          .where(author_table.c.login == 'luisrodriguezgil')
    )
