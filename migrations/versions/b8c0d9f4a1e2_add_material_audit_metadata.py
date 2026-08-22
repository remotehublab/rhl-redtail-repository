"""Add material audit metadata

Revision ID: b8c0d9f4a1e2
Revises: e424ea02d723
Create Date: 2026-08-22 16:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "b8c0d9f4a1e2"
down_revision = "e424ea02d723"
branch_labels = None
depends_on = None


MATERIAL_TABLES = {
    "laboratory_exercise_doc": {
        "legacy_timestamp": "last_updated",
        "uploaded_fk": "fk_lab_exercise_doc_uploaded_user",
        "updated_fk": "fk_lab_exercise_doc_updated_user",
    },
    "simulation_doc": {
        "legacy_timestamp": "last_updated",
        "uploaded_fk": "fk_simulation_doc_uploaded_user",
        "updated_fk": "fk_simulation_doc_updated_user",
    },
    "device_doc": {
        "legacy_timestamp": "last_updated",
        "uploaded_fk": "fk_device_doc_uploaded_user",
        "updated_fk": "fk_device_doc_updated_user",
    },
    "simulation_device_document": {
        "legacy_timestamp": None,
        "uploaded_fk": "fk_sim_device_doc_uploaded_user",
        "updated_fk": "fk_sim_device_doc_updated_user",
    },
}


def upgrade():
    for table_name, settings in MATERIAL_TABLES.items():
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
            batch_op.add_column(
                sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True)
            )
            batch_op.add_column(
                sa.Column("updated_by_user_id", sa.Integer(), nullable=True)
            )
            batch_op.create_foreign_key(
                settings["uploaded_fk"],
                "user",
                ["uploaded_by_user_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_foreign_key(
                settings["updated_fk"],
                "user",
                ["updated_by_user_id"],
                ["id"],
                ondelete="SET NULL",
            )

    connection = op.get_bind()
    metadata = sa.MetaData()
    for table_name, settings in MATERIAL_TABLES.items():
        table = sa.Table(table_name, metadata, autoload_with=connection)
        legacy_name = settings["legacy_timestamp"]
        timestamp = (
            sa.func.coalesce(table.c[legacy_name], sa.func.now())
            if legacy_name
            else sa.func.now()
        )
        connection.execute(
            table.update().values(created_at=timestamp, updated_at=timestamp)
        )

    for table_name in MATERIAL_TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
            batch_op.alter_column(
                "updated_at",
                existing_type=sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )


def downgrade():
    for table_name, settings in reversed(MATERIAL_TABLES.items()):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(settings["updated_fk"], type_="foreignkey")
            batch_op.drop_constraint(settings["uploaded_fk"], type_="foreignkey")
            batch_op.drop_column("updated_by_user_id")
            batch_op.drop_column("uploaded_by_user_id")
            batch_op.drop_column("updated_at")
            batch_op.drop_column("created_at")
