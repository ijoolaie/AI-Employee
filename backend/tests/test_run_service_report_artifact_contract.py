from pathlib import Path


def test_run_output_preserves_dict_report_artifacts():
    source = (
        Path(__file__).parents[1] / "app/services/run_service.py"
    ).read_text(encoding="utf-8")

    assert 'isinstance(last_tool_result.get("report_artifacts"), (dict, list))' in source
    assert 'output_data["report_artifacts"] = last_tool_result["report_artifacts"]' in source
