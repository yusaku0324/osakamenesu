import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from starlette.requests import Request

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
]:
    os.environ.pop(key, None)

import types

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
        self.notify_from_email = None
        self.mail_api_key = "test-mail-key"
        self.mail_from_address = "no-reply@example.com"
        self.mail_provider_base_url = "https://api.resend.com"
        self.escalation_pending_threshold_minutes = 30
        self.escalation_check_interval_minutes = 5
        self.auth_magic_link_expire_minutes = 15
        self.auth_magic_link_rate_limit = 5
        self.auth_session_ttl_days = 30
        self.auth_session_cookie_name = "osakamenesu_session"
        self.auth_session_cookie_secure = False
        self.auth_session_cookie_domain = None
        self.auth_magic_link_redirect_path = "/auth/complete"
        self.auth_magic_link_debug = True
        self.site_base_url = "https://example.com"


dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
dummy_settings_module.settings = _DummySettings()
sys.modules.setdefault("app.settings", dummy_settings_module)

from app import models  # type: ignore  # noqa: E402
from app.routers import auth  # type: ignore  # noqa: E402
from app.schemas import AuthRequestLink  # type: ignore  # noqa: E402
from app.settings import settings  # type: ignore  # noqa: E402
from app.utils.email import MailNotConfiguredError  # type: ignore  # noqa: E402


def _request(headers: Optional[Dict[str, str]] = None) -> Request:
    raw_headers = []
    headers = headers or {}
    for key, value in headers.items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/request-link",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


class FakeSession:
    def __init__(self) -> None:
        self.users: Dict[str, models.User] = {}
        self.tokens: list[models.UserAuthToken] = []

    async def execute(self, stmt):  # type: ignore[override]
        if stmt.column_descriptions and stmt.column_descriptions[0]["name"] == "User":
            email = None
            for criterion in getattr(stmt, "_where_criteria", []):
                if getattr(criterion.left, "name", None) == "email":
                    email = getattr(criterion.right, "value", None)
            user = self.users.get(email or "")

            class Result:
                def __init__(self, value):
                    self._value = value

                def scalar_one_or_none(self):
                    return self._value

            return Result(user)
        raw_columns = getattr(stmt, "_raw_columns", [])
        if raw_columns:
            first = raw_columns[0]
            if getattr(first, "name", None) == "count":
                class CountResult:
                    def scalar(self_inner):
                        return 0

                    def scalar_one(self_inner):
                        return 0

                    def scalar_one_or_none(self_inner):
                        return 0

                return CountResult()

        raise AssertionError(f"Unhandled statement: {stmt}")

    async def get(self, model, pk):  # type: ignore[override]
        if model is models.User:
            return self.users.get(pk)
        return None

    def add(self, obj: Any) -> None:
        if isinstance(obj, models.User):
            self.users[obj.email] = obj
        if isinstance(obj, models.UserAuthToken):
            self.tokens.append(obj)

    async def flush(self, _=None):  # type: ignore[override]
        return None

    async def commit(self) -> None:
        return None


@pytest.mark.anyio
async def test_request_link_sends_email(monkeypatch):
    original_api_key = settings.mail_api_key
    original_from = settings.mail_from_address
    settings.mail_api_key = "test-key"
    settings.mail_from_address = "no-reply@example.com"

    sent: Dict[str, Any] = {}

    async def _fake_send_email_async(**kwargs: Any) -> Dict[str, Any]:
        sent.update(kwargs)
        return {"id": "email-id"}

    monkeypatch.setattr(auth, "send_email_async", _fake_send_email_async)
    session = FakeSession()
    payload = AuthRequestLink(email="test@example.com")

    try:
        response = await auth.request_link(payload, _request(), db=session)
    finally:
        settings.mail_api_key = original_api_key
        settings.mail_from_address = original_from

    assert response["ok"] is True
    assert response["mail_sent"] is True
    assert sent["to"] == "test@example.com"
    assert "html" in sent
    assert session.tokens  # token persisted


@pytest.mark.anyio
async def test_request_link_handles_missing_mail_config(monkeypatch):
    original_api_key = settings.mail_api_key
    original_from = settings.mail_from_address
    settings.mail_api_key = None
    settings.mail_from_address = "no-reply@example.com"

    async def _raise_mail_not_configured(**kwargs: Any) -> Dict[str, Any]:
        raise MailNotConfiguredError("missing key")

    monkeypatch.setattr(auth, "send_email_async", _raise_mail_not_configured)
    session = FakeSession()
    payload = AuthRequestLink(email="test@example.com")

    try:
        response = await auth.request_link(payload, _request(), db=session)
    finally:
        settings.mail_api_key = original_api_key
        settings.mail_from_address = original_from

    assert response["ok"] is True
    assert response["mail_sent"] is False
    assert response.get("message") == "mail_not_configured"
