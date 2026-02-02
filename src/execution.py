"""Execution graph for fixed step ordering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class ExecutionGraph:
    """Deterministic execution graph with a fixed linear order."""

    steps: List[str]

    def index_of(self, step: str) -> int:
        try:
            return self.steps.index(step)
        except ValueError as exc:
            raise KeyError(f"Unknown step: {step}") from exc

    def next_step(self, step: str) -> str | None:
        idx = self.index_of(step)
        if idx + 1 >= len(self.steps):
            return None
        return self.steps[idx + 1]

    def is_terminal(self, step: str) -> bool:
        return self.next_step(step) is None


def build_linear_graph(steps: Iterable[str]) -> ExecutionGraph:
    steps_list = list(steps)
    if not steps_list:
        raise ValueError("steps cannot be empty")
    return ExecutionGraph(steps=steps_list)


def validate_unique_steps(steps: Iterable[str]) -> None:
    seen: Dict[str, int] = {}
    duplicates = []
    for step in steps:
        seen[step] = seen.get(step, 0) + 1
        if seen[step] == 2:
            duplicates.append(step)
    if duplicates:
        raise ValueError(f"Duplicate steps in execution graph: {duplicates}")
