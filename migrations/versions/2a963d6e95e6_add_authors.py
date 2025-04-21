"""Add authors

Revision ID: 2a963d6e95e6
Revises: e3e4fb2501a3
Create Date: 2025-04-21 12:00:20.380580

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, String, MetaData

# revision identifiers, used by Alembic.
revision = '2a963d6e95e6'
down_revision = 'e3e4fb2501a3'
branch_labels = None
depends_on = None


def upgrade():
    meta = MetaData()
    author_table = Table(
        'author',
        meta,
        Column('id', Integer, primary_key=True),
        Column('login', String(100), nullable=False, unique=True),
        Column('name', String(255), nullable=False),
        Column('link', String(255), nullable=False),
    )

    authors = [
        {'login': 'rhlab',      'name': 'RHLab (University of Washington)',      'link': 'https://rhlab.ece.uw.edu'},
        {'login': 'coltonharris','name': 'Colton Harris (RHLab, University of Washington)', 'link': 'https://rhlab.ece.uw.edu'},
        {'login': 'kevinkuo',    'name': 'Kevin Kuo (RHLab, University of Washington)',   'link': 'https://rhlab.ece.uw.edu'},
        {'login': 'mattguo',     'name': 'Matt Guo (RHLab, University of Washington)',    'link': 'https://rhlab.ece.uw.edu'},
        {'login': 'labsland',    'name': 'LabsLand',                                       'link': 'https://labsland.com'},
        {'login': 'deusto',      'name': 'WebLab-Deusto (University of Deusto)',           'link': 'https://weblab.deusto.es'},
        {'login': 'giovannalani','name': 'Giovanna Lani (WebLab-Deusto, University of Deusto)','link': 'https://weblab.deusto.es'},
    ]

    op.bulk_insert(author_table, authors)


def downgrade():
    meta = MetaData()
    author_table = Table('author', meta, autoload_with=op.get_bind())
    logins = [
        'rhlab',
        'coltonharris',
        'kevinkuo',
        'mattguo',
        'labsland',
        'deusto',
        'giovannalani',
    ]
    op.execute(
        author_table.delete().where(author_table.c.login.in_(logins))
    )
