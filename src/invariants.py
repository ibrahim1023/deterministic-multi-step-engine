"""Invariant validation for core schemas."""

from __future__ import annotations

from typing import Any, Mapping

from src.schemas import parse_reasoning_state, parse_step_result

def validate_state(state: Mapping[str, Any]) -> None:
    parse_reasoning_state(state)


def validate_step_result(result: Mapping[str, Any]) -> None:
    parse_step_result(result)
