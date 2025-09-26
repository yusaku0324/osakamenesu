import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks


# Align module path with production layout so router imports resolve during tests
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "services" / "api"))

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

import types

dummy_settings_module = types.ModuleType("app.settings")


class _DummySettings:
    def __init__(self) -> None:
        self.database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://app:app@localhost:5432/osaka_menesu",
        )
        self.api_origin = os.environ.get("API_ORIGIN", "http://localhost:3000")
        self.meili_host = os.environ.get("MEILI_HOST", "http://127.0.0.1:7700")
        self.meili_master_key = os.environ.get("MEILI_MASTER_KEY", "dev_key")
        self.admin_api_key = os.environ.get("ADMIN_API_KEY", "dev_admin_key")
        self.rate_limit_redis_url = os.environ.get("RATE_LIMIT_REDIS_URL")
        self.rate_limit_namespace = os.environ.get("RATE_LIMIT_NAMESPACE", "test")
        self.rate_limit_redis_error_cooldown = float(os.environ.get("RATE_LIMIT_REDIS_ERROR_COOLDOWN", "0"))
        self.init_db_on_startup = False
        self.slack_webhook_url = None
        self.notify_email_endpoint = None
        self.notify_line_endpoint = None
        self.escalation_pending_threshold_minutes = 30
        self.escalation_check_interval_minutes = 5


dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
dummy_settings_module.settings = _DummySettings()
sys.modules.setdefault("app.settings", dummy_settings_module)

email_validator_module = types.ModuleType("email_validator")


class _EmailNotValidError(ValueError):
    pass


def _validate_email(address: str, **_kwargs):
    return types.SimpleNamespace(email=address)


email_validator_module.EmailNotValidError = _EmailNotValidError
email_validator_module.validate_email = _validate_email
sys.modules.setdefault("email_validator", email_validator_module)

import importlib.metadata as importlib_metadata


def _version_stub(name: str):
    if name == "email-validator":
        return "2.0.0"
    raise importlib_metadata.PackageNotFoundError(name)


importlib_metadata.version = _version_stub  # type: ignore[assignment]

try:
    import pydantic.networks as _pydantic_networks

    _pydantic_networks.version = _version_stub  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - defensive guard if import layout changes
    pass


@pytest.mark.asyncio
async def test_create_reservation_queues_notification(monkeypatch):
    from app.routers import reservations  # type: ignore
    from app.schemas import ReservationCreateRequest, ReservationCustomerInput  # type: ignore

    shop_id = uuid4()
    shop = SimpleNamespace(id=shop_id, name="通知テスト店")

    async def fake_ensure_shop(db, sid):  # pragma: no cover -- stub
        assert sid == shop_id
        return shop

    async def fake_check_overlap(db, sid, desired_start, desired_end, exclude_reservation_id=None):
        return False

    calls = []

    def fake_queue(*, reservation, shop: SimpleNamespace, background_tasks):
        calls.append({
            "reservation": reservation,
            "shop": shop,
            "background_tasks": background_tasks,
        })

    class DummyReservation:
        def __init__(self, **kwargs):
            self.created_at = datetime.now(UTC)
            self.updated_at = self.created_at
            self.status_events = []
            self.status = kwargs.get("status")
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.id = kwargs.get("id") or uuid4()

    class DummyStatusEvent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeSession:
        def __init__(self):
            self.added = []
            self.commits = 0
            self.refreshes = []

        def add(self, obj):
            self.added.append(obj)

        async def commit(self):
            self.commits += 1

        async def refresh(self, obj, attribute_names=None):
            self.refreshes.append((obj, attribute_names))
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if attribute_names and "status_events" in attribute_names and not getattr(obj, "status_events", None):
                obj.status_events = []

    monkeypatch.setattr(reservations, "_ensure_shop", fake_ensure_shop)
    monkeypatch.setattr(reservations, "_check_overlap", fake_check_overlap)
    monkeypatch.setattr(reservations, "queue_reservation_notifications", fake_queue)
    monkeypatch.setattr(reservations.models, "Reservation", DummyReservation)
    monkeypatch.setattr(reservations.models, "ReservationStatusEvent", DummyStatusEvent)

    payload = ReservationCreateRequest(
        shop_id=shop_id,
        desired_start=datetime.now(UTC),
        desired_end=datetime.now(UTC) + timedelta(hours=1),
        customer=ReservationCustomerInput(name="テスター", phone="000-0000"),
    )

    db = FakeSession()
    background_tasks = BackgroundTasks()

    result = await reservations.create_reservation(
        payload,
        background_tasks=background_tasks,
        db=db,
        user=None,
    )

    assert calls, "queue_reservation_notifications should be invoked"
    assert calls[0]["shop"] is shop
    assert calls[0]["background_tasks"] is background_tasks
    assert result["status"] == "pending"
    assert result["id"] == calls[0]["reservation"].id
