from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional

from ..settings import settings


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def magic_link_expiry(now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now(UTC)
    return now + timedelta(minutes=settings.auth_magic_link_expire_minutes)


def session_expiry(now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now(UTC)
    return now + timedelta(days=settings.auth_session_ttl_days)
