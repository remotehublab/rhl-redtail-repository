"""Add example data

Revision ID: 31728de70194
Revises: 8e898549b8db
Create Date: 2025-02-11 10:58:21.576211

"""
import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, Text, DateTime


# revision identifiers, used by Alembic.
revision = '31728de70194'
down_revision = '8e898549b8db'
branch_labels = None
depends_on = None

device_table = Table(
    'device',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True),
    Column('description', Text),
)

simulation_table = Table(
    'simulation',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True),
    Column('description', Text),
)

lesson_category_table = Table(
    'lesson_category',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True),
    Column('slug', String(100), unique=True),
)

lesson_table = Table(
    'lesson',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True),
    Column('slug', String(255), unique=True),
    Column('short_description', String(255)),
    Column('active', Boolean),
    Column('category_id', Integer),
    Column('last_updated', DateTime),
)

def upgrade():
    device_table_data = [
        {
            'name': "STM32 WB55RG",
            'description': "STM32 Nucleo WB55RG microprocessor"
        },
        {
            'name': "FPGA DE1-SoC",
            'description': "Altera Cyclone V FPGA in a DE1-SoC board"
        },
        {
            'name': "Raspberry Pi Pico",
            'description': "Raspberry Pi Pico 1 microcontroller"
        },
    ]
    
    # missing device:
    # - device image
    # - last update
    # - slug
    # - device subcategories (new table, with last update, slug, name...)

    simulation_table_data = [
        {
            'name': "Parking Lot",
            'description': "Parking lot simulation with 5 sensors and 6 actuators"
        },
        {
            'name': "KeyPad",
            'description': "KeyPad simulation",
        },
        {
            'name': "NES Controller",
            'description': "NES Controller simulation with serial communication",
        },
        {
            'name': "Door",
            'description': "Simple door simulation with 2 sensors",
        },
    ]

    # Missing:
    # - slug
    # - image
    # - documents for the device
    #
    # - simulation categories (e.g., Digital Twin, Real-world, etc.)
    # - link to the device subcategories

    lesson_categories_data = [
        {
            'name': "Digital Twin",
            'slug': "digital-twin",
        },
        {
            'name': "Simulation",
            'slug': "simulation",
        },
        {
            'name': "Real-World",
            'slug': "real-world",
        }
    ]

    op.bulk_insert(lesson_category_table, lesson_categories_data)


    result = op.get_bind().execute(sa.select(lesson_category_table.c.id).limit(1))
    first_category_id = result.scalar()

    lessons_data = [
        {
            'name': "NES Controller Exercise",
            'slug': "nes-controller-exercise",
            'short_description': "In this exercise we do blah blah",
            'active': True,
            'category_id': first_category_id,
            'last_updated': datetime.datetime.now(),
        },
        {
            'name': "Parking Lot Exercise",
            'slug': "parking-lot-exercise",
            'short_description': "In this exercise we do blah blah",
            'active': True,
            'category_id': first_category_id,
            'last_updated': datetime.datetime.now(),
        },
    ]
    
    # Missing:
    # - cover image (url)
    # - long description (Text)
    # - learning goals (another Text)
    # - level
    # 
    # Also:
    # + something for solutions (either new table or update lessondoc to include a flag for is_solution or similar)
    # + One Lesson can be in multiple categories
    # + Links to device subcategories

    op.bulk_insert(device_table, device_table_data)
    op.bulk_insert(simulation_table, simulation_table_data)
    op.bulk_insert(lesson_table, lessons_data)


def downgrade():
    pass
