import json

from app.memory.auto_extract import _parse_candidates, auto_memory_settings


def test_auto_memory_settings_requires_explicit_opt_in():
    assert auto_memory_settings({"memory": {"enabled": True}})["enabled"] is False
    cfg = auto_memory_settings({"memory": {"enabled": True, "auto_extract": True}})
    assert cfg["enabled"] is True
    assert cfg["max_candidates"] == 5
    assert cfg["min_importance"] == 3


def test_parse_candidates_accepts_json_fence_and_filters_noise():
    payload = {
        "memories": [
            {"memory_type": "preference", "content": "User prefers concise answers.", "importance": 4},
            {"memory_type": "fact", "content": "password=secret", "importance": 5},
            {"memory_type": "unknown", "content": "ignore", "importance": 5},
            {"memory_type": "fact", "content": "", "importance": 5},
        ]
    }
    items = _parse_candidates("```json\n" + json.dumps(payload) + "\n```", 5, 3)
    assert len(items) == 1
    assert items[0]["memory_type"] == "preference"
