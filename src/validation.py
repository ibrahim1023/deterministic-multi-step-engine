"""Validation helpers for deterministic schemas."""

from __future__ import annotations

import re
from typing import Any, Mapping

from src.looping import parse_loop_config
from src.schemas import parse_problem_spec


_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate_semver(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not _SEMVER_RE.match(value):
        raise ValueError(f"{field} must be a semantic version (MAJOR.MINOR.PATCH)")


def validate_iso8601_utc(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not _ISO_UTC_RE.match(value):
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp ending with Z")


def validate_non_empty_str(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def validate_optional_str_list(value: Any, *, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} must contain non-empty strings")


def validate_problem_spec(problem_spec: Mapping[str, Any]) -> None:
    if not isinstance(problem_spec, Mapping):
        raise ValueError("problem_spec must be an object")
    parse_problem_spec(problem_spec)
    parse_loop_config(problem_spec)
