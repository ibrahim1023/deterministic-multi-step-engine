import pytest

from src.engine import execute_problem


def _base_problem_spec() -> dict:
    return {
        "version": "1.0.0",
        "id": "req-engine-1",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "Hello"},
    }


def test_execute_problem_native_path() -> None:
    result = execute_problem(_base_problem_spec(), now="2026-02-02T00:00:00Z")
    assert result.final_state["status"] == "completed"


def test_execute_problem_langgraph_path() -> None:
    problem_spec = _base_problem_spec()
    problem_spec["settings"] = {"orchestration_framework": "langgraph"}
    try:
        result = execute_problem(problem_spec, now="2026-02-02T00:00:00Z")
    except RuntimeError:
        pytest.skip("langgraph is not installed in this environment")
    assert result.final_state["status"] == "completed"
