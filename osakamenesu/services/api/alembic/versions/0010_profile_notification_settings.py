"""Add per-profile notification settings columns

Revision ID: 0010_profile_notification_settings
Revises: 0009_add_users_and_sessions
Create Date: 2025-09-26 07:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0010_profile_notification_settings"
down_revision = "0009_add_users_and_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "notify_email_recipients",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=True,
            server_default=sa.text("'{}'::text[]"),
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "notify_line_token",
            sa.String(length=128),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "notify_slack_webhook",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "notify_trigger_status",
            postgresql.ARRAY(sa.String(length=32)),
            nullable=True,
            server_default=sa.text("'{}'::text[]"),
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "notify_channels_enabled",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    # Ensure existing rows receive empty arrays/json objects rather than NULL for new columns
    op.execute(
        """
        UPDATE profiles
        SET
            notify_email_recipients = COALESCE(notify_email_recipients, ARRAY[]::text[]),
            notify_trigger_status = COALESCE(notify_trigger_status, ARRAY[]::text[]),
            notify_channels_enabled = COALESCE(notify_channels_enabled, '{}'::jsonb)
        """
    )


def downgrade() -> None:
    op.drop_column("profiles", "notify_channels_enabled")
    op.drop_column("profiles", "notify_trigger_status")
    op.drop_column("profiles", "notify_slack_webhook")
    op.drop_column("profiles", "notify_line_token")
    op.drop_column("profiles", "notify_email_recipients")
