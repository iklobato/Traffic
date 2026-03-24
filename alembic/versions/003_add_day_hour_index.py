"""Add composite index on day_of_week and hour for query performance.

This index significantly improves query performance for all endpoints
that filter by day_of_week and hour range (get_aggregates, get_link_detail,
get_slow_links, get_spatial_filter).
"""

from alembic import op

revision = "003"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_speed_records_day_hour",
        "speed_records",
        ["day_of_week", "hour"],
    )


def downgrade() -> None:
    op.drop_index("ix_speed_records_day_hour", table_name="speed_records")
