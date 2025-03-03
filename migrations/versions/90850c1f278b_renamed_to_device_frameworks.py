"""Renamed device_subcategory to device_framework

Revision ID: 90850c1f278b
Revises: 3d5bc741ee47
Create Date: 2025-03-02 21:33:06.315205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90850c1f278b'
down_revision = '3d5bc741ee47'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('device_subcategory', 'device_framework')
    op.rename_table('device_subcategory_association', 'device_framework_association')
    op.rename_table('lesson_device_subcategory_association', 'lesson_device_framework_association')

    with op.batch_alter_table('device_framework_association') as batch_op:
        batch_op.alter_column('subcategory_id', new_column_name='framework_id',
                              existing_type=sa.Integer, nullable=False)

    with op.batch_alter_table('lesson_device_framework_association') as batch_op:
        batch_op.alter_column('subcategory_id', new_column_name='framework_id',
                              existing_type=sa.Integer, nullable=False)

    with op.batch_alter_table('device_framework') as batch_op:
        batch_op.drop_index('name')
        batch_op.drop_index('slug')
        batch_op.create_index('name', ['name'], unique=True)
        batch_op.create_index('slug', ['slug'], unique=True)


def downgrade():
    op.rename_table('device_framework', 'device_subcategory')
    op.rename_table('device_framework_association', 'device_subcategory_association')
    op.rename_table('lesson_device_framework_association', 'lesson_device_subcategory_association')

    with op.batch_alter_table('device_subcategory_association') as batch_op:
        batch_op.alter_column('framework_id', new_column_name='subcategory_id',
                              existing_type=sa.Integer, nullable=False)

    with op.batch_alter_table('lesson_device_subcategory_association') as batch_op:
        batch_op.alter_column('framework_id', new_column_name='subcategory_id',
                              existing_type=sa.Integer, nullable=False)

    with op.batch_alter_table('device_subcategory') as batch_op:
        batch_op.drop_index('name')
        batch_op.drop_index('slug')
        batch_op.create_index('name', ['name'], unique=True)
        batch_op.create_index('slug', ['slug'], unique=True)
