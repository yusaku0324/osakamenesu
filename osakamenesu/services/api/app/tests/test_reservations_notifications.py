import os
import sys
import types
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

APP_ROOT = Path(__file__).resolve().parents[2]
os.chdir(APP_ROOT.parents[2])
sys.path.insert(0, str(APP_ROOT))

for key in [
    "PROJECT_NAME",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "API_PORT",
    "API_HOST",
    "NEXT_PUBLIC_API_BASE",
    "API_INTERNAL_BASE",
    "ADMIN_BASIC_USER",
    "ADMIN_BASIC_PASS",
    "JSONL_PATH",
    "OPENAI_API_KEY",
    "X_COOKIE_PATH",
    "PROVIDERS",
    "MAX_TOKENS",
]:
    os.environ.pop(key, None)


dummy_settings_module = types.ModuleType("app.settings")


class _DummySettings:
    def __init__(self) -> None:
        self.database_url = "postgresql+asyncpg://app:app@localhost:5432/osaka_menesu"
        self.api_origin = "http://localhost:3000"
        self.media_storage_backend = "local"
        self.media_local_directory = "test-media"
        self.media_url_prefix = "/media"
        self.media_cdn_base_url = None
        self.slack_webhook_url = None
        self.notify_email_endpoint = None
        self.notify_line_endpoint = None
        self.notify_from_email = None
        self.mail_api_key = None
        self.mail_from_address = "no-reply@example.com"
        self.mail_provider_base_url = "https://api.resend.com"
        self.dashboard_session_cookie_name = "osakamenesu_session"
        self.site_session_cookie_name = "osakamenesu_session"

    @property
    def media_root(self) -> Path:
        return Path.cwd() / self.media_local_directory


dummy_settings_module.settings = _DummySettings()
dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
sys.modules.setdefault("app.settings", dummy_settings_module)

from app.schemas import ReservationCreateRequest, ReservationCustomerInput  # type: ignore  # noqa: E402
from app.routers import reservations  # type: ignore  # noqa: E402


class DummySession:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0

    def add(self, instance) -> None:
        self.added.append(instance)

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, instance, attribute_names=None) -> None:  # type: ignore[override]
        if getattr(instance, "id", None) is None:
            instance.id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if getattr(instance, "updated_at", None) is None:
            instance.updated_at = now


@pytest.mark.asyncio
async def test_create_reservation_passes_resolved_channels(monkeypatch: pytest.MonkeyPatch) -> None:
    shop_id = uuid.uuid4()
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    end = start + timedelta(minutes=90)

    payload = ReservationCreateRequest(
        shop_id=shop_id,
        desired_start=start,
        desired_end=end,
        channel="web",
        notes="アロマ強めで",
        customer=ReservationCustomerInput(name="山田 太郎", phone="09012345678", email="guest@example.com"),
    )

    scheduled: dict[str, object] = {}

    def capture(notification) -> None:
        scheduled["payload"] = notification

    async def fake_ensure_shop(db, incoming_shop_id):
        assert incoming_shop_id == shop_id
        return SimpleNamespace(
            id=shop_id,
            name="癒しサロン",
            contact_json={"phone": "06-1234-5678", "line": "https://line.me/R/ti/p/@salon"},
        )

    async def fake_check_overlap(*_args, **_kwargs):
        return False

    async def fake_resolve(_db, incoming_shop_id, status):
        assert incoming_shop_id == shop_id
        assert status == "pending"
        return {
            "emails": ["ops@example.com"],
            "slack": "https://hooks.slack.com/services/test",
            "line": "line-token",
        }

    monkeypatch.setattr(reservations, "schedule_reservation_notification", capture, raising=False)
    monkeypatch.setattr(reservations, "_ensure_shop", fake_ensure_shop)
    monkeypatch.setattr(reservations, "_check_overlap", fake_check_overlap)
    monkeypatch.setattr(reservations, "_resolve_notification_channels", fake_resolve)

    session = DummySession()
    result = await reservations.create_reservation(payload, session, user=None)

    assert result["status"] == "pending"
    assert session.commits == 1
    assert "payload" in scheduled

    notification = scheduled["payload"]
    assert notification.shop_id == str(shop_id)
    assert notification.shop_name == "癒しサロン"
    assert notification.customer_name == payload.customer.name
    assert notification.customer_phone == payload.customer.phone
    assert notification.customer_email == payload.customer.email
    assert notification.email_recipients == ["ops@example.com"]
    assert notification.slack_webhook_url == "https://hooks.slack.com/services/test"
    assert notification.line_notify_token == "line-token"
    assert notification.shop_phone == "06-1234-5678"
    assert notification.shop_line_contact == "https://line.me/R/ti/p/@salon"
