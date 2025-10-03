"""add external ids for diaries and reviews

Revision ID: 0012_ext_ids_for_ingest
Revises: 0011_extend_notif_settings
Create Date: 2025-10-02 17:10:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0012_ext_ids_for_ingest"
down_revision = "0011_extend_notif_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "diaries",
        sa.Column("external_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_diaries_external_id",
        "diaries",
        ["external_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_diaries_profile_external",
        "diaries",
        ["profile_id", "external_id"],
    )

    op.add_column(
        "reviews",
        sa.Column("external_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_reviews_external_id",
        "reviews",
        ["external_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_reviews_profile_external",
        "reviews",
        ["profile_id", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_reviews_profile_external", "reviews", type_="unique")
    op.drop_index("ix_reviews_external_id", table_name="reviews")
    op.drop_column("reviews", "external_id")

    op.drop_constraint("uq_diaries_profile_external", "diaries", type_="unique")
    op.drop_index("ix_diaries_external_id", table_name="diaries")
    op.drop_column("diaries", "external_id")
