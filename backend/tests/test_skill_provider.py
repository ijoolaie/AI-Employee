import pytest

from app.services.skill_provider import (
    HttpSkillProvider,
    SkillProviderError,
    UnconfiguredSkillProvider,
    get_skill_provider,
)


def test_skill_provider_defaults_to_fail_closed_none():
    provider = UnconfiguredSkillProvider()
    assert provider.name == "none"
    assert provider.external_execution is False


def test_skill_provider_names_are_explicit():
    assert get_skill_provider("none").name == "none"
    assert get_skill_provider("http").name == "http"


def test_unknown_skill_provider_fails_closed():
    with pytest.raises(ValueError, match="Unknown skill provider"):
        get_skill_provider("shell")


def test_http_skill_provider_is_external():
    assert HttpSkillProvider.external_execution is True


@pytest.mark.parametrize("payload", ["x", [], None])
def test_skill_provider_response_shape_is_object(monkeypatch, payload):
    import json
    from app.core import config

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit): return json.dumps(payload).encode()

    class Opener:
        def open(self, request, timeout): return Response()

    monkeypatch.setattr("app.services.skill_provider.build_opener", lambda *args: Opener())
    settings = config.get_settings()
    monkeypatch.setattr(settings, "skill_provider_name", "http")
    monkeypatch.setattr(settings, "skill_provider_base_url", "https://provider.example.test/execute")
    monkeypatch.setattr(settings, "skill_provider_api_key", "test-key")
    with pytest.raises(SkillProviderError, match="response must be a JSON object"):
        HttpSkillProvider().execute(
            tenant_id="tenant",
            employee_id="employee",
            skill_package_id="skill",
            skill_slug="slug",
            skill_version=1,
            input_data={},
            request_id="req-1",
        )
