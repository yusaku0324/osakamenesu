"""Add notification channels to profiles"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0010_add_notification_channels"
down_revision = "0009_add_users_and_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "notification_emails",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column("notification_line_token", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("notification_slack_webhook", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("profiles", "notification_slack_webhook")
    op.drop_column("profiles", "notification_line_token")
    op.drop_column("profiles", "notification_emails")
