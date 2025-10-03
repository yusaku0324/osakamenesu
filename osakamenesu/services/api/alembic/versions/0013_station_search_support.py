"""add station metadata for search

Revision ID: 0013_station_search_support
Revises: 0012_ext_ids_for_ingest
Create Date: 2025-10-03 23:10:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0013_station_search_support"
down_revision = "0012_ext_ids_for_ingest"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("nearest_station", sa.String(length=80), nullable=True))
    op.add_column("profiles", sa.Column("station_line", sa.String(length=80), nullable=True))
    op.add_column("profiles", sa.Column("station_exit", sa.String(length=32), nullable=True))
    op.add_column("profiles", sa.Column("station_walk_minutes", sa.Integer(), nullable=True))
    op.add_column("profiles", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("profiles", sa.Column("longitude", sa.Float(), nullable=True))
    op.create_index("ix_profiles_nearest_station", "profiles", ["nearest_station"])
    op.create_index("ix_profiles_station_line", "profiles", ["station_line"])


def downgrade() -> None:
    op.drop_index("ix_profiles_station_line", table_name="profiles")
    op.drop_index("ix_profiles_nearest_station", table_name="profiles")
    op.drop_column("profiles", "longitude")
    op.drop_column("profiles", "latitude")
    op.drop_column("profiles", "station_walk_minutes")
    op.drop_column("profiles", "station_exit")
    op.drop_column("profiles", "station_line")
    op.drop_column("profiles", "nearest_station")
