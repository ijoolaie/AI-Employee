from types import SimpleNamespace

from app.services.shopify_service import normalize_shop_domain, webhook_matches_integration


def test_normalize_shop_domain_canonicalizes_scheme_and_case():
    assert normalize_shop_domain("HTTPS://Example-Shop.MyShopify.com/") == "example-shop.myshopify.com"


def test_webhook_matches_configured_integration_shop():
    integration = SimpleNamespace(config={"shop_domain": "example-shop.myshopify.com"})

    assert webhook_matches_integration(integration, "https://EXAMPLE-SHOP.myshopify.com/") is True


def test_webhook_rejects_missing_or_different_shop():
    integration = SimpleNamespace(config={"shop_domain": "tenant-a.myshopify.com"})

    assert webhook_matches_integration(integration, None) is False
    assert webhook_matches_integration(integration, "tenant-b.myshopify.com") is False
