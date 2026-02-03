"""Deterministic execution runner for the core steps."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from src.execution import build_linear_graph, validate_unique_steps
from src.invariants import validate_state
from src.routing import ensure_steps_known, resolve_steps
from src.steps import decompose, normalize, verify
from src.trace import create_trace_header, create_trace_step
from src.validation import validate_iso8601_utc, validate_problem_spec, validate_semver


ENGINE_VERSION = "0.1.0"
TRACE_VERSION = "1.0.0"
STATE_VERSION = "1.0.0"


State = Dict[str, Any]
Record = Dict[str, Any]


_STEP_HANDLERS = {
    "Normalize": normalize,
    "Decompose": decompose,
    "Verify": verify,
}


@dataclass(frozen=True)
class ExecutionResult:
    trace_id: str
    engine_version: str
    trace: List[Record]
    final_state: State


def _copy_state(state: Mapping[str, Any]) -> State:
    return copy.deepcopy(dict(state))


def _ensure_failed_state(state: State, result: Mapping[str, Any], *, now: str) -> State:
    next_state = _copy_state(state)
    next_state["status"] = "failed"
    errors = list(next_state.get("errors") or [])
    if result.get("errors"):
        errors.extend(result.get("errors") or [])
    if errors:
        next_state["errors"] = errors
    metadata = dict(next_state.get("metadata") or {})
    metadata["updated_at"] = now
    next_state["metadata"] = metadata
    return next_state


def _ensure_completed_state(state: State, *, now: str) -> State:
    next_state = _copy_state(state)
    next_state["status"] = "completed"
    metadata = dict(next_state.get("metadata") or {})
    metadata["updated_at"] = now
    next_state["metadata"] = metadata
    return next_state


def _resolve_steps(problem_spec: Mapping[str, Any]) -> List[str]:
    steps = resolve_steps(problem_spec)
    ensure_steps_known(steps, _STEP_HANDLERS.keys())
    validate_unique_steps(steps)
    build_linear_graph(steps)
    return list(steps)


def _initial_state(problem_spec: Mapping[str, Any], *, trace_id: str, now: str) -> State:
    inputs = problem_spec.get("inputs") or {}
    settings = problem_spec.get("settings") if isinstance(problem_spec.get("settings"), dict) else {}
    state: State = {
        "version": STATE_VERSION,
        "problem": _copy_state(problem_spec),
        "step_index": 0,
        "status": "pending",
        "artifacts": {},
        "assumptions": [],
        "constraints": list(inputs.get("constraints") or []),
        "errors": [],
        "metadata": {
            "trace_id": trace_id,
            "policy_profile": settings.get("policy_profile"),
            "model_profile": settings.get("model_profile"),
            "created_at": problem_spec.get("created_at"),
            "updated_at": now,
        },
    }
    validate_state(state)
    return state


def execute_problem(
    problem_spec: Mapping[str, Any],
    *,
    trace_id: str | None = None,
    engine_version: str | None = None,
    now: str | None = None,
) -> ExecutionResult:
    validate_problem_spec(problem_spec)
    engine_version = engine_version or ENGINE_VERSION
    validate_semver(engine_version, field="engine_version")

    now_value = now or problem_spec.get("created_at")
    validate_iso8601_utc(now_value, field="now")

    trace_id_value = trace_id or str(problem_spec.get("id"))

    steps = _resolve_steps(problem_spec)
    settings = problem_spec.get("settings") if isinstance(problem_spec.get("settings"), dict) else {}
    max_steps = settings.get("max_steps")
    if max_steps is not None and max_steps < len(steps):
        raise ValueError("settings.max_steps is lower than resolved step count")

    state = _initial_state(problem_spec, trace_id=trace_id_value, now=now_value)
    trace: List[Record] = []

    header = create_trace_header(
        version=TRACE_VERSION,
        trace_id=trace_id_value,
        created_at=now_value,
        engine_version=engine_version,
        problem_spec=problem_spec,
        initial_state=state,
    )
    trace.append(header)

    prev_hash = header["record_hash"]
    index = 1
    failed = False

    for step_name in steps:
        state_before = _copy_state(state)
        step_fn = _STEP_HANDLERS[step_name]
        state_after, result = step_fn(state_before, now=now_value)
        if result.get("status") == "failed":
            failed = True
            state_after = _ensure_failed_state(state_after, result, now=now_value)

        record = create_trace_step(
            index=index,
            step_index=state_before.get("step_index", 0),
            result=result,
            state_before=state_before,
            state_after=state_after,
            prev_hash=prev_hash,
        )
        trace.append(record)
        prev_hash = record["record_hash"]
        index += 1
        state = state_after
        if failed:
            break

    if not failed and state.get("status") == "running":
        state = _ensure_completed_state(state, now=now_value)

    return ExecutionResult(
        trace_id=trace_id_value,
        engine_version=engine_version,
        trace=trace,
        final_state=state,
    )


def list_known_steps() -> Iterable[str]:
    return sorted(_STEP_HANDLERS.keys())
