"""Create daily_link_speeds materialized view for fast slow_links queries.

This materialized view pre-aggregates speed data by link and day_of_week,
allowing fast queries on slow links without scanning millions of records.
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS daily_link_speeds AS
        SELECT 
            l.id as link_id,
            l.link_id as link_id_str,
            l.name,
            sr.day_of_week,
            AVG(sr.speed) as avg_speed,
            COUNT(*) as record_count,
            COUNT(DISTINCT sr.hour) as hours_covered
        FROM links l
        JOIN speed_records sr ON l.id = sr.link_id
        GROUP BY l.id, l.link_id, l.name, sr.day_of_week
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dls_link_day 
        ON daily_link_speeds(link_id_str, day_of_week)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dls_avg_speed 
        ON daily_link_speeds(avg_speed)
        """
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_link_speeds")
