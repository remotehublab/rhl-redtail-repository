"""Link categories to lessons, etc.

Revision ID: 9d35284b47bc
Revises: e23b428b9e5d
Create Date: 2025-02-18 11:19:18.823922

"""
import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, Text, DateTime

# revision identifiers, used by Alembic.
revision = '9d35284b47bc'
down_revision = 'e23b428b9e5d'
branch_labels = None
depends_on = None

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
    Column('slug', String(100), unique=True),
)

lesson_category_association_table = Table(
    'lesson_category_association',
    MetaData(),
    Column('lesson_id', Integer, primary_key=True),
    Column('category_id', Integer, primary_key=True),
)

simulation_category_table = Table(
    'simulation_category',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True),
    Column('slug', String(255), unique=True),
    Column('last_updated', DateTime, unique=True),
)

simulation_table = Table(
    'simulation',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('slug', String(100), unique=True),
)

simulation_category_association_table = Table(
    'simulation_category_association',
    MetaData(),
    Column('simulation_id', Integer, primary_key=True),
    Column('category_id', Integer, primary_key=True),
)

device_category_table = Table(
    'device_category',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True),
    Column('slug', String(255), unique=True),
    Column('last_updated', DateTime, unique=True),
)

device_table = Table(
    'device',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('slug', String(255), unique=True),
)

device_category_association_table = Table(
    'device_category_association',
    MetaData(),
    Column('device_id', Integer, primary_key=True),
    Column('device_category_id', Integer, primary_key=True),
)

def upgrade():

    simulation_category_data = [
        {
            'name': "Simulation",
            'slug': "simulation",
            'last_updated': datetime.datetime.utcnow(),
        },
        {
            'name': "Real World",
            'slug': "real-world",
            'last_updated': datetime.datetime.utcnow(),
        },
        {
            'name': "Digital Twin",
            'slug': "digital-twin",
            'last_updated': datetime.datetime.utcnow(),
        },
    ]

    op.bulk_insert(simulation_category_table, simulation_category_data)
    
    device_category_data = [
        {
            'name': "Microcontroller",
            'slug': "microcontroller",
            'last_updated': datetime.datetime.utcnow(),
        },
        {
            'name': "ARM",
            'slug': "arm",
            'last_updated': datetime.datetime.utcnow(),
        },
        {
            'name': "FPGA",
            'slug': "fpga",
            'last_updated': datetime.datetime.utcnow(),
        },
    ]

    op.bulk_insert(device_category_table, device_category_data)
    

    # List of rows of lesson categories
    lesson_category_existing_data_by_slug = { row[1]: row[0] for row in op.get_bind().execute(sa.select(lesson_category_table.c.id, lesson_category_table.c.slug)) }

    # List of rows of lessons
    lesson_existing_data_by_slug = { row[1]: row[0] for row in op.get_bind().execute(sa.select(lesson_table.c.id, lesson_table.c.slug)) }

    # List of rows of device categories
    device_category_existing_data_by_slug = { row[1]: row[0] for row in op.get_bind().execute(sa.select(device_category_table.c.id, device_category_table.c.slug)) }

    # List of rows of devices
    device_existing_data_by_slug = { row[1]: row[0] for row in op.get_bind().execute(sa.select(device_table.c.id, device_table.c.slug)) }

    # List of rows of device categories
    simulation_category_existing_data_by_slug = { row[1]: row[0] for row in op.get_bind().execute(sa.select(simulation_category_table.c.id, simulation_category_table.c.slug)) }

    # List of rows of simulation
    simulation_existing_data_by_slug = { row[1]: row[0] for row in op.get_bind().execute(sa.select(simulation_table.c.id, simulation_table.c.slug)) }

    lesson_category_association_data = [
        {
            'lesson_id': lesson_existing_data_by_slug['parking-lot-exercise'],
            'category_id': lesson_category_existing_data_by_slug['simulation'],
        },
        {
            'lesson_id': lesson_existing_data_by_slug['parking-lot-exercise'],
            'category_id': lesson_category_existing_data_by_slug['real-world'],
        },
        {
            'lesson_id': lesson_existing_data_by_slug['nes-controller-exercise'],
            'category_id': lesson_category_existing_data_by_slug['digital-twin'],
        },
    ]

    op.bulk_insert(lesson_category_association_table, lesson_category_association_data)

    device_category_association_data = [
        {
            'device_id': device_existing_data_by_slug['stm32-wb55rg'],
            'device_category_id': device_category_existing_data_by_slug['microcontroller'],
        },
        {
            'device_id': device_existing_data_by_slug['stm32-wb55rg'],
            'device_category_id': device_category_existing_data_by_slug['arm'],
        },
        {
            'device_id': device_existing_data_by_slug['fpga-de1-soc'],
            'device_category_id': device_category_existing_data_by_slug['fpga'],
        },
        {
            'device_id': device_existing_data_by_slug['raspberry-pi-pico'],
            'device_category_id': device_category_existing_data_by_slug['microcontroller'],
        },
        {
            'device_id': device_existing_data_by_slug['raspberry-pi-pico'],
            'device_category_id': device_category_existing_data_by_slug['arm'],
        },
    ]

    op.bulk_insert(device_category_association_table, device_category_association_data)

    simulation_category_association_data = [
        {
            'simulation_id': simulation_existing_data_by_slug['parking-lot'],
            'category_id': simulation_category_existing_data_by_slug['simulation'],
        },
        {
            'simulation_id': simulation_existing_data_by_slug['parking-lot'],
            'category_id': simulation_category_existing_data_by_slug['real-world'],
        },
        {
            'simulation_id': simulation_existing_data_by_slug['door'],
            'category_id': simulation_category_existing_data_by_slug['real-world'],
        },
        {
            'simulation_id': simulation_existing_data_by_slug['door'],
            'category_id': simulation_category_existing_data_by_slug['simulation'],
        },
        {
            'simulation_id': simulation_existing_data_by_slug['keypad'],
            'category_id': simulation_category_existing_data_by_slug['digital-twin'],
        },
        {
            'simulation_id': simulation_existing_data_by_slug['nes-controller'],
            'category_id': simulation_category_existing_data_by_slug['digital-twin'],
        },
    ]

    op.bulk_insert(simulation_category_association_table, simulation_category_association_data)


def downgrade():
    pass
