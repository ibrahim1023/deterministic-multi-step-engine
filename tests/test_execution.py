import pytest

from src.execution import ExecutionGraph, build_linear_graph, validate_unique_steps


def test_build_linear_graph() -> None:
    graph = build_linear_graph(["Normalize", "Decompose", "Verify"])
    assert isinstance(graph, ExecutionGraph)
    assert graph.steps == ["Normalize", "Decompose", "Verify"]
    assert graph.next_step("Normalize") == "Decompose"
    assert graph.next_step("Verify") is None
    assert graph.is_terminal("Verify") is True


def test_build_linear_graph_empty() -> None:
    with pytest.raises(ValueError):
        build_linear_graph([])


def test_validate_unique_steps() -> None:
    validate_unique_steps(["Normalize", "Decompose"])
    with pytest.raises(ValueError):
        validate_unique_steps(["Normalize", "Normalize"])
