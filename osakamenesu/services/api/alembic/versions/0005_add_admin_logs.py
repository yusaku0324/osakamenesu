from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0005_add_admin_logs'
down_revision = '0004_unify_bust_tag_to_varchar'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('admin_logs'):
        op.create_table(
            'admin_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('ts', sa.DateTime(timezone=True), index=True),
            sa.Column('method', sa.String(length=8)),
            sa.Column('path', sa.String(length=200), index=True),
            sa.Column('ip_hash', sa.String(length=128), index=True),
            sa.Column('admin_key_hash', sa.String(length=128)),
            sa.Column('details', postgresql.JSONB()),
        )


def downgrade() -> None:
    op.drop_table('admin_logs')

