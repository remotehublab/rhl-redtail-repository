"""Start adding example simulations

Revision ID: df02d6e62a01
Revises: d9791af79990
Create Date: 2025-04-21 15:06:19.543202

"""
import datetime
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Table, MetaData

# revision identifiers, used by Alembic.
revision = 'df02d6e62a01'
down_revision = 'd9791af79990'
branch_labels = None
depends_on = None



def upgrade():
    conn = op.get_bind()
    meta = MetaData()

    # Reflect tables
    simulation_table        = Table('simulation', meta, autoload_with=conn)
    author_table            = Table('author', meta, autoload_with=conn)
    author_sim_assoc        = Table('author_simulation', meta, autoload_with=conn)
    device_table            = Table('device', meta, autoload_with=conn)
    device_sim_assoc        = Table('device_simulation', meta, autoload_with=conn)
    framework_table         = Table('device_framework', meta, autoload_with=conn)
    sim_framework_assoc     = Table('simulation_framework_association', meta, autoload_with=conn)
    sim_cat_assoc           = Table('simulation_category_association', meta, autoload_with=conn)
    sim_category_table      = Table('simulation_category', meta, autoload_with=conn)

    # Pre-fetch IDs
    all_device_ids = [row.id for row in conn.execute(sa.select(device_table.c.id)).all()]
    all_framework_ids = [row.id for row in conn.execute(sa.select(framework_table.c.id)).all()]

    fpga_id = conn.execute(
        sa.select(device_table.c.id).where(device_table.c.slug == 'fpga-de1-soc')
    ).scalar_one()
    fpga_framework_ids = [
        row.id for row in conn.execute(
            sa.select(framework_table.c.id).where(framework_table.c.device_id == fpga_id)
        ).all()
    ]

    sim_cat_id  = conn.execute(
        sa.select(sim_category_table.c.id).where(sim_category_table.c.slug == 'simulation')
    ).scalar_one()
    real_cat_id = conn.execute(
        sa.select(sim_category_table.c.id).where(sim_category_table.c.slug == 'real-world')
    ).scalar_one()
    dt_cat_id   = conn.execute(
        sa.select(sim_category_table.c.id).where(sim_category_table.c.slug == 'digital-twin')
    ).scalar_one()

    # Define simulations to insert
    simulations = [
        {
            'name': 'Parking Lot',
            'slug': 'parking-lot',
            'description': 'Manage a parking lot: entrance and exit barriers, LEDs for car presence.',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/parking-lot.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
            'author_logins': ['labsland', 'rhlab'],
            'device_ids': all_device_ids,
            'framework_ids': all_framework_ids,
            'category_ids': [sim_cat_id, real_cat_id],
        },
        {
            'name': 'KeyPad',
            'slug': 'keypad',
            'description': 'Manage a Parallax 4x4 Matrix Membrane Keypad',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/keypad.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
            'author_logins': ['labsland'],
            'device_ids': all_device_ids,
            'framework_ids': all_framework_ids,
            'category_ids': [sim_cat_id, dt_cat_id],
        },
        {
            'name': 'Breadboard (Butterfly)',
            'slug': 'butterfly',
            'description': 'Connect logic gates in a breadboard',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/butterfly.jpg',
            'last_updated': datetime.datetime(2023, 6, 30),
            'author_logins': ['rhlab', 'mattguo'],
            'device_ids': [fpga_id],
            'framework_ids': fpga_framework_ids,
            'category_ids': [sim_cat_id, dt_cat_id],
        },
        {
            'name': 'NES Controller',
            'slug': 'nes-controller',
            'description': 'Use a NES controller with its serial protocol',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/n8.jpg',
            'last_updated': datetime.datetime(2023, 6, 30),
            'author_logins': ['labsland'],
            'device_ids': all_device_ids,
            'framework_ids': fpga_framework_ids,
            'category_ids': [sim_cat_id, dt_cat_id],
        },
        {
            'name': 'Joystick',
            'slug': 'joystick',
            'description': 'Use a Joystick with a serial communication',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/joystick.jpg',
            'last_updated': datetime.datetime(2023, 6, 30),
            'author_logins': ['labsland'],
            'device_ids': all_device_ids,
            'framework_ids': fpga_framework_ids,
            'category_ids': [sim_cat_id],
        },
        {
            'name': 'Door',
            'slug': 'door',
            'description': 'Manage a school door with a presence sensor',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/door.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
            'author_logins': ['deusto', 'giovannalani'],
            'device_ids': all_device_ids,
            'framework_ids': all_framework_ids,
            'category_ids': [sim_cat_id, real_cat_id],
        },
        {
            'name': 'Water tank',
            'slug': 'watertank',
            'description': 'Manage a water tank with two pumps and a variable amount of water demand',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/watertankDeusto.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
            'author_logins': ['deusto', 'giovannalani'],
            'device_ids': all_device_ids,
            'framework_ids': all_framework_ids,
            'category_ids': [sim_cat_id, real_cat_id],
        },
        {
            'name': 'LED Matrix',
            'slug': 'ledmatrix',
            'description': 'Send through a serial communication information to a 16x16 LED Matrix',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/led-matrix.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
            'author_logins': ['rhlab', 'coltonharris'],
            'device_ids': all_device_ids,
            'framework_ids': all_framework_ids,
            'category_ids': [sim_cat_id, real_cat_id],
        },
        {
            'name': 'Morse code',
            'slug': 'morse',
            'description': 'Send a message using Morse code',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/simulations/morse.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
            'author_logins': ['rhlab', 'kevinkuo'],
            'device_ids': all_device_ids,
            'framework_ids': all_framework_ids,
            'category_ids': [sim_cat_id],
        },
    ]

    for sim in simulations:
        # Insert simulation record
        conn.execute(
            simulation_table.insert().values(
                name=sim['name'],
                slug=sim['slug'],
                description=sim['description'],
                cover_image_url=sim['cover_image_url'],
                last_updated=sim['last_updated']
            )
        )
        sim_id = conn.execute(
            sa.select(simulation_table.c.id).where(simulation_table.c.slug == sim['slug'])
        ).scalar_one()

        # Associate authors
        for login in sim['author_logins']:
            author_id = conn.execute(
                sa.select(author_table.c.id).where(author_table.c.login == login)
            ).scalar_one()
            conn.execute(
                author_sim_assoc.insert().values(
                    author_id=author_id,
                    simulation_id=sim_id
                )
            )

        # Associate devices
        for did in sim['device_ids']:
            conn.execute(
                device_sim_assoc.insert().values(
                    device_id=did,
                    simulation_id=sim_id
                )
            )

        # Associate frameworks
        for fid in sim['framework_ids']:
            conn.execute(
                sim_framework_assoc.insert().values(
                    simulation_id=sim_id,
                    framework_id=fid
                )
            )

        # Associate categories
        for cid in sim['category_ids']:
            conn.execute(
                sim_cat_assoc.insert().values(
                    simulation_id=sim_id,
                    category_id=cid
                )
            )


def downgrade():
    conn = op.get_bind()
    meta = MetaData()

    simulation_table    = Table('simulation', meta, autoload_with=conn)
    author_sim_assoc    = Table('author_simulation', meta, autoload_with=conn)
    device_sim_assoc    = Table('device_simulation', meta, autoload_with=conn)
    sim_framework_assoc = Table('simulation_framework_association', meta, autoload_with=conn)
    sim_cat_assoc       = Table('simulation_category_association', meta, autoload_with=conn)

    slugs = [
        'parking-lot', 'keypad', 'butterfly', 'nes-controller',
        'joystick', 'door', 'watertank', 'ledmatrix', 'morse'
    ]

    for slug in slugs:
        sim_id = conn.execute(
            sa.select(simulation_table.c.id).where(simulation_table.c.slug == slug)
        ).scalar_one_or_none()
        if not sim_id:
            continue

        # Delete associations first
        conn.execute(author_sim_assoc.delete().where(author_sim_assoc.c.simulation_id == sim_id))
        conn.execute(device_sim_assoc.delete().where(device_sim_assoc.c.simulation_id == sim_id))
        conn.execute(sim_framework_assoc.delete().where(sim_framework_assoc.c.simulation_id == sim_id))
        conn.execute(sim_cat_assoc.delete().where(sim_cat_assoc.c.simulation_id == sim_id))

        # Delete the simulation
        conn.execute(simulation_table.delete().where(simulation_table.c.id == sim_id))
