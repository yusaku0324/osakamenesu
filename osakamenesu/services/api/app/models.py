from __future__ import annotations

from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, Enum, DateTime, ForeignKey, Date, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
from datetime import datetime, date, UTC
from typing import Any


Base = declarative_base()


StatusProfile = Enum('draft', 'published', 'hidden', name='status_profile')
StatusDiary = Enum('mod', 'published', 'hidden', name='status_diary')
OutlinkKind = Enum('line', 'tel', 'web', name='outlink_kind')
ReportTarget = Enum('profile', 'diary', name='report_target')
ReportStatus = Enum('open', 'closed', name='report_status')
ReviewStatus = Enum('pending', 'published', 'rejected', name='review_status')
# bust_tag はマイグレーション互換性のため VARCHAR で運用
ServiceType = Enum('store', 'dispatch', name='service_type')
ReservationStatus = Enum('pending', 'confirmed', 'declined', 'cancelled', 'expired', name='reservation_status')


def now_utc() -> datetime:
    return datetime.now(UTC)


class Profile(Base):
    __tablename__ = 'profiles'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    area: Mapped[str] = mapped_column(String(80), index=True)
    price_min: Mapped[int] = mapped_column(Integer, index=True)
    price_max: Mapped[int] = mapped_column(Integer, index=True)
    bust_tag: Mapped[str] = mapped_column(String(16), index=True)
    service_type: Mapped[str] = mapped_column(ServiceType, default='store', index=True)
    # Optional stats
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)))
    photos: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    contact_json: Mapped[dict | None] = mapped_column(JSONB)
    discounts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    ranking_badges: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)))
    ranking_weight: Mapped[int | None] = mapped_column(Integer, index=True)
    notify_email_recipients: Mapped[list[str] | None] = mapped_column(ARRAY(String(255)), nullable=True)
    notify_line_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notify_slack_webhook: Mapped[str | None] = mapped_column(Text, nullable=True)
    notify_trigger_status: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)), nullable=True)
    notify_channels_enabled: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(StatusProfile, default='draft', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    diaries: Mapped[list["Diary"]] = relationship(back_populates='profile', cascade='all,delete-orphan')
    reviews: Mapped[list["Review"]] = relationship(back_populates='profile', cascade='all, delete-orphan')
    favorites: Mapped[list[UserFavorite]] = relationship(back_populates='profile', cascade='all, delete-orphan')


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    auth_tokens: Mapped[list[UserAuthToken]] = relationship(back_populates='user', cascade='all, delete-orphan')
    sessions: Mapped[list[UserSession]] = relationship(back_populates='user', cascade='all, delete-orphan')
    favorites: Mapped[list[UserFavorite]] = relationship(back_populates='user', cascade='all, delete-orphan')
    reservations: Mapped[list[Reservation]] = relationship(back_populates='user')


class UserAuthToken(Base):
    __tablename__ = 'user_auth_tokens'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    user: Mapped[User] = relationship(back_populates='auth_tokens')


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)

    user: Mapped[User] = relationship(back_populates='sessions')


class UserFavorite(Base):
    __tablename__ = 'user_favorites'
    __table_args__ = (UniqueConstraint('user_id', 'shop_id', name='uq_user_favorites_user_shop'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    shop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    user: Mapped[User] = relationship(back_populates='favorites')
    profile: Mapped[Profile] = relationship(back_populates='favorites')


class Diary(Base):
    __tablename__ = 'diaries'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    photos: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)))
    status: Mapped[str] = mapped_column(StatusDiary, default='mod', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates='diaries')


class Availability(Base):
    __tablename__ = 'availabilities'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    date: Mapped[datetime] = mapped_column(Date, index=True)
    slots_json: Mapped[dict | None] = mapped_column(JSONB)
    is_today: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Outlink(Base):
    __tablename__ = 'outlinks'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(OutlinkKind, index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    target_url: Mapped[str] = mapped_column(Text)
    utm: Mapped[dict | None] = mapped_column(JSONB)


class Click(Base):
    __tablename__ = 'clicks'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlink_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('outlinks.id', ondelete='CASCADE'), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    referer: Mapped[str | None] = mapped_column(Text)
    ua: Mapped[str | None] = mapped_column(Text)
    ip_hash: Mapped[str | None] = mapped_column(String(128), index=True)


class Consent(Base):
    __tablename__ = 'consents'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    doc_version: Mapped[str] = mapped_column(String(40))
    agreed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(Text)


class Report(Base):
    __tablename__ = 'reports'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type: Mapped[str] = mapped_column(ReportTarget, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    reason: Mapped[str] = mapped_column(String(80))
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(ReportStatus, default='open', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    status: Mapped[str] = mapped_column(ReviewStatus, default='pending', nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_alias: Mapped[str | None] = mapped_column(String(80))
    visited_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates='reviews')


class AdminLog(Base):
    __tablename__ = 'admin_logs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    method: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(200), index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    admin_key_hash: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict | None] = mapped_column(JSONB)


class AdminChangeLog(Base):
    __tablename__ = 'admin_change_logs'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(32))
    before_json: Mapped[dict | None] = mapped_column(JSONB)
    after_json: Mapped[dict | None] = mapped_column(JSONB)
    admin_key_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), index=True)


class Reservation(Base):
    __tablename__ = 'reservations'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    menu_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    desired_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    desired_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(ReservationStatus, default='pending', index=True)
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_phone: Mapped[str] = mapped_column(String(40))
    customer_email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    customer_line_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    customer_remark: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    status_events: Mapped[list['ReservationStatusEvent']] = relationship(
        back_populates='reservation', cascade='all, delete-orphan', order_by='ReservationStatusEvent.changed_at'
    )
    user: Mapped[User | None] = relationship(back_populates='reservations')


class ReservationStatusEvent(Base):
    __tablename__ = 'reservation_status_events'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('reservations.id', ondelete='CASCADE'), index=True
    )
    status: Mapped[str] = mapped_column(ReservationStatus, nullable=False, index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    changed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text)

    reservation: Mapped['Reservation'] = relationship(back_populates='status_events')
