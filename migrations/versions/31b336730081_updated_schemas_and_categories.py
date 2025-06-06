"""Updated schemas and categories

Revision ID: 31b336730081
Revises: 31728de70194
Create Date: 2025-02-13 17:01:38.776603

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '31b336730081'
down_revision = '31728de70194'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('last_updated', sa.DateTime(),
                  server_default=sa.text('NOW()'),
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_table('simulation_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('last_updated', sa.DateTime(),
                  server_default=sa.text('NOW()'),
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    op.create_table('device_category_association',
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('device_category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['device_category_id'], ['device_category.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
        sa.PrimaryKeyConstraint('device_id', 'device_category_id')
    )
    op.create_table('device_doc',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('doc_url', sa.String(length=2083), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(),
                  server_default=sa.text('NOW()'),
                  nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lesson_category_association',
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['lesson_category.id'], ),
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
        sa.PrimaryKeyConstraint('lesson_id', 'category_id')
    )
    op.create_table('simulation_category_association',
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['simulation_category.id'], ),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulation.id'], ),
        sa.PrimaryKeyConstraint('simulation_id', 'category_id')
    )
    op.create_table('simulation_device_category_association',
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('device_category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['device_category_id'], ['device_category.id'], ),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulation.id'], ),
        sa.PrimaryKeyConstraint('simulation_id', 'device_category_id')
    )

    # Make new columns nullable=True or provide a default
    with op.batch_alter_table('device', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('image_url', sa.String(length=2083), nullable=True))
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(),
                                      server_default=sa.text('NOW()'),
                                      nullable=False))
        batch_op.create_unique_constraint('uq_device_slug', ['slug'])

    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cover_image', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('long_description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('learning_goals', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('level', sa.String(length=50), nullable=True))
        batch_op.drop_constraint('lesson_ibfk_1', type_='foreignkey')
        batch_op.drop_column('category_id')

    with op.batch_alter_table('lesson_category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(),
                                      server_default=sa.text('NOW()'),
                                      nullable=False))

    with op.batch_alter_table('lesson_doc', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_solution', sa.Boolean(),
                                      server_default=sa.text('0'),
                                      nullable=False))
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(),
                                      server_default=sa.text('NOW()'),
                                      nullable=False))
        batch_op.alter_column('doc_url',
                              existing_type=mysql.VARCHAR(length=255),
                              type_=sa.String(length=2083),
                              existing_nullable=False)

    with op.batch_alter_table('lesson_image', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(),
                                      server_default=sa.text('NOW()'),
                                      nullable=False))
        batch_op.alter_column('image_url',
                              existing_type=mysql.VARCHAR(length=255),
                              type_=sa.String(length=2083),
                              existing_nullable=False)

    with op.batch_alter_table('lesson_video', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_updated', sa.DateTime(),
                                      server_default=sa.text('NOW()'),
                                      nullable=False))
        batch_op.alter_column('video_url',
                              existing_type=mysql.VARCHAR(length=255),
                              type_=sa.String(length=2083),
                              existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson_video', schema=None) as batch_op:
        batch_op.alter_column('video_url',
                              existing_type=sa.String(length=2083),
                              type_=mysql.VARCHAR(length=255),
                              existing_nullable=False)
        batch_op.drop_column('last_updated')

    with op.batch_alter_table('lesson_image', schema=None) as batch_op:
        batch_op.alter_column('image_url',
                              existing_type=sa.String(length=2083),
                              type_=mysql.VARCHAR(length=255),
                              existing_nullable=False)
        batch_op.drop_column('last_updated')

    with op.batch_alter_table('lesson_doc', schema=None) as batch_op:
        batch_op.alter_column('doc_url',
                              existing_type=sa.String(length=2083),
                              type_=mysql.VARCHAR(length=255),
                              existing_nullable=False)
        batch_op.drop_column('last_updated')
        batch_op.drop_column('is_solution')

    with op.batch_alter_table('lesson_category', schema=None) as batch_op:
        batch_op.drop_column('last_updated')

    with op.batch_alter_table('lesson', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', mysql.INTEGER(), autoincrement=False, nullable=False))
        batch_op.create_foreign_key('lesson_ibfk_1', 'lesson_category', ['category_id'], ['id'])
        batch_op.drop_column('level')
        batch_op.drop_column('learning_goals')
        batch_op.drop_column('long_description')
        batch_op.drop_column('cover_image')

    with op.batch_alter_table('device', schema=None) as batch_op:
        batch_op.drop_constraint('uq_device_slug', type_='unique')
        batch_op.drop_column('last_updated')
        batch_op.drop_column('image_url')
        batch_op.drop_column('slug')

    op.drop_table('simulation_device_category_association')
    op.drop_table('simulation_category_association')
    op.drop_table('lesson_category_association')
    op.drop_table('device_doc')
    op.drop_table('device_category_association')
    op.drop_table('simulation_category')
    op.drop_table('device_category')
    # ### end Alembic commands ###
