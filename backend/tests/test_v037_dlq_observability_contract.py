from pathlib import Path

def test_v037_contract_files_present():
    root=Path(__file__).parents[1]
    assert (root/"app/services/phase1_observability_service.py").exists()
    assert (root/"app/api/v1/operations.py").exists()
    assert any("f7c8d9e0a123" in p.read_text() for p in (root/"alembic/versions").glob("*.py"))

def test_v037_requirements():
    req=(Path(__file__).parents[1]/"requirements.txt").read_text()
    assert "prometheus-client" in req
    assert "opentelemetry-api" in req


def test_v037_metrics_endpoint_contract():
    main=(Path(__file__).parents[1]/"app/main.py").read_text()
    middleware=(Path(__file__).parents[1]/"app/core/middleware.py").read_text()
    assert '@app.get("/metrics")' in main
    assert 'HTTP_REQUESTS.labels' in middleware
    assert 'aiep_http_requests_total' in (Path(__file__).parents[1]/"app/core/metrics.py").read_text()

def test_v037_dlq_replay_contract():
    service=(Path(__file__).parents[1]/"app/services/outbox_service.py").read_text()
    api=(Path(__file__).parents[1]/"app/api/v1/operations.py").read_text()
    assert 'status = "dead"' in service
    assert 'async def replay' in service
    assert '/dead-letters/{message_id}/replay' in api
