"""Add user accounts, auth tokens, sessions, favorites"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_add_users_and_sessions"
down_revision = "0008_add_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_auth_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_user_auth_tokens_user_id", "user_auth_tokens", ["user_id"])
    op.create_index("ix_user_auth_tokens_expires_at", "user_auth_tokens", ["expires_at"])

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])

    op.create_table(
        "user_favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "shop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "shop_id", name="uq_user_favorites_user_shop"),
    )
    op.create_index("ix_user_favorites_user_id", "user_favorites", ["user_id"])
    op.create_index("ix_user_favorites_shop_id", "user_favorites", ["shop_id"])

    op.add_column(
        "reservations",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_reservations_user_id", "reservations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_reservations_user_id", table_name="reservations")
    with op.batch_alter_table("reservations") as batch_op:
        batch_op.drop_constraint("reservations_user_id_fkey", type_="foreignkey")
        batch_op.drop_column("user_id")

    op.drop_index("ix_user_favorites_shop_id", table_name="user_favorites")
    op.drop_index("ix_user_favorites_user_id", table_name="user_favorites")
    op.drop_table("user_favorites")
    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_user_auth_tokens_expires_at", table_name="user_auth_tokens")
    op.drop_index("ix_user_auth_tokens_user_id", table_name="user_auth_tokens")
    op.drop_table("user_auth_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
