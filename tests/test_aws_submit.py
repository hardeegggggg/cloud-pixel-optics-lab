import pytest

from scripts.aws_submit import count_cases, safe_run_id


def test_count_cases_accepts_batch_array_range(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text("{}\n{}\n", encoding="utf-8")
    assert count_cases(path) == 2


def test_count_cases_rejects_single_case(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="between 2 and 10,000"):
        count_cases(path)


def test_safe_run_id_removes_unsafe_characters() -> None:
    assert safe_run_id("demo run/001") == "demo-run-001"

