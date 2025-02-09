"""Add base users

Revision ID: b31a35e5d7f7
Revises: 8dfd2d2c61e4
Create Date: 2025-01-15 11:21:10.969098

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData

from werkzeug.security import generate_password_hash


# revision identifiers, used by Alembic.
revision = 'b31a35e5d7f7'
down_revision = '8dfd2d2c61e4'
branch_labels = None
depends_on = None

user_table = Table(
    'user',
    MetaData(),
    Column('id', Integer, primary_key=True),
    Column('login', String(100), unique=True),
    Column('name', String(255)),
    Column('author_id', Integer),
    Column('password_hash', String(255)),
    Column('role', String(100)),
    Column('verified', Boolean),
)

def upgrade():
    initial_users = [
        {
            'login': 'porduna',
            'name': 'Pablo Orduna',
            'role': 'admin',
            'verified': True,
            'password_hash': generate_password_hash('password'),
            'author_id': None
        },
        {
            'login': 'jonathan',
            'name': 'Jonathan Trinh',
            'role': 'admin',
            'verified': True,
            'password_hash': generate_password_hash('password'),
            'author_id': None
        },
        {
            'login': 'steven',
            'name': 'Steven Han',
            'role': 'admin',
            'verified': True,
            'password_hash': generate_password_hash('password'),
            'author_id': None
        }
    ]
    op.bulk_insert(user_table, initial_users)


def downgrade():
    pass
