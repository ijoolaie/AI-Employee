# RC8 TESTFIX3 — LM Studio Provider Settings Fix

Date: 2026-08-12

## Fixed

`LMStudioProvider` previously captured `get_settings()` at module import time. In a Docker environment this could resolve `LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1` before tests monkeypatched `app.ai.providers.registry.get_settings`, causing the registry test to observe the wrong base URL.

The provider now resolves settings inside `__init__`, so runtime/test overrides are respected.

## Validation

The reported staging result was:

- 150 passed
- 1 failed

The single failure was `test_registry_defaults_to_lm_studio` and is addressed by this patch.

Local host-side validation of the full suite is not authoritative because the host environment does not include the container's `asyncpg` dependency. The authoritative validation remains `docker compose exec api pytest -q` after rebuilding the supplied image.
