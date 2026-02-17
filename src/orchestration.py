"""Orchestration adapters for deterministic execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

from src.execution import build_linear_graph, validate_unique_steps
from src.routing import ensure_steps_known, resolve_steps
from src.steps import (
    acquire_evidence,
    audit,
    compute,
    decompose,
    normalize,
    synthesize,
    verify,
)
from src.validation import validate_problem_spec


State = Dict[str, Any]


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
class OrchestrationPlan:
    framework: str
    steps: List[str]


def build_orchestration_plan(problem_spec: Mapping[str, Any]) -> OrchestrationPlan:
    validate_problem_spec(problem_spec)
    settings = (
        dict(problem_spec.get("settings") or {})
        if isinstance(problem_spec.get("settings"), dict)
        else {}
    )
    framework = settings.get("orchestration_framework") or "native"
    if framework not in {"native", "langgraph"}:
        raise ValueError(
            "problem_spec.settings.orchestration_framework must be native or langgraph"
        )
    steps = resolve_steps(problem_spec)
    ensure_steps_known(steps, _STEP_HANDLERS.keys())
    validate_unique_steps(steps)
    build_linear_graph(steps)
    return OrchestrationPlan(framework=framework, steps=list(steps))


def compile_langgraph_plan(steps: Iterable[str]) -> Any:
    """Compile a LangGraph state graph for deterministic linear execution."""
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "langgraph is required for LangGraph orchestration. Install langgraph first."
        ) from exc

    steps_list = list(steps)
    if not steps_list:
        raise ValueError("steps cannot be empty")

    graph = StateGraph(dict)
    for step_name in steps_list:
        graph.add_node(step_name, lambda state, _name=step_name: state)

    graph.set_entry_point(steps_list[0])
    for current, nxt in zip(steps_list, steps_list[1:]):
        graph.add_edge(current, nxt)
    graph.add_edge(steps_list[-1], END)
    return graph.compile()
