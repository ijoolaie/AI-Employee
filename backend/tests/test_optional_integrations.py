from app.core.config import Settings


def test_paid_integrations_are_optional_for_ci_and_first_install():
    settings = Settings(
        app_env="production",
        debug=False,
        secret_key="ci-only-secret-key-012345678901234567890123456789",
        database_url="postgresql+asyncpg://ci:ci@postgres:5432/app",
        database_url_sync="postgresql://ci:ci@postgres:5432/app",
        redis_url="redis://redis:6379/0",
        celery_broker_url="redis://redis:6379/1",
        celery_result_backend="redis://redis:6379/2",
        cors_origins=["https://ci.example.test"],
        frontend_base_url="https://ci.example.test",
        frontend_app_url="https://ci.example.test",
        lm_studio_base_url="https://ai.example.test/v1",
        rate_limit_enabled=True,
        rate_limit_fail_closed=True,
        stripe_secret_key=None,
        stripe_webhook_secret=None,
        shopify_client_id=None,
        shopify_client_secret=None,
    )

    assert settings.stripe_enabled is False
    assert settings.shopify_client_id is None
    assert settings.shopify_client_secret is None
