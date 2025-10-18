import os
import sys
import types
import uuid
from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace

import pytest

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


dummy_settings_module = types.ModuleType("app.settings")


class _DummySettings:
    def __init__(self) -> None:
        self.database_url = "postgresql+asyncpg://app:app@localhost:5432/osaka_menesu"
        self.api_origin = "http://localhost:3000"
        self.meili_host = "http://127.0.0.1:7700"
        self.meili_master_key = "dev_key"
        self.admin_api_key = "dev_admin_key"
        self.rate_limit_redis_url = None
        self.rate_limit_namespace = "test"
        self.rate_limit_redis_error_cooldown = 0.0
        self.init_db_on_startup = False
        self.slack_webhook_url = None
        self.notify_email_endpoint = None
        self.notify_line_endpoint = None
        self.escalation_pending_threshold_minutes = 30
        self.escalation_check_interval_minutes = 5


dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
dummy_settings_module.settings = _DummySettings()
sys.modules.setdefault("app.settings", dummy_settings_module)

from app import models  # type: ignore  # noqa: E402
from app.routers import dashboard_shops  # type: ignore  # noqa: E402


class FakeSession:
    def __init__(self, profile: models.Profile) -> None:
        self._profile = profile
        self.committed = False
        self.refreshed = False

    async def get(self, model, pk):  # type: ignore[override]
        if model is models.Profile and pk == self._profile.id:
            return self._profile
        return None

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, instance):  # type: ignore[override]
        self.refreshed = True


@pytest.mark.anyio
async def test_update_profile_changes_status(monkeypatch):
    now = datetime.now(UTC)
    profile = models.Profile(
        id=uuid.uuid4(),
        name="ステータステスト",
        area="梅田",
        price_min=9000,
        price_max=16000,
        bust_tag="C",
        service_type="store",
        contact_json={"store_name": "ステータステスト"},
        status="draft",
        created_at=now,
        updated_at=now,
    )
    session = FakeSession(profile)

    async def _noop_reindex(db, prof):  # type: ignore
        return None

    monkeypatch.setattr(dashboard_shops, "_reindex_profile", _noop_reindex)

    payload = dashboard_shops.DashboardShopProfileUpdatePayload(
        updated_at=now,
        status="published",
    )

    response = await dashboard_shops.update_dashboard_shop_profile(
        profile.id,
        payload,
        db=session,
        user=SimpleNamespace(id=uuid.uuid4()),
    )

    assert profile.status == "published"
    assert response.status == "published"
    assert session.committed is True
    assert session.refreshed is True
