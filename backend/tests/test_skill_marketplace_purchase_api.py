from app.api.v1.skill_marketplace import router


def test_marketplace_purchase_route_is_static_before_publication_id_route():
    routes = [route.path for route in router.routes if hasattr(route, "path")]
    assert "/purchases" in routes
    assert "/{publication_id}" in routes
    assert routes.index("/purchases") < routes.index("/{publication_id}")


def test_marketplace_purchase_schema_is_explicit():
    from app.schemas.skill_marketplace_purchase import SkillMarketplacePurchaseCreate

    fields = SkillMarketplacePurchaseCreate.model_fields
    assert set(fields) == {"publication_id", "employee_id", "idempotency_key"}
    assert fields["idempotency_key"].is_required()
