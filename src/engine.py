"""Deterministic execution runner for the core steps."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from src.execution import build_linear_graph, validate_unique_steps
from src.invariants import validate_state
from src.looping import parse_loop_config, resolve_loop_bounds, stop_condition_met
from src.orchestration import build_orchestration_plan, compile_langgraph_plan
from src.routing import ensure_steps_known
from src.steps import (
    acquire_evidence,
    audit,
    compute,
    decompose,
    normalize,
    synthesize,
    verify,
)
from src.trace import create_trace_control, create_trace_header, create_trace_step
from src.validation import validate_iso8601_utc, validate_problem_spec, validate_semver


ENGINE_VERSION = "0.1.0"
TRACE_VERSION = "1.0.0"
STATE_VERSION = "1.0.0"


State = Dict[str, Any]
Record = Dict[str, Any]


_STEP_HANDLERS = {
    "Normalize": normalize,
    "Decompose": decompose,
    "AcquireEvidence": acquire_evidence,
    "Compute": compute,
    "Verify": verify,
    "Synthesize": synthesize,
    "Audit": audit,
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
    plan = build_orchestration_plan(problem_spec)
    steps = list(plan.steps)
    ensure_steps_known(steps, _STEP_HANDLERS.keys())
    validate_unique_steps(steps)
    build_linear_graph(steps)
    if plan.framework == "langgraph":
        compile_langgraph_plan(steps)
    return steps


def _initial_state(problem_spec: Mapping[str, Any], *, trace_id: str, now: str) -> State:
    inputs = problem_spec.get("inputs") or {}
    settings = problem_spec.get("settings") if isinstance(
        problem_spec.get("settings"), dict) else {}
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
    settings = problem_spec.get("settings") if isinstance(
        problem_spec.get("settings"), dict) else {}
    max_steps = settings.get("max_steps")
    loop_config = parse_loop_config(problem_spec)
    loop_bounds = resolve_loop_bounds(steps, loop_config) if loop_config else None
    max_required = len(steps)
    if loop_bounds and loop_config:
        max_required += (loop_config.max_iterations -
                         1) * loop_bounds.segment_length
    if max_steps is not None and max_steps < max_required:
        raise ValueError(
            "settings.max_steps is lower than required step count")

    state = _initial_state(
        problem_spec, trace_id=trace_id_value, now=now_value)
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

    step_cursor = 0
    loop_iteration = 0
    while step_cursor < len(steps):
        step_name = steps[step_cursor]
        if loop_bounds and step_cursor == loop_bounds.start_index and loop_iteration == 0:
            loop_iteration = 1
        state_before = _copy_state(state)
        step_fn = _STEP_HANDLERS[step_name]
        state_after, result = step_fn(state_before, now=now_value)
        if result.get("status") == "failed":
            failed = True
            state_after = _ensure_failed_state(
                state_after, result, now=now_value)
        next_cursor = step_cursor + 1
        loop_action = None
        loop_iteration_for_record = loop_iteration
        if (loop_bounds and loop_config
                and step_cursor == loop_bounds.end_index and loop_iteration > 0):
            if stop_condition_met(state_after, loop_config):
                loop_action = "stop"
                next_cursor = step_cursor + 1
            else:
                if loop_iteration < loop_config.max_iterations:
                    loop_action = "repeat"
                    next_cursor = loop_bounds.start_index
                    loop_iteration += 1
                else:
                    loop_action = "max_iterations_reached"
                    failed = True
                    error = {
                        "code": "loop_max_iterations_reached",
                        "message": (
                            "Loop stop condition not met after "
                            f"{loop_config.max_iterations} iteration(s)."
                        ),
                        "step": loop_config.end_step,
                    }
                    state_after = _ensure_failed_state(
                        state_after, {"errors": [error]}, now=now_value)

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
        if loop_action and loop_config:
            control = create_trace_control(
                index=index,
                control_type="loop",
                action=loop_action,
                loop_iteration=loop_iteration_for_record,
                start_step=loop_config.start_step,
                end_step=loop_config.end_step,
                stop_path=loop_config.stop_path,
                stop_operator=loop_config.stop_operator,
                stop_value=loop_config.stop_value,
                state=state,
                prev_hash=prev_hash,
            )
            trace.append(control)
            prev_hash = control["record_hash"]
            index += 1
        if failed:
            break
        step_cursor = next_cursor

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
