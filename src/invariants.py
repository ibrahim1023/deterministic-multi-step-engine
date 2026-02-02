"""Invariant validation for core schemas."""

from __future__ import annotations

from typing import Any, Mapping


_ALLOWED_STATE_STATUS = {"pending", "running", "failed", "completed"}
_ALLOWED_STEP_STATUS = {"success", "failed", "skipped"}


def validate_state(state: Mapping[str, Any]) -> None:
    if "step_index" not in state:
        raise ValueError("ReasoningState.step_index is required")
    step_index = state.get("step_index")
    if not isinstance(step_index, int) or step_index < 0:
        raise ValueError(
            "ReasoningState.step_index must be a non-negative integer")

    if "status" not in state:
        raise ValueError("ReasoningState.status is required")
    status = state.get("status")
    if status not in _ALLOWED_STATE_STATUS:
        raise ValueError(
            f"ReasoningState.status must be one of: {sorted(_ALLOWED_STATE_STATUS)}")

    artifacts = state.get("artifacts")
    if artifacts is not None and not isinstance(artifacts, dict):
        raise ValueError(
            "ReasoningState.artifacts must be an object when provided")

    metadata = state.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError(
            "ReasoningState.metadata must be an object when provided")


def validate_step_result(result: Mapping[str, Any]) -> None:
    required = [
        "version",
        "step",
        "status",
        "input_hash",
        "output_hash",
        "started_at",
        "finished_at",
    ]
    missing = [key for key in required if key not in result]
    if missing:
        raise ValueError(f"StepResult missing required fields: {missing}")

    status = result.get("status")
    if status not in _ALLOWED_STEP_STATUS:
        raise ValueError(
            f"StepResult.status must be one of: {sorted(_ALLOWED_STEP_STATUS)}")

    has_output = "output" in result
    has_errors = "errors" in result
    if status == "success" and not has_output:
        raise ValueError("StepResult.success requires output")
    if status == "failed" and not has_errors:
        raise ValueError("StepResult.failed requires errors")
    if status == "skipped" and (has_output or has_errors):
        raise ValueError(
            "StepResult.skipped must not include output or errors")
