import pytest

from src.orchestration import build_orchestration_plan, compile_langgraph_plan


def test_build_orchestration_plan_defaults_to_native() -> None:
    spec = {
        "version": "1.0.0",
        "id": "req-orch-1",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "hello"},
    }
    plan = build_orchestration_plan(spec)
    assert plan.framework == "native"
    assert plan.steps[0] == "Normalize"


def test_build_orchestration_plan_rejects_unknown_framework() -> None:
    spec = {
        "version": "1.0.0",
        "id": "req-orch-2",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "hello"},
        "settings": {"orchestration_framework": "other"},
    }
    with pytest.raises(ValueError):
        build_orchestration_plan(spec)


def test_compile_langgraph_plan_compiles_when_available() -> None:
    try:
        compiled = compile_langgraph_plan(["Normalize", "Decompose"])
    except RuntimeError:
        pytest.skip("langgraph is not installed in this environment")
    assert hasattr(compiled, "invoke")
