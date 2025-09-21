"""Add reservations tables

Revision ID: 0007_add_reservations
Revises: 0006_profile_marketing_meta
Create Date: 2024-06-08 00:15:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0007_add_reservations'
down_revision = '0006_profile_marketing_meta'
branch_labels = None
depends_on = None


def upgrade() -> None:
    reservation_status_type = postgresql.ENUM(
        'pending', 'confirmed', 'declined', 'cancelled', 'expired',
        name='reservation_status'
    )

    bind = op.get_bind()
    reservation_status_type.create(bind, checkfirst=True)

    reservation_status = postgresql.ENUM(
        'pending', 'confirmed', 'declined', 'cancelled', 'expired',
        name='reservation_status',
        create_type=False,
    )

    op.create_table(
        'reservations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('shop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('menu_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('channel', sa.String(length=32), nullable=True),
        sa.Column('desired_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('desired_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', reservation_status, nullable=False),
        sa.Column('marketing_opt_in', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('customer_name', sa.String(length=120), nullable=False),
        sa.Column('customer_phone', sa.String(length=40), nullable=False),
        sa.Column('customer_email', sa.String(length=160), nullable=True),
        sa.Column('customer_line_id', sa.String(length=80), nullable=True),
        sa.Column('customer_remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index(op.f('ix_reservations_shop_id'), 'reservations', ['shop_id'], unique=False)
    op.create_index(op.f('ix_reservations_staff_id'), 'reservations', ['staff_id'], unique=False)
    op.create_index(op.f('ix_reservations_menu_id'), 'reservations', ['menu_id'], unique=False)
    op.create_index(op.f('ix_reservations_channel'), 'reservations', ['channel'], unique=False)
    op.create_index(op.f('ix_reservations_desired_start'), 'reservations', ['desired_start'], unique=False)
    op.create_index(op.f('ix_reservations_desired_end'), 'reservations', ['desired_end'], unique=False)
    op.create_index(op.f('ix_reservations_status'), 'reservations', ['status'], unique=False)

    op.create_table(
        'reservation_status_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', reservation_status, nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('changed_by', sa.String(length=64), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
    )
    op.create_index(op.f('ix_reservation_status_events_reservation_id'), 'reservation_status_events', ['reservation_id'], unique=False)
    op.create_index(op.f('ix_reservation_status_events_status'), 'reservation_status_events', ['status'], unique=False)
    op.create_index(op.f('ix_reservation_status_events_changed_at'), 'reservation_status_events', ['changed_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reservation_status_events_changed_at'), table_name='reservation_status_events')
    op.drop_index(op.f('ix_reservation_status_events_status'), table_name='reservation_status_events')
    op.drop_index(op.f('ix_reservation_status_events_reservation_id'), table_name='reservation_status_events')
    op.drop_table('reservation_status_events')

    op.drop_index(op.f('ix_reservations_status'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_desired_end'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_desired_start'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_channel'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_menu_id'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_staff_id'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_shop_id'), table_name='reservations')
    op.drop_table('reservations')

    reservation_status = postgresql.ENUM(name='reservation_status')
    reservation_status.drop(op.get_bind(), checkfirst=True)
