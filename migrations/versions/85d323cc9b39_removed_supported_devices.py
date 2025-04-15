"""Removed supported Devices

Revision ID: 85d323cc9b39
Revises: 85bbb1cf787b
Create Date: 2025-04-14 23:35:42.736064
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '85d323cc9b39'
down_revision = '85bbb1cf787b'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('supported_device_lesson')
    op.drop_table('supported_device_simulation')

    with op.batch_alter_table('supported_device', schema=None) as batch_op:
        batch_op.drop_index('name')
        batch_op.drop_index('slug')

    op.drop_table('supported_device')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('role',
            existing_type=mysql.VARCHAR(length=100),
            nullable=True
        )


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('role',
            existing_type=mysql.VARCHAR(length=100),
            nullable=False
        )

    op.create_table(
        'supported_device',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('cover_image_url', sa.String(length=2083), nullable=True),
        sa.Column(
            'last_updated',
            sa.DateTime(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False
        ),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci'
    )

    with op.batch_alter_table('supported_device', schema=None) as batch_op:
        batch_op.create_index('slug', ['slug'], unique=True)
        batch_op.create_index('name', ['name'], unique=True)

    op.create_table(
        'supported_device_simulation',
        sa.Column('supported_device_id', sa.Integer(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulation.id']),
        sa.ForeignKeyConstraint(['supported_device_id'], ['supported_device.id']),
        sa.PrimaryKeyConstraint('supported_device_id', 'simulation_id'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci'
    )

    op.create_table(
        'supported_device_lesson',
        sa.Column('supported_device_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id']),
        sa.ForeignKeyConstraint(['supported_device_id'], ['supported_device.id']),
        sa.PrimaryKeyConstraint('supported_device_id', 'lesson_id'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4',
        mysql_collate='utf8mb4_0900_ai_ci'
    )
