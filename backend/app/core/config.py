"""Application settings — loaded from environment variables."""

from functools import lru_cache
from typing import Any, List

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

    # Dev-friendly defaults include common localhost + Docker Desktop bridge origins.
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.18.0.1:3000",
        "http://host.docker.internal:3000",
    ]

    @model_validator(mode="after")
    def validate_production_safety(self):
        """Fail fast on unsafe production configuration.

        Development/e2e environments keep their existing defaults. A real
        production deployment must opt into explicit secrets, HTTPS-oriented
        controls, and fail-closed rate limiting.
        """
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
                return v  # let pydantic parse JSON
            return [part.strip() for part in s.split(",") if part.strip()]
        return v
    # Explicit allowlist for platform-admin bootstrap tooling. Never inferred from tenant-admin status.
    platform_admin_emails: List[str] = []

    storage_dir: str = "./var/storage"

    # AI Gateway — provider-agnostic by design. Provider selection is handled
    # by app.ai.providers.registry; LM Studio is the development default.
    ai_default_provider: str = "lm_studio"
    ai_default_model: str = "google/gemma-4-e4b"
    ai_embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    anthropic_api_key: str | None = None
    lm_studio_base_url: str = "http://127.0.0.1:1234/v1"
    lm_studio_api_key: str | None = None

    # Controlled Tool execution boundary. A Run may perform only this many
    # model -> tool -> model iterations before failing closed.
    ai_max_tool_iterations: int = 4
    # Autonomous planner limits. Planning is still opt-in per EmployeeVersion rules.
    ai_autonomy_max_steps: int = 6

    # External email Tool integration. Real credentials remain in .env only.
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
    # Fail closed when the recipient-domain allowlist is empty.
    smtp_allowed_recipient_domains: List[str] = []

    # Security hardening
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    rate_limit_fail_closed: bool = False
    webhook_rate_limit_requests: int = 30
    webhook_rate_limit_window_seconds: int = 60
    webhook_max_payload_bytes: int = 262144
    webhook_replay_window_seconds: int = 300

    # Reliability / observability
    outbox_max_attempts: int = 8
    otel_enabled: bool = True
    otel_service_name: str = "ai-employee-platform"
    otel_exporter_endpoint: str | None = None

    # Billing webhook authentication. Fail closed when unset.
    billing_webhook_secret: str | None = None

    # Phase 6 — real payment-provider adapter (Stripe). Provider-neutral
    # billing_service.py / Subscription/BillingEvent models are unchanged;
    # this only supplies the Stripe-specific glue (Checkout, Billing
    # Portal, webhook signature verification). Unset by default — fails
    # closed (checkout/portal endpoints return a clear error, the webhook
    # route rejects all requests) until real keys are configured.
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None
    # plan_code -> Stripe Price ID, e.g. {"business": "price_123", "professional": "price_456"}.
    # Parsed from a JSON env var (STRIPE_PRICE_MAP='{"business":"price_123"}').
    stripe_price_map: dict[str, str] = {}
    stripe_checkout_success_url: str = "http://localhost:3000/billing?checkout=success"
    stripe_checkout_cancel_url: str = "http://localhost:3000/billing?checkout=cancelled"
    stripe_portal_return_url: str = "http://localhost:3000/billing"
    stripe_trial_days: int = 14

    # Shopify public-app OAuth / GraphQL connector.
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
