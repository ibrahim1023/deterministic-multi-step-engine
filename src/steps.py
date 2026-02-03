"""Core deterministic steps."""

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


def acquire_evidence(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Collect deterministic evidence from inputs/context (placeholder)."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    problem = dict(state.get("problem") or {})
    inputs = dict(problem.get("inputs") or {})
    settings = dict(problem.get("settings") or {}) if isinstance(
        problem.get("settings"), dict) else {}
    context = inputs.get("context") if isinstance(
        inputs.get("context"), dict) else {}
    evidence = context.get("evidence")
    evidence_list = evidence if isinstance(evidence, list) else []
    output = {
        "evidence": evidence_list,
        "evidence_required": bool(settings.get("evidence_required", False)),
        "evidence_count": len(evidence_list),
    }
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="evidence", artifact_value=output)
    result = _step_result(
        step="AcquireEvidence",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"evidence": evidence_list},
        output_payload=output,
    )
    validate_step_result(result)
    validate_state(next_state)
    return next_state, result


def compute(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Deterministic computation placeholder derived from tasks."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    artifacts = state.get("artifacts") or {}
    decomposition = artifacts.get("decomposition") or {}
    tasks = decomposition.get("tasks") or []
    task_count = len(tasks) if isinstance(tasks, list) else 0
    output = {"task_count": task_count, "status": "ok"}
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="computation", artifact_value=output)
    result = _step_result(
        step="Compute",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"tasks": tasks},
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
    evidence = artifacts.get("evidence") or {}
    evidence_count = evidence.get(
        "evidence_count") if isinstance(evidence, dict) else 0
    settings = dict((state.get("problem") or {}).get("settings") or {})
    evidence_required_default = bool(settings.get("evidence_required", False))
    base_checks = {
        "tasks_present": bool(tasks),
        "task_count": len(tasks) if isinstance(tasks, list) else 0,
        "evidence_present": bool(evidence_count),
    }
    verification_paths = settings.get("verification_paths")
    if isinstance(verification_paths, list) and verification_paths:
        paths_output = []
        for entry in verification_paths:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            evidence_required = entry.get("evidence_required")
            if evidence_required is None:
                evidence_required = evidence_required_default
            checks = dict(base_checks)
            checks["evidence_required"] = bool(evidence_required)
            passed = checks["tasks_present"] and (
                not checks["evidence_required"] or checks["evidence_present"])
            paths_output.append(
                {"name": name, "checks": checks, "status": "passed" if passed else "failed"}
            )
        aggregate_passed = all(
            path.get("status") == "passed" for path in paths_output
        )
        output = {
            "paths": paths_output,
            "aggregate": {
                "status": "passed" if aggregate_passed else "failed",
                "total": len(paths_output),
                "failed_count": sum(
                    1 for path in paths_output if path.get("status") != "passed"
                ),
            },
            "status": "passed" if aggregate_passed else "failed",
        }
    else:
        checks = dict(base_checks)
        checks["evidence_required"] = evidence_required_default
        passed = checks["tasks_present"] and (
            not checks["evidence_required"] or checks["evidence_present"])
        output = {"checks": checks, "status": "passed" if passed else "failed"}
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


def synthesize(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Deterministic synthesis placeholder derived from computation."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    computation = (state.get("artifacts") or {}).get("computation") or {}
    task_count = computation.get("task_count", 0)
    output = {"summary": f"Processed {task_count} task(s)."}
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="synthesis", artifact_value=output)
    result = _step_result(
        step="Synthesize",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"task_count": task_count},
        output_payload=output,
    )
    validate_step_result(result)
    validate_state(next_state)
    return next_state, result


def audit(state: Mapping[str, Any], *, now: str | None) -> Tuple[State, Result]:
    """Deterministic audit placeholder of final artifacts."""
    validate_state(state)
    started_at = _now_required(now)
    finished_at = started_at
    artifacts = state.get("artifacts") or {}
    output = {"artifact_keys": sorted(artifacts.keys()), "status": "ok"}
    next_state = _advance_state(
        state=state, now=finished_at, artifact_key="audit", artifact_value=output)
    result = _step_result(
        step="Audit",
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        input_payload={"artifact_keys": output["artifact_keys"]},
        output_payload=output,
    )
    validate_step_result(result)
    validate_state(next_state)
    return next_state, result
