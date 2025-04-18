"""Added lesson levels and device subcategories

Revision ID: 3d5bc741ee47
Revises: 9d35284b47bc
Create Date: 2025-02-24 01:32:37.168158

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3d5bc741ee47'
down_revision = '9d35284b47bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device_subcategory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('lesson_level',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('device_subcategory_association',
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('subcategory_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['subcategory_id'], ['device_subcategory.id'], ),
    sa.PrimaryKeyConstraint('device_id', 'subcategory_id')
    )
    op.create_table('lesson_device_subcategory_association',
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('subcategory_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.ForeignKeyConstraint(['subcategory_id'], ['device_subcategory.id'], ),
    sa.PrimaryKeyConstraint('lesson_id', 'subcategory_id')
    )
    op.create_table('lesson_level_association',
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('level_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.ForeignKeyConstraint(['level_id'], ['lesson_level.id'], ),
    sa.PrimaryKeyConstraint('lesson_id', 'level_id')
    )
    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.drop_column('level')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.add_column(sa.Column('level', mysql.VARCHAR(length=50), nullable=True))

    op.drop_table('lesson_level_association')
    op.drop_table('lesson_device_subcategory_association')
    op.drop_table('device_subcategory_association')
    op.drop_table('lesson_level')
    op.drop_table('device_subcategory')
    # ### end Alembic commands ###
