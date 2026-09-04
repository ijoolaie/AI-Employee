import json
import logging

from app.core.logging import JSONLogFormatter
from app.core.privacy import REDACTED


def test_json_logs_redact_sensitive_extra_fields():
    record = logging.LogRecord(
        name="security-test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.extra_context = {"authorization": "Bearer super-secret", "tenant": "tenant-a"}

    payload = json.loads(JSONLogFormatter().format(record))

    assert payload["extra_context"]["authorization"] == REDACTED
    assert payload["extra_context"]["tenant"] == "tenant-a"
