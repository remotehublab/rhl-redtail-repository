"""Unified table names

Revision ID: 6326d264a1ff
Revises: 64a0cc9a0a0f
Create Date: 2025-02-03 21:12:26.751826

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6326d264a1ff'
down_revision = '64a0cc9a0a0f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('lesson_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('simulation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('lesson',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('short_description', sa.String(length=255), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['lesson_category.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('lesson_doc',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('doc_url', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lesson_image',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('image_url', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lesson_video',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=False),
    sa.Column('video_url', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lesson.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('lesson_videos')


    op.drop_table('lesson_docs')

    op.drop_table('lesson_images')
    with op.batch_alter_table('author_lesson', schema=None) as batch_op:
        batch_op.drop_constraint('author_lesson_ibfk_2', type_='foreignkey')
        batch_op.create_foreign_key(None, 'lesson', ['lesson_id'], ['id'])

    with op.batch_alter_table('device_simulation', schema=None) as batch_op:
        batch_op.drop_constraint('device_simulation_ibfk_1', type_='foreignkey')
        batch_op.drop_constraint('device_simulation_ibfk_2', type_='foreignkey')
        batch_op.create_foreign_key(None, 'simulation', ['simulation_id'], ['id'])
        batch_op.create_foreign_key(None, 'device', ['device_id'], ['id'])

    with op.batch_alter_table('lesson_device', schema=None) as batch_op:
        batch_op.drop_constraint('lesson_device_ibfk_2', type_='foreignkey')
        batch_op.drop_constraint('lesson_device_ibfk_1', type_='foreignkey')
        batch_op.create_foreign_key(None, 'device', ['device_id'], ['id'])
        batch_op.create_foreign_key(None, 'lesson', ['lesson_id'], ['id'])

    with op.batch_alter_table('lesson_simulation', schema=None) as batch_op:
        batch_op.drop_constraint('lesson_simulation_ibfk_2', type_='foreignkey')
        batch_op.drop_constraint('lesson_simulation_ibfk_1', type_='foreignkey')
        batch_op.create_foreign_key(None, 'simulation', ['simulation_id'], ['id'])
        batch_op.create_foreign_key(None, 'lesson', ['lesson_id'], ['id'])

    with op.batch_alter_table('simulations', schema=None) as batch_op:
        batch_op.drop_index('name')

    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.drop_index('name')

    op.drop_table('devices')

    op.drop_table('simulations')

    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.drop_index('name')

    op.drop_table('lessons')

    with op.batch_alter_table('lesson_categories', schema=None) as batch_op:
        batch_op.drop_index('name')
        batch_op.drop_index('slug')

    op.drop_table('lesson_categories')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('lesson_simulation', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('lesson_simulation_ibfk_1', 'lessons', ['lesson_id'], ['id'])
        batch_op.create_foreign_key('lesson_simulation_ibfk_2', 'simulations', ['simulation_id'], ['id'])

    with op.batch_alter_table('lesson_device', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('lesson_device_ibfk_1', 'devices', ['device_id'], ['id'])
        batch_op.create_foreign_key('lesson_device_ibfk_2', 'lessons', ['lesson_id'], ['id'])

    with op.batch_alter_table('device_simulation', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('device_simulation_ibfk_2', 'simulations', ['simulation_id'], ['id'])
        batch_op.create_foreign_key('device_simulation_ibfk_1', 'devices', ['device_id'], ['id'])

    with op.batch_alter_table('author_lesson', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('author_lesson_ibfk_2', 'lessons', ['lesson_id'], ['id'])

    op.create_table('lesson_images',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('lesson_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('image_url', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('title', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('description', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name='lesson_images_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('devices',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('description', mysql.TEXT(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.create_index('name', ['name'], unique=True)

    op.create_table('lesson_categories',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('slug', mysql.VARCHAR(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('lesson_categories', schema=None) as batch_op:
        batch_op.create_index('slug', ['slug'], unique=True)
        batch_op.create_index('name', ['name'], unique=True)

    op.create_table('simulations',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('description', mysql.TEXT(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('simulations', schema=None) as batch_op:
        batch_op.create_index('name', ['name'], unique=True)

    op.create_table('lesson_docs',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('lesson_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('doc_url', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('title', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('description', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name='lesson_docs_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('lessons',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('short_description', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('active', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('category_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['lesson_categories.id'], name='lessons_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.create_index('name', ['name'], unique=True)

    op.create_table('lesson_videos',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('lesson_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('video_url', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('title', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('description', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name='lesson_videos_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('lesson_video')
    op.drop_table('lesson_image')
    op.drop_table('lesson_doc')
    op.drop_table('lesson')
    op.drop_table('simulation')
    op.drop_table('lesson_category')
    op.drop_table('device')
    # ### end Alembic commands ###
