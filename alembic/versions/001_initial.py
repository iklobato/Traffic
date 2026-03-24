"""Initial migration - create links and speed_records tables with PostGIS."""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("link_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("geometry", Geometry("MULTILINESTRING", srid=4326), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("link_id"),
    )
    op.create_index("ix_links_link_id", "links", ["link_id"])

    op.create_table(
        "speed_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=False),
        sa.Column("day_of_week", sa.String(), nullable=False),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["link_id"], ["links.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_speed_records_link_id", "speed_records", ["link_id"])
    op.create_index("ix_speed_records_timestamp", "speed_records", ["timestamp"])


def downgrade() -> None:
    op.drop_table("speed_records")
    op.drop_table("links")
