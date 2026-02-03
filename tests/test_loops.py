import pytest

from src.engine import execute_problem


def _base_spec() -> dict:
    return {
        "version": "1.0.0",
        "id": "req-loop-1",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {
            "prompt": "Check loop behavior",
        },
    }


def _step_names(result) -> list[str]:
    return [record["result"]["step"] for record in result.trace if record["type"] == "step"]


def _control_actions(result) -> list[str]:
    return [record["action"] for record in result.trace if record["type"] == "control"]


def test_loop_stops_when_condition_met() -> None:
    spec = _base_spec()
    spec["settings"] = {
        "loop": {
            "enabled": True,
            "start_step": "AcquireEvidence",
            "end_step": "Verify",
            "max_iterations": 3,
            "stop_condition": {
                "path": "artifacts.verification.status",
                "operator": "equals",
                "value": "passed",
            },
        }
    }

    result = execute_problem(spec, now=spec["created_at"])

    assert result.final_state["status"] == "completed"
    assert _step_names(result) == [
        "Normalize",
        "Decompose",
        "AcquireEvidence",
        "Compute",
        "Verify",
        "Synthesize",
        "Audit",
    ]
    assert _control_actions(result) == ["stop"]


def test_loop_repeats_until_max_iterations_then_fails() -> None:
    spec = _base_spec()
    spec["settings"] = {
        "evidence_required": True,
        "loop": {
            "enabled": True,
            "start_step": "AcquireEvidence",
            "end_step": "Verify",
            "max_iterations": 2,
            "stop_condition": {
                "path": "artifacts.verification.status",
                "operator": "equals",
                "value": "passed",
            },
        },
    }

    result = execute_problem(spec, now=spec["created_at"])

    assert result.final_state["status"] == "failed"
    assert _step_names(result) == [
        "Normalize",
        "Decompose",
        "AcquireEvidence",
        "Compute",
        "Verify",
        "AcquireEvidence",
        "Compute",
        "Verify",
    ]
    assert _control_actions(result) == ["repeat", "max_iterations_reached"]
    assert any(
        error.get("code") == "loop_max_iterations_reached"
        for error in result.final_state.get("errors", [])
    )


def test_loop_stop_condition_comparison_operator() -> None:
    spec = _base_spec()
    spec["settings"] = {
        "loop": {
            "enabled": True,
            "start_step": "AcquireEvidence",
            "end_step": "Verify",
            "max_iterations": 2,
            "stop_condition": {
                "path": "artifacts.verification.checks.task_count",
                "operator": "gte",
                "value": 1,
            },
        },
    }

    result = execute_problem(spec, now=spec["created_at"])

    assert result.final_state["status"] == "completed"
    assert _control_actions(result) == ["stop"]


def test_loop_max_steps_validation() -> None:
    spec = _base_spec()
    spec["settings"] = {
        "max_steps": 5,
        "loop": {
            "enabled": True,
            "start_step": "AcquireEvidence",
            "end_step": "Verify",
            "max_iterations": 2,
            "stop_condition": {
                "path": "artifacts.verification.status",
                "equals": "passed",
            },
        },
    }

    with pytest.raises(ValueError):
        execute_problem(spec, now=spec["created_at"])
