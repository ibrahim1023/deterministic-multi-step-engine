"""Core deterministic steps: Normalize, Decompose, Verify."""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Mapping, Tuple

from src.invariants import validate_state, validate_step_result
from src.trace import hash_json


State = Dict[str, Any]
Result = Dict[str, Any]


_WHITESPACE_RE = re.compile(r"\s+")


def _now_required(now: str | None) -> str:
    if not now:
        raise ValueError("now timestamp is required for deterministic steps")
    return now


def _step_result(
    *,
    step: str,
    status: str,
    started_at: str,
    finished_at: str,
    input_payload: Mapping[str, Any],
    output_payload: Mapping[str, Any] | None = None,
    errors: List[Dict[str, str]] | None = None,
) -> Result:
    result: Result = {
        "version": "1.0.0",
        "step": step,
        "status": status,
        "input_hash": hash_json(input_payload),
        "output_hash": hash_json(output_payload or {}),
        "started_at": started_at,
        "finished_at": finished_at,
    }
    if status == "success":
        result["output"] = output_payload or {}
    if status == "failed":
        result["errors"] = errors or []
    return result


def _copy_state(state: Mapping[str, Any]) -> State:
    return copy.deepcopy(dict(state))


def _advance_state(state: State, *, now: str, artifact_key: str, artifact_value: Any) -> State:
    next_state = _copy_state(state)
    next_state["step_index"] = int(next_state.get("step_index", 0)) + 1
    next_state["status"] = "running"
    artifacts = dict(next_state.get("artifacts") or {})
    artifacts[artifact_key] = artifact_value
    next_state["artifacts"] = artifacts
    metadata = dict(next_state.get("metadata") or {})
    metadata["updated_at"] = now
    next_state["metadata"] = metadata
    return next_state


def normalize(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Normalize the input prompt (trim + collapse whitespace)."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    problem = dict(state.get("problem") or {})
    inputs = dict(problem.get("inputs") or {})
    prompt = inputs.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        result = _step_result(
            step="Normalize",
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            input_payload={"prompt": prompt},
            output_payload={},
            errors=[{"code": "invalid_prompt", "message": "prompt is required"}],
        )
        validate_step_result(result)
        next_state = _copy_state(state)
        validate_state(next_state)
        return next_state, result

    normalized_prompt = _WHITESPACE_RE.sub(" ", prompt).strip()
    output = {"normalized_prompt": normalized_prompt}
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="normalized", artifact_value=output)
    result = _step_result(
        step="Normalize",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"prompt": prompt},
        output_payload=output,
    )
    validate_step_result(result)
    validate_state(next_state)
    return next_state, result


def decompose(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Derive a deterministic list of tasks from goals or normalized prompt."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    problem = dict(state.get("problem") or {})
    inputs = dict(problem.get("inputs") or {})
    goals = inputs.get("goals") if isinstance(
        inputs.get("goals"), list) else []
    normalized = (state.get("artifacts") or {}).get("normalized") or {}
    base_prompt = normalized.get("normalized_prompt") or inputs.get("prompt")
    tasks = [goal for goal in goals if isinstance(goal, str) and goal.strip()]
    if not tasks:
        if isinstance(base_prompt, str) and base_prompt.strip():
            tasks = [base_prompt]
        else:
            tasks = ["unspecified task"]
    output = {"tasks": tasks}
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="decomposition", artifact_value=output)
    result = _step_result(
        step="Decompose",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"goals": goals, "prompt": base_prompt},
        output_payload=output,
    )
    validate_step_result(result)
    validate_state(next_state)
    return next_state, result


def verify(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Perform deterministic verification checks (placeholder)."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    artifacts = state.get("artifacts") or {}
    decomposition = artifacts.get("decomposition") or {}
    tasks = decomposition.get("tasks") or []
    checks = {
        "tasks_present": bool(tasks),
        "task_count": len(tasks) if isinstance(tasks, list) else 0,
    }
    output = {"checks": checks,
              "status": "passed" if checks["tasks_present"] else "failed"}
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="verification", artifact_value=output)
    result = _step_result(
        step="Verify",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"tasks": tasks},
        output_payload=output,
    )
    validate_step_result(result)
    validate_state(next_state)
    return next_state, result
