"""add admin change log

Revision ID: 2b1da46b88f9
Revises: 0007_add_reservations
Create Date: 2025-09-20 18:52:34.288622
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '2b1da46b88f9'
down_revision = '0007_add_reservations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    has_table = inspector.has_table('admin_change_logs')
    if not has_table:
        op.create_table(
            'admin_change_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,),
            sa.Column('ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('target_type', sa.String(length=64), nullable=False),
            sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('action', sa.String(length=32), nullable=False),
            sa.Column('before_json', postgresql.JSONB(), nullable=True),
            sa.Column('after_json', postgresql.JSONB(), nullable=True),
            sa.Column('admin_key_hash', sa.String(length=128), nullable=True),
            sa.Column('ip_hash', sa.String(length=128), nullable=True),
        )

    existing_indexes = {ix['name'] for ix in inspector.get_indexes('admin_change_logs')} if has_table else set()

    if 'ix_admin_change_logs_ts' not in existing_indexes:
        op.create_index('ix_admin_change_logs_ts', 'admin_change_logs', ['ts'], unique=False)
    if 'ix_admin_change_logs_target_type' not in existing_indexes:
        op.create_index('ix_admin_change_logs_target_type', 'admin_change_logs', ['target_type'], unique=False)
    if 'ix_admin_change_logs_target_id' not in existing_indexes:
        op.create_index('ix_admin_change_logs_target_id', 'admin_change_logs', ['target_id'], unique=False)
    if 'ix_admin_change_logs_admin_key_hash' not in existing_indexes:
        op.create_index('ix_admin_change_logs_admin_key_hash', 'admin_change_logs', ['admin_key_hash'], unique=False)
    if 'ix_admin_change_logs_ip_hash' not in existing_indexes:
        op.create_index('ix_admin_change_logs_ip_hash', 'admin_change_logs', ['ip_hash'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('admin_change_logs'):
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('admin_change_logs')}
        if 'ix_admin_change_logs_ip_hash' in existing_indexes:
            op.drop_index('ix_admin_change_logs_ip_hash', table_name='admin_change_logs')
        if 'ix_admin_change_logs_admin_key_hash' in existing_indexes:
            op.drop_index('ix_admin_change_logs_admin_key_hash', table_name='admin_change_logs')
        if 'ix_admin_change_logs_target_id' in existing_indexes:
            op.drop_index('ix_admin_change_logs_target_id', table_name='admin_change_logs')
        if 'ix_admin_change_logs_target_type' in existing_indexes:
            op.drop_index('ix_admin_change_logs_target_type', table_name='admin_change_logs')
        if 'ix_admin_change_logs_ts' in existing_indexes:
            op.drop_index('ix_admin_change_logs_ts', table_name='admin_change_logs')
        op.drop_table('admin_change_logs')
