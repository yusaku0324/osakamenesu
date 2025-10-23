import os
import sys
import types
import uuid
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "services" / "api"))

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
        self.notify_from_email = None
        self.mail_api_key = "test-mail-key"
        self.mail_from_address = "no-reply@example.com"
        self.mail_provider_base_url = "https://api.resend.com"
        self.dashboard_session_cookie_name = "osakamenesu_session"
        self.site_session_cookie_name = "osakamenesu_session"
        self.site_base_url = None


dummy_settings_module.Settings = _DummySettings  # type: ignore[attr-defined]
dummy_settings_module.settings = _DummySettings()
sys.modules.setdefault("app.settings", dummy_settings_module)

from app import models  # type: ignore  # noqa: E402
from app.routers import dashboard_therapists  # type: ignore  # noqa: E402


def test_sanitize_strings_filters_blanks():
    values = ["  a  ", "", "  ", "b", None, "c "]
    result = dashboard_therapists._sanitize_strings(values)  # type: ignore[attr-defined]
    assert result == ["a", "b", "c"]


def test_serialize_and_summary_roundtrip():
    now = datetime.now(UTC)
    profile_id = uuid.uuid4()
    therapist = models.Therapist(
        id=uuid.uuid4(),
        profile_id=profile_id,
        name="佐藤 さゆり",
        alias="Sayuri",
        headline="極上癒し",
        biography="3年経験",
        specialties=["オイル", "ヘッド"],
        qualifications=["認定セラピスト"],
        experience_years=3,
        photo_urls=["https://example.com/1.jpg"],
        display_order=5,
        status="draft",
        is_booking_enabled=True,
        created_at=now,
        updated_at=now,
    )

    detail = dashboard_therapists._serialize_therapist(therapist)  # type: ignore[attr-defined]
    summary = dashboard_therapists._summary_from_detail(detail)  # type: ignore[attr-defined]

    assert summary.name == therapist.name
    assert summary.alias == therapist.alias
    assert summary.status == therapist.status
    assert summary.display_order == therapist.display_order
    assert summary.specialties == therapist.specialties
    assert detail.qualifications == therapist.qualifications
