"""Determinism CI helpers for trace diffing."""

from __future__ import annotations

import difflib
from pathlib import Path


def trace_diff(expected_path: str | Path, actual_path: str | Path) -> str:
    expected = Path(expected_path).read_text(encoding="utf-8").splitlines(keepends=True)
    actual = Path(actual_path).read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            expected,
            actual,
            fromfile=str(expected_path),
            tofile=str(actual_path),
        )
    )


def assert_no_trace_diff(expected_path: str | Path, actual_path: str | Path) -> None:
    diff = trace_diff(expected_path, actual_path)
    if diff:
        raise AssertionError(f"Determinism regression detected:\n{diff}")
