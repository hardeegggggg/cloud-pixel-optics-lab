import json

import pytest

from pixelcloud.batch_runner import load_case, result_location


@pytest.mark.xfail(reason="ISSUE-001: replace raw IndexError with a domain error", strict=True)
def test_invalid_array_index_has_actionable_error(tmp_path) -> None:
    cases = tmp_path / "cases.jsonl"
    cases.write_text(json.dumps({"case_id": "only"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="array index"):
        load_case(str(cases), 4)


@pytest.mark.xfail(reason="ISSUE-002: destination must include run_id", strict=True)
def test_result_location_keeps_runs_separate() -> None:
    first = result_location("case-001", "output", None)
    second = result_location("case-001", "output", None)
    assert first != second

