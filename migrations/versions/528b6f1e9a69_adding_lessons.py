"""Adding lessons

Revision ID: 528b6f1e9a69
Revises: a2348614116c
Create Date: 2025-01-14 11:59:51.022338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '528b6f1e9a69'
down_revision = 'a2348614116c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lesson',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('short_description', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lesson')
    # ### end Alembic commands ###
