from pathlib import Path

import pytest

from src.determinism_ci import assert_no_trace_diff, trace_diff


def test_trace_diff_empty_for_identical_files(tmp_path: Path) -> None:
    a = tmp_path / "a.ndjson"
    b = tmp_path / "b.ndjson"
    payload = '{"x":1}\n'
    a.write_text(payload, encoding="utf-8")
    b.write_text(payload, encoding="utf-8")

    assert trace_diff(a, b) == ""
    assert_no_trace_diff(a, b)


def test_trace_diff_reports_changes(tmp_path: Path) -> None:
    a = tmp_path / "a.ndjson"
    b = tmp_path / "b.ndjson"
    a.write_text('{"x":1}\n', encoding="utf-8")
    b.write_text('{"x":2}\n', encoding="utf-8")

    diff = trace_diff(a, b)
    assert '-{"x":1}' in diff
    assert '+{"x":2}' in diff
    with pytest.raises(AssertionError):
        assert_no_trace_diff(a, b)
