from pydantic_settings import BaseSettings
from pydantic import EmailStr, field_validator, Field


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:app@osakamenesu-db:5432/osaka_menesu"
    api_origin: str = "http://localhost:3000"
    meili_host: str = "http://osakamenesu-meili:7700"
    meili_master_key: str = "dev_meili_master_key"
    admin_api_key: str = "dev_admin_key"
    rate_limit_redis_url: str | None = None
    rate_limit_namespace: str = "osakamenesu_outlinks"
    rate_limit_redis_error_cooldown: float = 5.0
    init_db_on_startup: bool = True
    slack_webhook_url: str | None = None
    notify_email_endpoint: str | None = None
    notify_line_endpoint: str | None = None
    notify_smtp_host: str | None = None
    notify_smtp_port: int = 587
    notify_smtp_username: str | None = None
    notify_smtp_password: str | None = None
    notify_smtp_use_tls: bool = True
    notify_smtp_use_ssl: bool = False
    notify_from_email: EmailStr | None = None
    admin_notification_emails: list[EmailStr] = Field(default_factory=list)
    escalation_pending_threshold_minutes: int = 30
    escalation_check_interval_minutes: int = 5
    auth_magic_link_expire_minutes: int = 15
    auth_magic_link_rate_limit: int = 5
    auth_session_ttl_days: int = 30
    auth_session_cookie_name: str = "osakamenesu_session"
    auth_session_cookie_secure: bool = False
    auth_session_cookie_domain: str | None = None
    auth_magic_link_redirect_path: str = "/auth/complete"
    auth_magic_link_debug: bool = True
    site_base_url: str | None = None

    class Config:
        env_file = ".env"
        env_prefix = ""

    @field_validator("admin_notification_emails", mode="before")
    @classmethod
    def _parse_admin_emails(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [email.strip() for email in value.split(",") if email.strip()]
        return value


settings = Settings()
