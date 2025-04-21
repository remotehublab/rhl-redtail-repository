"""add example data - devices

Revision ID: d9791af79990
Revises: 2a963d6e95e6
Create Date: 2025-04-21 13:12:46.479101

"""
import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Table, MetaData

# revision identifiers, used by Alembic.
revision = 'd9791af79990'
down_revision = '2a963d6e95e6'
branch_labels = None
depends_on = None



def upgrade():
    conn = op.get_bind()
    meta = MetaData()

    # Reflect the tables we need
    device_table               = Table('device', meta, autoload_with=conn)
    category_table             = Table('device_category', meta, autoload_with=conn)
    device_category_assoc      = Table('device_category_association', meta, autoload_with=conn)
    framework_table            = Table('device_framework', meta, autoload_with=conn)
    device_doc_table           = Table('device_doc', meta, autoload_with=conn)

    # 1) Insert Devices
    devices = [
        {
            'slug': 'fpga-de1-soc',
            'name': 'Altera DE1-SoC',
            'description': 'Remote laboratory for Terasic DE1-SoC Altera with a Cyclone V FPGA.',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/devices/fpga-de1-soc.jpg',
            'last_updated': datetime.datetime(2025, 1, 1),
        },
        {
            'slug': 'stm32-nucleo-wb55rg',
            'name': 'STM32 Nucleo WB55RG',
            'description': 'Remote laboratory for the STM32 Nucleo WB55RG board',
            'cover_image_url': 'https://redtail.rhlab.ece.uw.edu/public/images/devices/stm32-nucleo-wb55rg.png',
            'last_updated': datetime.datetime(2025, 1, 1),
        },
    ]
    for d in devices:
        conn.execute(device_table.insert().values(**d))

    # Fetch their IDs
    fpga_id = conn.execute(
        sa.select(device_table.c.id).where(device_table.c.slug == 'fpga-de1-soc')
    ).scalar_one()
    stm_id  = conn.execute(
        sa.select(device_table.c.id).where(device_table.c.slug == 'stm32-nucleo-wb55rg')
    ).scalar_one()

    # 2) Link to categories
    fpga_cat_id = conn.execute(
        sa.select(category_table.c.id).where(category_table.c.slug == 'fpga')
    ).scalar_one()
    conn.execute(device_category_assoc.insert().values(
        device_id=fpga_id,
        device_category_id=fpga_cat_id
    ))

    arm_cat_id = conn.execute(
        sa.select(category_table.c.id).where(category_table.c.slug == 'arm')
    ).scalar_one()
    mcu_cat_id = conn.execute(
        sa.select(category_table.c.id).where(category_table.c.slug == 'microcontroller')
    ).scalar_one()
    conn.execute(device_category_assoc.insert().values(
        device_id=stm_id,
        device_category_id=arm_cat_id
    ))
    conn.execute(device_category_assoc.insert().values(
        device_id=stm_id,
        device_category_id=mcu_cat_id
    ))

    # 3) Add Device Frameworks for FPGA
    fpga_frameworks = [
        ('VHDL',                'fpga-de1-soc-vhdl'),
        ('Verilog',             'fpga-de1-soc-verilog'),
        ('SystemVerilog',       'fpga-de1-soc-system-verilog'),
    ]
    for name, slug in fpga_frameworks:
        conn.execute(framework_table.insert().values(
            name=name,
            slug=slug,
            last_updated=datetime.datetime(2025, 1, 1),
            device_id=fpga_id
        ))

    # 4) Add Device Frameworks for STM32
    stm_frameworks = [
        ('STM32CubeMX',                                'stm32-nucleo-wb55rg-stm32cubemx'),
        ('mbedOS',                                     'stm32-nucleo-wb55rg-mbedos'),
        ('Online IDE (STM32CubeMX)',                   'stm32-nucleo-wb55rg-stm32cubemx-online'),
    ]
    for name, slug in stm_frameworks:
        conn.execute(framework_table.insert().values(
            name=name,
            slug=slug,
            last_updated=datetime.datetime(2025, 1, 1),
            device_id=stm_id
        ))

    # 5) Add Device Docs
    device_docs = [
        {
            'device_id': fpga_id,
            'doc_url':   'https://labsland.com/en/labs/fpga-de1-soc',
            'title':     'Website for the DE1-SoC remote lab',
            'description': 'LabsLand website including documentation',
            'last_updated': datetime.datetime(2025, 1, 1),
        },
        {
            'device_id': stm_id,
            'doc_url':   'https://labsland.com/en/labs/stm32-nucleo-c',
            'title':     'Website for the Nucleo WB55RG remote lab (using an online editor based that relies on STM32CubeMX)',
            'description': 'LabsLand website including documentation',
            'last_updated': datetime.datetime(2025, 1, 1),
        },
        {
            'device_id': stm_id,
            'doc_url':   'https://labsland.com/en/labs/stm32-nucleo-direct',
            'title':     'Website for the Nucleo WB55RG remote lab (using uploading binary)',
            'description': 'LabsLand website including documentation',
            'last_updated': datetime.datetime(2025, 1, 1),
        },
    ]
    for doc in device_docs:
        conn.execute(device_doc_table.insert().values(**doc))


def downgrade():
    conn = op.get_bind()
    meta = MetaData()

    device_doc_table      = Table('device_doc', meta, autoload_with=conn)
    framework_table       = Table('device_framework', meta, autoload_with=conn)
    device_category_assoc = Table('device_category_association', meta, autoload_with=conn)
    device_table          = Table('device', meta, autoload_with=conn)
    category_table        = Table('device_category', meta, autoload_with=conn)

    # 1) Remove docs
    for url in (
        'https://labsland.com/en/labs/fpga-de1-soc',
        'https://labsland.com/en/labs/stm32-nucleo-c',
        'https://labsland.com/en/labs/stm32-nucleo-direct',
    ):
        conn.execute(
            device_doc_table.delete().where(device_doc_table.c.doc_url == url)
        )

    # 2) Remove frameworks
    for slug in (
        'fpga-de1-soc-vhdl',
        'fpga-de1-soc-verilog',
        'fpga-de1-soc-system-verilog',
        'stm32-nucleo-wb55rg-stm32cubemx',
        'stm32-nucleo-wb55rg-mbedos',
        'stm32-nucleo-wb55rg-stm32cubemx-online',
    ):
        conn.execute(
            framework_table.delete().where(framework_table.c.slug == slug)
        )

    # 3) Remove category links
    for device_slug, cat_slugs in (
        ('fpga-de1-soc',       ['fpga']),
        ('stm32-nucleo-wb55rg',['arm', 'microcontroller']),
    ):
        dev_id = conn.execute(
            sa.select(device_table.c.id).where(device_table.c.slug == device_slug)
        ).scalar_one()
        for cs in cat_slugs:
            cat_id = conn.execute(
                sa.select(category_table.c.id).where(category_table.c.slug == cs)
            ).scalar_one()
            conn.execute(
                device_category_assoc.delete().where(
                    sa.and_(
                        device_category_assoc.c.device_id == dev_id,
                        device_category_assoc.c.device_category_id == cat_id
                    )
                )
            )

    # 4) Delete devices
    for slug in ('fpga-de1-soc', 'stm32-nucleo-wb55rg'):
        conn.execute(
            device_table.delete().where(device_table.c.slug == slug)
        )
