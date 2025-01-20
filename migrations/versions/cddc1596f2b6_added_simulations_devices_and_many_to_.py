"""Added Simulations, Devices, and many to many relationships for Author-Lesson, Lesson-Simulation, Lesson-Device, Simulation-Device

Revision ID: cddc1596f2b6
Revises: e177703528e8
Create Date: 2025-01-20 02:04:16.315812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cddc1596f2b6'
down_revision = 'e177703528e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('simulations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('author_lesson',
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['author.id'], ),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
    sa.PrimaryKeyConstraint('author_id', 'lesson_id')
    )
    op.create_table('device_simulation',
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('simulation_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ),
    sa.PrimaryKeyConstraint('device_id', 'simulation_id')
    )
    op.create_table('lesson_device',
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
    sa.PrimaryKeyConstraint('lesson_id', 'device_id')
    )
    op.create_table('lesson_simulation',
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('simulation_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
    sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ),
    sa.PrimaryKeyConstraint('lesson_id', 'simulation_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lesson_simulation')
    op.drop_table('lesson_device')
    op.drop_table('device_simulation')
    op.drop_table('author_lesson')
    op.drop_table('simulations')
    op.drop_table('devices')
    # ### end Alembic commands ###
