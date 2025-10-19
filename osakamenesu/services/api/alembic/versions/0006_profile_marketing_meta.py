"""Add discounts and ranking metadata to profiles

Revision ID: 0006_profile_marketing_meta
Revises: 0005_add_admin_logs
Create Date: 2024-06-08 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0006_profile_marketing_meta'
down_revision = '0005_add_admin_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('profiles', sa.Column('discounts', postgresql.JSONB(), nullable=True))
    op.add_column('profiles', sa.Column('ranking_badges', postgresql.ARRAY(sa.String(length=32)), nullable=True))
    op.add_column('profiles', sa.Column('ranking_weight', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_profiles_ranking_weight'), 'profiles', ['ranking_weight'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_profiles_ranking_weight'), table_name='profiles')
    op.drop_column('profiles', 'ranking_weight')
    op.drop_column('profiles', 'ranking_badges')
    op.drop_column('profiles', 'discounts')
