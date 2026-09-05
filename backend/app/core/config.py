"""Application settings — loaded from environment variables."""

from functools import lru_cache
from typing import Any, List
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Employee Platform"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-me-to-a-long-random-string-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    database_url: str = "postgresql+asyncpg://aiep:aiep@localhost:5432/aiep"
    database_url_sync: str = "postgresql://aiep:aiep@localhost:5432/aiep"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    test_center_run_timeout_seconds: int = 3600

    # Tenant-scoped execution resource shares. A tenant-specific entry wins;
    # the default is deliberately small so one tenant cannot monopolize workers.
    tenant_resource_concurrency: dict[str, int] = {}
    tenant_resource_default_concurrency: int = 1
    tenant_resource_lease_seconds: int = 3600

    # Data lifecycle: operational records default to one year and may be
    # overridden through DATA_RETENTION_DAYS within the enforced safety bounds.
    data_retention_days: int = 365

    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.18.0.1:3000",
        "http://host.docker.internal:3000",
    ]

    # Explicit opt-in for the local production-like Docker stack. This keeps
    # the normal production HTTPS policy intact while allowing localhost HTTP
    # endpoints on a developer workstation without weakening VPS production.
    local_production_allow_http: bool = False

    @model_validator(mode="after")
    def validate_production_safety(self):
        """Fail fast on unsafe production configuration."""
        if self.test_center_run_timeout_seconds < 1 or self.test_center_run_timeout_seconds > 86_400:
            raise ValueError("TEST_CENTER_RUN_TIMEOUT_SECONDS must be between 1 and 86400")
        if self.tenant_resource_default_concurrency < 1:
            raise ValueError("TENANT_RESOURCE_DEFAULT_CONCURRENCY must be positive")
        if self.tenant_resource_lease_seconds < 1 or self.tenant_resource_lease_seconds > 86_400:
            raise ValueError("TENANT_RESOURCE_LEASE_SECONDS must be between 1 and 86400")
        if any(limit < 1 for limit in self.tenant_resource_concurrency.values()):
            raise ValueError("TENANT_RESOURCE_CONCURRENCY values must be positive")
        if self.data_retention_days < 1 or self.data_retention_days > 3650:
            raise ValueError("DATA_RETENTION_DAYS must be between 1 and 3650")
        if self.app_env.lower() in {"production", "prod"}:
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if self.secret_key.startswith("change-me") or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be a strong production secret")
            if not self.rate_limit_enabled:
                raise ValueError("RATE_LIMIT_ENABLED must be true in production")
            if not self.rate_limit_fail_closed:
                raise ValueError("RATE_LIMIT_FAIL_CLOSED must be true in production")
            if not self.cors_origins:
                raise ValueError("CORS_ORIGINS must explicitly allow trusted origins in production")

            if not self.local_production_allow_http:
                if any(urlparse(origin).scheme != "https" for origin in self.cors_origins):
                    raise ValueError("CORS_ORIGINS must use HTTPS in production")
                if urlparse(self.frontend_base_url).scheme != "https":
                    raise ValueError("FRONTEND_BASE_URL must use HTTPS in production")
                if urlparse(self.frontend_app_url).scheme != "https":
                    raise ValueError("FRONTEND_APP_URL must use HTTPS in production")

            database_urls = {
                "DATABASE_URL": self.database_url,
                "DATABASE_URL_SYNC": self.database_url_sync,
            }
            for name, value in {
                **database_urls,
                "REDIS_URL": self.redis_url,
                "CELERY_BROKER_URL": self.celery_broker_url,
                "CELERY_RESULT_BACKEND": self.celery_result_backend,
            }.items():
                parsed = urlparse(value)
                host = (parsed.hostname or "").lower()
                if host in {"localhost", "127.0.0.1", "::1"}:
                    raise ValueError(f"{name} must not point to localhost in production")

            # The repository's E2E defaults intentionally use a known demo
            # database credential. Never allow that credential to cross into
            # production, even when the database host itself is remote.
            for name, value in database_urls.items():
                parsed = urlparse(value)
                if parsed.username == "aiep" and parsed.password == "aiep":
                    raise ValueError(f"{name} must not use the default E2E database credentials in production")

            # AI must not silently fall back to a local HTTP endpoint in production.
            if not self.local_production_allow_http and urlparse(self.lm_studio_base_url).scheme != "https":
                raise ValueError("LM_STUDIO_BASE_URL must use HTTPS in production")

            # External integrations must not redirect users or callbacks over plaintext HTTP.
            if not self.local_production_allow_http:
                if self.stripe_secret_key or self.stripe_webhook_secret:
                    for name, value in {
                        "STRIPE_CHECKOUT_SUCCESS_URL": self.stripe_checkout_success_url,
                        "STRIPE_CHECKOUT_CANCEL_URL": self.stripe_checkout_cancel_url,
                        "STRIPE_PORTAL_RETURN_URL": self.stripe_portal_return_url,
                    }.items():
                        if urlparse(value).scheme != "https":
                            raise ValueError(f"{name} must use HTTPS in production")

                if self.shopify_client_id or self.shopify_client_secret:
                    if urlparse(self.shopify_redirect_uri).scheme != "https":
                        raise ValueError("SHOPIFY_REDIRECT_URI must use HTTPS in production")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: Any) -> Any:
        """Accept JSON list or comma-separated string from env."""
        defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://172.18.0.1:3000",
            "http://host.docker.internal:3000",
        ]
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return defaults
            if s.startswith("["):
                return v
            return [part.strip() for part in s.split(",") if part.strip()]
        return v

    platform_admin_emails: List[str] = []
    storage_dir: str = "./var/storage"
    ai_default_provider: str = "lm_studio"
    ai_default_model: str = "google/gemma-4-e4b"
    ai_embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    anthropic_api_key: str | None = None
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    lm_studio_api_key: str | None = None
    ai_max_tool_iterations: int = 4
    ai_autonomy_max_steps: int = 6
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_starttls: bool = True
    frontend_base_url: str = "http://localhost:3000"
    password_reset_token_expire_minutes: int = 30
    password_reset_rate_limit: int = 5
    password_reset_rate_window_minutes: int = 15
    smtp_allowed_recipient_domains: List[str] = []
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    rate_limit_fail_closed: bool = False
    webhook_rate_limit_requests: int = 30
    webhook_rate_limit_window_seconds: int = 60
    webhook_max_payload_bytes: int = 262144
    webhook_replay_window_seconds: int = 300
    outbox_max_attempts: int = 8
    otel_enabled: bool = True
    otel_service_name: str = "ai-employee-platform"
    otel_exporter_endpoint: str | None = None
    billing_webhook_secret: str | None = None
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_map: dict[str, str] = {}
    stripe_checkout_success_url: str = "http://localhost:3000/billing?checkout=success"
    stripe_checkout_cancel_url: str = "http://localhost:3000/billing?checkout=cancelled"
    stripe_portal_return_url: str = "http://localhost:3000/billing"
    stripe_trial_days: int = 14
    shopify_client_id: str | None = None
    shopify_client_secret: str | None = None
    shopify_redirect_uri: str = "http://localhost:8000/api/v1/commerce-integrations/shopify/callback"
    shopify_scopes: str = "read_products,read_inventory,read_orders,read_customers,write_orders"
    shopify_api_version: str = "2026-07"
    frontend_app_url: str = "http://localhost:3000"

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.stripe_secret_key and self.stripe_webhook_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
