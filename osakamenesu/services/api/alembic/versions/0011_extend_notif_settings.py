"""extend dashboard notification channels JSON"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_extend_notif_settings"
down_revision = "0010_add_notification_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "notification_trigger_status",
            postgresql.ARRAY(sa.String(length=32)),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "notification_channels_enabled",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("profiles", "notification_channels_enabled")
    op.drop_column("profiles", "notification_trigger_status")
