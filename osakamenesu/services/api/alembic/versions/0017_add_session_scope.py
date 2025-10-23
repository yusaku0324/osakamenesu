"""add scope column to auth tokens and sessions

Revision ID: 0017_add_session_scope
Revises: 0016_add_therapists
Create Date: 2025-10-23 10:12:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0017_add_session_scope"
down_revision = "0016_add_therapists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_auth_tokens",
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="dashboard"),
    )
    op.add_column(
        "user_sessions",
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="dashboard"),
    )

    op.alter_column("user_auth_tokens", "scope", server_default=None)
    op.alter_column("user_sessions", "scope", server_default=None)


def downgrade() -> None:
    op.drop_column("user_sessions", "scope")
    op.drop_column("user_auth_tokens", "scope")
