import os
import sys
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4, UUID

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "services" / "api"))


from app.main import app  # type: ignore  # noqa: E402
from app import models, deps  # type: ignore  # noqa: E402
from app.db import get_session  # type: ignore  # noqa: E402
from app.settings import settings  # type: ignore  # noqa: E402
from app.routers import dashboard_notifications as dashboard_router  # type: ignore  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def session(monkeypatch) -> Any:
    class DummySession:
        def __init__(self) -> None:
            self._profile: models.Profile | None = None
            self.commits = 0

        async def get(self, model, pk):
            if model is models.Profile and self._profile and str(self._profile.id) == str(pk):
                return self._profile
            if model is models.User and self._profile and self._profile.contact_json:
                allowed = self._profile.contact_json.get("dashboard_user_ids", [])
                if str(pk) in {str(x) for x in allowed}:
                    user = models.User(
                        id=pk,
                        email="owner@example.com",
                        status="active",
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    return user
            return None

        async def commit(self) -> None:
            self.commits += 1

        async def refresh(self, instance, attribute_names=None):
            return None

        def add(self, instance):
            return None

    dummy = DummySession()

    async def override_session():
        yield dummy

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[dashboard_router.get_session] = override_session

    async def override_require_user(request: Request):
        cookie_name = settings.auth_session_cookie_name
        if not cookie_name:
            raise HTTPException(status_code=401, detail="not_authenticated")
        raw_token = request.cookies.get(cookie_name)
        if not raw_token or not raw_token.startswith("session-"):
            raise HTTPException(status_code=401, detail="not_authenticated")
        suffix = raw_token[len("session-") :]
        try:
            user_id = UUID(suffix)
        except ValueError:
            raise HTTPException(status_code=401, detail="not_authenticated")
        return models.User(
            id=user_id,
            email="owner@example.com",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def override_get_dashboard_profile(profile_id: UUID, request: Request):
        user = await override_require_user(request)
        if not dummy._profile or str(dummy._profile.id) != str(profile_id):
            raise HTTPException(status_code=404, detail="profile_not_found")
        allowed = {str(x) for x in (dummy._profile.contact_json or {}).get("dashboard_user_ids", [])}
        if str(user.id) not in allowed:
            raise HTTPException(status_code=403, detail="dashboard_access_denied")
        return dummy._profile

    monkeypatch.setitem(app.dependency_overrides, deps.require_user, override_require_user)
    monkeypatch.setitem(app.dependency_overrides, deps.get_dashboard_profile, override_get_dashboard_profile)
    monkeypatch.setitem(app.dependency_overrides, dashboard_router.get_dashboard_profile, override_get_dashboard_profile)
    return dummy


def _profile_factory(user_id=None, updated_at=None) -> models.Profile:
    pid = uuid4()
    profile = models.Profile(
        id=pid,
        name="Test Shop",
        area="梅田",
        price_min=10000,
        price_max=15000,
        bust_tag="C",
        service_type="store",
        created_at=datetime.now(UTC),
        updated_at=updated_at or datetime.now(UTC),
    )
    profile.contact_json = {"dashboard_user_ids": [str(user_id or uuid4())]}
    profile.notify_channels_enabled = {"email": False, "line": False, "slack": False}
    profile.notify_email_recipients = []
    profile.notify_trigger_status = []
    return profile


def _auth_headers(user_id: str | None = None) -> Dict[str, str]:
    session_token = f"session-{user_id or uuid4()}"
    return {"cookie": f"osakamenesu_session={session_token}"}


def test_get_requires_authentication(client: TestClient):
    response = client.get("/api/dashboard/shops/00000000-0000-0000-0000-000000000000/notifications")
    assert response.status_code == 401


def test_get_returns_404_for_missing_profile(client: TestClient, session: Any):
    user_id = uuid4()
    headers = _auth_headers(str(user_id))
    response = client.get(
        f"/api/dashboard/shops/{uuid4()}/notifications",
        headers=headers,
    )
    assert response.status_code == 404


def test_get_returns_403_when_user_not_allowed(client: TestClient, session: Any):
    allowed_user = uuid4()
    profile = _profile_factory(user_id=allowed_user)
    session._profile = profile

    other_user = uuid4()
    headers = _auth_headers(str(other_user))

    response = client.get(
        f"/api/dashboard/shops/{profile.id}/notifications",
        headers=headers,
    )
    assert response.status_code == 403


def test_get_returns_existing_settings(client: TestClient, session: Any):
    user_id = uuid4()
    profile = _profile_factory(user_id=user_id)
    profile.notify_email_recipients = ["owner@example.com"]
    profile.notify_channels_enabled = {"email": True, "line": False, "slack": False}
    profile.notify_trigger_status = ["pending"]
    session._profile = profile

    headers = _auth_headers(str(user_id))
    response = client.get(
        f"/api/dashboard/shops/{profile.id}/notifications",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["channels"]["email"]["enabled"] is True
    assert payload["channels"]["email"]["recipients"] == ["owner@example.com"]
    assert payload["trigger_status"] == ["pending"]


def test_put_conflict_returns_409(client: TestClient, session: Any):
    user_id = uuid4()
    profile = _profile_factory(user_id=user_id)
    session._profile = profile

    headers = _auth_headers(str(user_id))
    now = datetime.now(UTC)
    payload = {
        "updated_at": (now - timedelta(minutes=5)).isoformat(),
        "channels": {
            "email": {"enabled": True, "recipients": ["owner@example.com"]},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
        "trigger_status": ["pending"],
    }

    response = client.put(
        f"/api/dashboard/shops/{profile.id}/notifications",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 409


def test_put_succeeds(client: TestClient, session: Any):
    user_id = uuid4()
    updated_at = datetime.now(UTC)
    profile = _profile_factory(user_id=user_id, updated_at=updated_at)
    session._profile = profile

    headers = _auth_headers(str(user_id))
    payload = {
        "updated_at": updated_at.isoformat(),
        "channels": {
            "email": {"enabled": True, "recipients": ["owner@example.com"]},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
        "trigger_status": ["pending", "confirmed"],
    }

    response = client.put(
        f"/api/dashboard/shops/{profile.id}/notifications",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["channels"]["email"]["enabled"] is True
    assert session.commits == 1


def test_put_validation_errors(client: TestClient, session: Any):
    user_id = uuid4()
    updated_at = datetime.now(UTC)
    profile = _profile_factory(user_id=user_id, updated_at=updated_at)
    session._profile = profile

    headers = _auth_headers(str(user_id))
    payload = {
        "updated_at": updated_at.isoformat(),
        "channels": {
            "email": {"enabled": True, "recipients": []},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
        "trigger_status": [],
    }

    response = client.put(
        f"/api/dashboard/shops/{profile.id}/notifications",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 422


def test_post_test_accepts_valid_payload(client: TestClient, session: Any):
    user_id = uuid4()
    profile = _profile_factory(user_id=user_id)
    session._profile = profile

    headers = _auth_headers(str(user_id))
    payload = {
        "channels": {
            "email": {"enabled": False, "recipients": []},
            "line": {"enabled": True, "token": "A" * 43},
            "slack": {"enabled": False, "webhook_url": None},
        },
        "trigger_status": ["pending"],
    }

    response = client.post(
        f"/api/dashboard/shops/{profile.id}/notifications/test",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 204


def test_post_test_validation_error(client: TestClient, session: Any):
    user_id = uuid4()
    profile = _profile_factory(user_id=user_id)
    session._profile = profile

    headers = _auth_headers(str(user_id))
    payload = {
        "channels": {
            "email": {"enabled": True, "recipients": []},
            "line": {"enabled": False, "token": None},
            "slack": {"enabled": False, "webhook_url": None},
        },
        "trigger_status": [],
    }

    response = client.post(
        f"/api/dashboard/shops/{profile.id}/notifications/test",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 422
