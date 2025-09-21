from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:app@db:5432/osaka_menesu"
    api_origin: str = "http://localhost:3000"
    meili_host: str = "http://meili:7700"
    meili_master_key: str = "dev_meili_master_key"
    admin_api_key: str = "dev_admin_key"
    rate_limit_redis_url: str | None = None
    rate_limit_namespace: str = "osaka_outlinks"
    rate_limit_redis_error_cooldown: float = 5.0
    init_db_on_startup: bool = True
    slack_webhook_url: str | None = None
    notify_email_endpoint: str | None = None
    notify_line_endpoint: str | None = None
    escalation_pending_threshold_minutes: int = 30
    escalation_check_interval_minutes: int = 5

    class Config:
        env_file = ".env"
        env_prefix = ""


settings = Settings()
