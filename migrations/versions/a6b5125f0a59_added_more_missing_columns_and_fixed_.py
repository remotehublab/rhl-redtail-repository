"""Added more missing columns and fixed attribute names

Revision ID: a6b5125f0a59
Revises: 31b336730081
Create Date: 2025-02-14 00:07:33.772773

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import table, column
import datetime, re

# revision identifiers, used by Alembic.
revision = 'a6b5125f0a59'
down_revision = '31b336730081'
branch_labels = None
depends_on = None

def generate_slug(name):
    return re.sub(r'[^a-zA-Z0-9]+', '-', name.strip().lower()).strip('-')

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    
    with op.batch_alter_table('simulation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('cover_image_url', sa.String(length=2083), nullable=True))
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
        batch_op.create_unique_constraint(None, ['slug'])
    
    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cover_image_url', sa.String(length=2083), nullable=True))
        batch_op.drop_column('cover_image')

    device_table = table(
        'device',
        column('id', sa.Integer),
        column('name', sa.String),
        column('slug', sa.String),
        column('image_url', sa.String),
        column('last_updated', sa.DateTime)
    )

    simulation_table = table(
        'simulation',
        column('id', sa.Integer),
        column('name', sa.String),
        column('slug', sa.String),
        column('cover_image_url', sa.String),
        column('last_updated', sa.DateTime)
    )

    lesson_table = table(
        'lesson',
        column('id', sa.Integer),
        column('name', sa.String),
        column('slug', sa.String),
        column('short_description', sa.String),
        column('active', sa.Boolean),
        column('cover_image_url', sa.String),
        column('long_description', sa.Text),
        column('learning_goals', sa.Text),
        column('level', sa.String),
        column('last_updated', sa.DateTime)
    )

    conn = op.get_bind()
    results = conn.execute(sa.select(device_table.c.id, device_table.c.name)).fetchall()
    for row in results:
        slug = generate_slug(row.name)
        conn.execute(
            device_table.update()
            .where(device_table.c.id == row.id)
            .values(
                slug=slug,
                image_url="",
                last_updated=datetime.datetime.now()
            )
        )

    results = conn.execute(sa.select(simulation_table.c.id, simulation_table.c.name)).fetchall()
    for row in results:
        slug = generate_slug(row.name)
        conn.execute(
            simulation_table.update()
            .where(simulation_table.c.id == row.id)
            .values(
                slug=slug,
                cover_image_url="",
                last_updated=datetime.datetime.now()
            )
        )

    results = conn.execute(sa.select(lesson_table.c.id, lesson_table.c.name, lesson_table.c.short_description)).fetchall()
    for row in results:
        slug = generate_slug(row.name)
        short_desc = row.short_description if row.short_description else "No description available."
        conn.execute(
            lesson_table.update()
            .where(lesson_table.c.id == row.id)
            .values(
                slug=slug,
                active=True,
                short_description=short_desc,
                cover_image_url="",
                long_description="Placeholder description.",
                learning_goals="Plceholder learning goal.",
                level="Beginner",
                last_updated=datetime.datetime.now()
            )
        )
    
    with op.batch_alter_table('simulation', schema=None) as batch_op:
        batch_op.alter_column('slug',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)

    with op.batch_alter_table('device', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cover_image_url', sa.String(length=2083), nullable=True))
        batch_op.alter_column('slug',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
        batch_op.drop_column('image_url')

    with op.batch_alter_table('supported_device', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('cover_image_url', sa.String(length=2083), nullable=True))
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
        batch_op.create_unique_constraint(None, ['slug'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('supported_device', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('last_updated')
        batch_op.drop_column('cover_image_url')
        batch_op.drop_column('slug')

    with op.batch_alter_table('simulation', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('last_updated')
        batch_op.drop_column('cover_image_url')
        batch_op.drop_column('slug')

    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cover_image', mysql.VARCHAR(length=255), nullable=True))
        batch_op.drop_column('cover_image_url')

    with op.batch_alter_table('device', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', mysql.VARCHAR(length=2083), nullable=True))
        batch_op.alter_column('slug',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
        batch_op.drop_column('cover_image_url')

    
    # ### end Alembic commands ###
