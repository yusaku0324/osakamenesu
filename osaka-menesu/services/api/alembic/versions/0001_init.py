from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # enums
    status_profile = sa.Enum('draft', 'published', 'hidden', name='status_profile')
    status_diary = sa.Enum('mod', 'published', 'hidden', name='status_diary')
    outlink_kind = sa.Enum('line', 'tel', 'web', name='outlink_kind')
    report_target = sa.Enum('profile', 'diary', name='report_target')
    report_status = sa.Enum('open', 'closed', name='report_status')
    # Note: bust_tag is stored as VARCHAR to avoid ENUM migration conflicts.
    # Historical environments may already have a conflicting ENUM type.

    bind = op.get_bind()
    status_profile.create(bind, checkfirst=True)
    status_diary.create(bind, checkfirst=True)
    outlink_kind.create(bind, checkfirst=True)
    report_target.create(bind, checkfirst=True)
    report_status.create(bind, checkfirst=True)
    # Do not create bust_tag ENUM here; we use VARCHAR column for bust_tag.

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
    for t in ['reports','consents','clicks','outlinks','availabilities','diaries','profiles']:
        op.drop_table(t)
    for e in ['report_status','report_target','outlink_kind','status_diary','status_profile','bust_tag']:
        sa.Enum(name=e).drop(op.get_bind(), checkfirst=True)
