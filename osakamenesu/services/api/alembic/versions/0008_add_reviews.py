"""Add reviews table

Revision ID: 0008_add_reviews
Revises: 0007_add_reservations
Create Date: 2025-09-21 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0008_add_reviews'
down_revision = '2b1da46b88f9'
branch_labels = None
depends_on = None


def _ensure_enum(name: str, *values: str) -> sa.Enum:
    values_sql = ", ".join(f"'{v}'" for v in values)
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                CREATE TYPE {name} AS ENUM ({values_sql});
              END IF;
            END
            $$;
            """
        )
    )
    return postgresql.ENUM(*values, name=name, create_type=False, _create_events=False)


def upgrade() -> None:
    review_status = _ensure_enum('review_status', 'pending', 'published', 'rejected')

    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', review_status, nullable=False, server_default='pending'),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=160)),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('author_alias', sa.String(length=80)),
        sa.Column('visited_at', sa.Date()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_reviews_profile_id_created_at', 'reviews', ['profile_id', 'created_at'])
    op.create_check_constraint('ck_reviews_score_range', 'reviews', 'score BETWEEN 1 AND 5')


def downgrade() -> None:
    op.drop_constraint('ck_reviews_score_range', 'reviews', type_='check')
    op.drop_index('ix_reviews_profile_id_created_at', table_name='reviews')
    op.drop_table('reviews')
    postgresql.ENUM(name='review_status').drop(op.get_bind(), checkfirst=True)
