import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient, ASGITransport


# Ensure the application package is importable when running tests from repo root
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "services" / "api"))

import types

dummy_settings_module = types.ModuleType("app.settings")


class _DummySettings:
    def __init__(self) -> None:
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.api_origin = "http://localhost:3000"
        self.meili_host = "http://127.0.0.1:7700"
        self.meili_master_key = "dev"
        self.admin_api_key = "dev_admin_key"
        self.rate_limit_redis_url = None
        self.rate_limit_namespace = "test"
        self.rate_limit_redis_error_cooldown = 0.0
        self.init_db_on_startup = False
        self.slack_webhook_url = None
        self.notify_email_endpoint = None
        self.notify_line_endpoint = None
        self.notify_smtp_host = None
        self.notify_smtp_port = 587
        self.notify_smtp_username = None
        self.notify_smtp_password = None
        self.notify_smtp_use_tls = True
        self.notify_smtp_use_ssl = False
        self.notify_from_email = None
        self.admin_notification_emails: list[str] = []
        self.escalation_pending_threshold_minutes = 30
        self.escalation_check_interval_minutes = 5
        self.auth_magic_link_expire_minutes = 15
        self.auth_magic_link_rate_limit = 5
        self.auth_session_ttl_days = 30
        self.auth_session_cookie_name = "osakamenesu_session"
        self.auth_session_cookie_secure = False
        self.auth_session_cookie_domain = None
        self.auth_magic_link_redirect_path = "/auth/complete"
        self.auth_magic_link_debug = False
        self.site_base_url = "http://localhost:3000"


dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
dummy_settings_module.settings = _DummySettings()
sys.modules["app.settings"] = dummy_settings_module

from app.db import get_session  # type: ignore  # noqa: E402
from app.deps import get_dashboard_profile, require_user  # type: ignore  # noqa: E402
from app.routers.dashboard_notifications import router  # type: ignore  # noqa: E402


class DummySession:
    def __init__(self, profiles: Dict[UUID, SimpleNamespace]) -> None:
        self._profiles = profiles
        self.add_calls: list[SimpleNamespace] = []
        self.commit_calls = 0
        self.refresh_calls: list[SimpleNamespace] = []

    async def get(self, model, key):  # pragma: no cover - model is unused for stubbing
        return self._profiles.get(key)

    def add(self, obj):  # pragma: no cover - router stores the profile back
        self.add_calls.append(obj)

    async def commit(self):  # pragma: no cover - tracking invocation count
        self.commit_calls += 1

    async def refresh(self, obj):  # pragma: no cover - no-op for tests
        self.refresh_calls.append(obj)


def make_profile(
    profile_id: UUID,
    *,
    user_ids: Iterable[UUID],
    updated_at: datetime | None = None,
    emails: Iterable[str] | None = None,
    line_token: str | None = None,
    slack_webhook: str | None = None,
    trigger_status: Iterable[str] | None = None,
    channel_flags: Dict[str, bool] | None = None,
) -> SimpleNamespace:
    updated = updated_at or datetime.now(timezone.utc)
    emails_list = list(emails or ["shop@example.com"])
    flags = channel_flags or {"email": True, "line": False, "slack": False}
    return SimpleNamespace(
        id=profile_id,
        updated_at=updated,
        contact_json={"dashboard_user_ids": [str(uid) for uid in user_ids]},
        notification_emails=list(emails_list),
        notification_line_token=line_token,
        notification_slack_webhook=slack_webhook,
        notification_trigger_status=list(trigger_status or ["pending"]),
        notification_channels_enabled=dict(flags),
    )


def override_session(app: FastAPI, session: DummySession) -> None:
    async def _session_override():
        yield session

    app.dependency_overrides[get_session] = _session_override


def override_user(app: FastAPI, user: SimpleNamespace | None) -> None:
    if user is None:
        async def _raise_unauth():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")

        app.dependency_overrides[require_user] = _raise_unauth
    else:
        async def _user_override():
            return user

        app.dependency_overrides[require_user] = _user_override


@pytest.fixture()
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    yield app
    app.dependency_overrides.clear()


@pytest.fixture()
async def api_client(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_get_notification_settings_success(test_app: FastAPI, api_client: AsyncClient):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(
        profile_id,
        user_ids=[user_id],
        emails=["shop@example.com", "owner@example.com"],
        line_token="LINE_TOKEN_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
        slack_webhook="https://hooks.slack.com/services/T000/B000/XYZ",
        trigger_status=["pending", "confirmed"],
        channel_flags={"email": True, "line": True, "slack": True},
    )
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    response = await api_client.get(f"/api/dashboard/shops/{profile_id}/notifications")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["profile_id"] == str(profile_id)
    returned_at = datetime.fromisoformat(body["updated_at"].replace("Z", "+00:00"))
    assert returned_at == profile.updated_at
    assert body["channels"]["email"] == {
        "enabled": True,
        "recipients": ["shop@example.com", "owner@example.com"],
    }
    assert body["channels"]["line"] == {
        "enabled": True,
        "token": "LINE_TOKEN_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
    }
    assert body["channels"]["slack"] == {
        "enabled": True,
        "webhook_url": "https://hooks.slack.com/services/T000/B000/XYZ",
    }
    assert body["trigger_status"] == ["pending", "confirmed"]


@pytest.mark.anyio
async def test_get_notification_settings_requires_auth(test_app: FastAPI, api_client: AsyncClient):
    override_session(test_app, DummySession({}))
    override_user(test_app, None)

    profile_id = uuid4()
    response = await api_client.get(f"/api/dashboard/shops/{profile_id}/notifications")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    detail = response.json()["detail"]
    assert detail == "not_authenticated"


@pytest.mark.anyio
async def test_get_notification_settings_not_found(test_app: FastAPI, api_client: AsyncClient):
    user_id = uuid4()
    session = DummySession({})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    profile_id = uuid4()
    response = await api_client.get(f"/api/dashboard/shops/{profile_id}/notifications")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "profile_not_found"


@pytest.mark.anyio
async def test_get_notification_settings_forbidden_when_not_configured(
    test_app: FastAPI,
    api_client: AsyncClient,
):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(profile_id, user_ids=[])
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    response = await api_client.get(f"/api/dashboard/shops/{profile_id}/notifications")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "dashboard_access_not_configured"


@pytest.mark.anyio
async def test_get_notification_settings_forbidden_when_user_not_allowed(
    test_app: FastAPI,
    api_client: AsyncClient,
):
    profile_id = uuid4()
    user_id = uuid4()
    other_user_id = uuid4()
    profile = make_profile(profile_id, user_ids=[other_user_id])
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    response = await api_client.get(f"/api/dashboard/shops/{profile_id}/notifications")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "dashboard_access_denied"


@pytest.mark.anyio
async def test_update_notification_settings_conflict(test_app: FastAPI, api_client: AsyncClient):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(profile_id, user_ids=[user_id])
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    stale_timestamp = (profile.updated_at - timedelta(seconds=5)).isoformat()
    payload = {
        "updated_at": stale_timestamp,
        "trigger_status": ["pending"],
        "channels": {
            "email": {"enabled": True, "recipients": ["new@example.com"]},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
    }

    response = await api_client.put(
        f"/api/dashboard/shops/{profile_id}/notifications",
        json=payload,
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()["detail"]
    assert body["code"] == "notification_settings_conflict"
    assert "current" in body
    assert session.commit_calls == 0


@pytest.mark.anyio
async def test_update_notification_settings_success(test_app: FastAPI, api_client: AsyncClient):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(
        profile_id,
        user_ids=[user_id],
        channel_flags={"email": False, "line": False, "slack": False},
    )
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    payload = {
        "updated_at": profile.updated_at.isoformat(),
        "trigger_status": ["confirmed", "declined"],
        "channels": {
            "email": {"enabled": True, "recipients": ["owner@example.com"]},
            "line": {"enabled": True, "token": "L" * 40},
            "slack": {"enabled": True, "webhook_url": "https://hooks.slack.com/services/T/1/ABC"},
        },
    }

    response = await api_client.put(
        f"/api/dashboard/shops/{profile_id}/notifications",
        json=payload,
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["trigger_status"] == ["confirmed", "declined"]
    assert profile.notification_emails == ["owner@example.com"]
    assert profile.notification_line_token == payload["channels"]["line"]["token"]
    assert profile.notification_slack_webhook == payload["channels"]["slack"]["webhook_url"]
    assert profile.notification_channels_enabled == {
        "email": True,
        "line": True,
        "slack": True,
    }
    assert session.commit_calls == 1


@pytest.mark.anyio
async def test_update_notification_settings_validation_error(test_app: FastAPI, api_client: AsyncClient):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(profile_id, user_ids=[user_id])
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    payload = {
        "updated_at": profile.updated_at.isoformat(),
        "trigger_status": ["pending"],
        "channels": {
            "email": {"enabled": True, "recipients": []},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
    }

    response = await api_client.put(
        f"/api/dashboard/shops/{profile_id}/notifications",
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = response.json()["detail"]
    # Validate that we surface the Pydantic error about missing recipients
    assert any("宛先" in err["msg"] for err in detail), detail
    assert session.commit_calls == 0


@pytest.mark.anyio
async def test_test_notification_settings_success(test_app: FastAPI, api_client: AsyncClient):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(profile_id, user_ids=[user_id])
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    payload = {
        "trigger_status": ["pending"],
        "channels": {
            "email": {"enabled": True, "recipients": ["owner@example.com"]},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
    }

    response = await api_client.post(
        f"/api/dashboard/shops/{profile_id}/notifications/test",
        json=payload,
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content in (b"", b"null")


@pytest.mark.anyio
async def test_test_notification_settings_validation_error(test_app: FastAPI, api_client: AsyncClient):
    profile_id = uuid4()
    user_id = uuid4()
    profile = make_profile(profile_id, user_ids=[user_id])
    session = DummySession({profile_id: profile})

    override_session(test_app, session)
    override_user(test_app, SimpleNamespace(id=user_id))

    payload = {
        "trigger_status": ["unknown-status"],
        "channels": {
            "email": {"enabled": False, "recipients": []},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
    }

    response = await api_client.post(
        f"/api/dashboard/shops/{profile_id}/notifications/test",
        json=payload,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = response.json()["detail"]
    assert any((err.get("input") == "unknown-status" or "未対応" in err.get("msg", "")) for err in detail), detail


@pytest.mark.anyio
async def test_get_dashboard_profile_dependency_direct():
    user_id = uuid4()
    profile_id = uuid4()
    profile = make_profile(profile_id, user_ids=[user_id])
    session = DummySession({profile_id: profile})

    result = await get_dashboard_profile(profile_id, user=SimpleNamespace(id=user_id), db=session)
    assert result is profile
