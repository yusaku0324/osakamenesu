"""add therapists table for dashboard management

Revision ID: 0016_add_therapists
Revises: 0015_add_dashboard_users
Create Date: 2025-10-21 17:35:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0016_add_therapists"
down_revision = "0015_add_dashboard_users"
branch_labels = None
depends_on = None


therapist_status_enum = postgresql.ENUM(
    "draft",
    "published",
    "archived",
    name="therapist_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_enums = {enum["name"] for enum in inspector.get_enums(schema="public")}

    if "therapist_status" not in existing_enums:
        therapist_status_enum.create(bind, checkfirst=True)

    if not inspector.has_table("therapists"):
        op.create_table(
            "therapists",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "profile_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("profiles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("alias", sa.String(length=160), nullable=True),
            sa.Column("headline", sa.String(length=255), nullable=True),
            sa.Column("biography", sa.Text(), nullable=True),
            sa.Column("specialties", postgresql.ARRAY(sa.String(length=64)), nullable=True),
            sa.Column("qualifications", postgresql.ARRAY(sa.String(length=128)), nullable=True),
            sa.Column("experience_years", sa.Integer(), nullable=True),
            sa.Column("photo_urls", postgresql.ARRAY(sa.Text()), nullable=True),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", therapist_status_enum, nullable=False, server_default="draft"),
            sa.Column("is_booking_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        )
        op.create_index("ix_therapists_profile_id", "therapists", ["profile_id"], unique=False)
        op.create_index("ix_therapists_status", "therapists", ["status"], unique=False)
        op.create_index("ix_therapists_display_order", "therapists", ["display_order"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("therapists"):
        op.drop_index("ix_therapists_display_order", table_name="therapists")
        op.drop_index("ix_therapists_status", table_name="therapists")
        op.drop_index("ix_therapists_profile_id", table_name="therapists")
        op.drop_table("therapists")

    enums = inspector.get_enums(schema="public")
    enum_names = {enum["name"] for enum in enums}
    if "therapist_status" in enum_names:
        therapist_status_enum.drop(bind, checkfirst=True)
