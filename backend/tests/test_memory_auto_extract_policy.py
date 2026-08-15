import pytest
from app.memory.auto_extract import auto_memory_settings
from app.core.exceptions import ValidationAppError


def test_auto_memory_candidate_limits_are_bounded():
    with pytest.raises(ValidationAppError):
        auto_memory_settings({"memory": {"enabled": True, "auto_extract": True, "max_candidates": 11}})
    with pytest.raises(ValidationAppError):
        auto_memory_settings({"memory": {"enabled": True, "auto_extract": True, "dedup_threshold": 0.5}})
