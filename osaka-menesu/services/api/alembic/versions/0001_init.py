from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0001_init'
down_revision = None
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
    return sa.Enum(*values, name=name, create_type=False)


def upgrade() -> None:
    # enums
    status_profile = _ensure_enum('status_profile', 'draft', 'published', 'hidden')
    status_diary = _ensure_enum('status_diary', 'mod', 'published', 'hidden')
    review_status = _ensure_enum('review_status', 'pending', 'published', 'rejected')
    outlink_kind = _ensure_enum('outlink_kind', 'line', 'tel', 'web')
    report_target = _ensure_enum('report_target', 'profile', 'diary')
    report_status = _ensure_enum('report_status', 'open', 'closed')
    # Note: bust_tag is stored as VARCHAR to avoid ENUM migration conflicts.
    # Historical environments may already have a conflicting ENUM type.

    bind = op.get_bind()

    inspector = sa.inspect(bind)

    if not inspector.has_table('profiles'):
        op.create_table(
            'profiles',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(length=160), nullable=False),
            sa.Column('area', sa.String(length=80), index=True),
            sa.Column('price_min', sa.Integer(), index=True),
            sa.Column('price_max', sa.Integer(), index=True),
            sa.Column('bust_tag', sa.String(length=16), index=True),
            sa.Column('body_tags', postgresql.ARRAY(sa.String(length=64))),
            sa.Column('photos', postgresql.ARRAY(sa.Text())),
            sa.Column('contact_json', postgresql.JSONB()),
            sa.Column('status', status_profile, index=True, server_default='draft'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if not inspector.has_table('diaries'):
        op.create_table(
            'diaries',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), index=True),
            sa.Column('title', sa.String(length=160)),
            sa.Column('text', sa.Text()),
            sa.Column('photos', postgresql.ARRAY(sa.Text())),
            sa.Column('hashtags', postgresql.ARRAY(sa.String(length=64))),
            sa.Column('status', status_diary, index=True, server_default='mod'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    if not inspector.has_table('reviews'):
        op.create_table(
            'reviews',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), index=True),
            sa.Column('status', review_status, nullable=False, index=True, server_default='pending'),
            sa.Column('score', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=160)),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('author_alias', sa.String(length=80)),
            sa.Column('visited_at', sa.Date()),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    if not inspector.has_table('availabilities'):
        op.create_table(
            'availabilities',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), index=True),
            sa.Column('date', sa.Date(), index=True),
            sa.Column('slots_json', postgresql.JSONB()),
            sa.Column('is_today', sa.Boolean(), server_default=sa.text('false'), index=True),
        )

    if not inspector.has_table('outlinks'):
        op.create_table(
            'outlinks',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), index=True),
            sa.Column('kind', outlink_kind, index=True),
            sa.Column('token', sa.String(length=64), unique=True, index=True),
            sa.Column('target_url', sa.Text()),
            sa.Column('utm', postgresql.JSONB()),
        )

    if not inspector.has_table('clicks'):
        op.create_table(
            'clicks',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('outlink_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outlinks.id', ondelete='CASCADE'), index=True),
            sa.Column('ts', sa.DateTime(timezone=True), index=True),
            sa.Column('referer', sa.Text()),
            sa.Column('ua', sa.Text()),
            sa.Column('ip_hash', sa.String(length=128), index=True),
        )

    if not inspector.has_table('consents'):
        op.create_table(
            'consents',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), index=True),
            sa.Column('doc_version', sa.String(length=40)),
            sa.Column('agreed_at', sa.DateTime(timezone=True)),
            sa.Column('ip', sa.String(length=64)),
            sa.Column('user_agent', sa.Text()),
        )

    if not inspector.has_table('reports'):
        op.create_table(
            'reports',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('target_type', report_target, index=True),
            sa.Column('target_id', postgresql.UUID(as_uuid=True), index=True),
            sa.Column('reason', sa.String(length=80)),
            sa.Column('note', sa.Text()),
            sa.Column('status', report_status, index=True, server_default='open'),
            sa.Column('created_at', sa.DateTime(timezone=True)),
        )


def downgrade() -> None:
    for t in ['reports','consents','clicks','outlinks','availabilities','reviews','diaries','profiles']:
        op.drop_table(t)
    for e in ['report_status','report_target','outlink_kind','review_status','status_diary','status_profile','bust_tag']:
        sa.Enum(name=e).drop(op.get_bind(), checkfirst=True)
