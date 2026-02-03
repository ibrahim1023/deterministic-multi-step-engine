"""Deterministic routing policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Mapping


StepList = List[str]
PolicyFn = Callable[[Mapping[str, object]], StepList]


@dataclass(frozen=True)
class RoutingPolicy:
    name: str
    steps: StepList


class PolicyRegistry:
    """Deterministic policy registry with explicit ordering."""

    def __init__(self) -> None:
        self._policies: Dict[str, RoutingPolicy] = {}

    def register(self, policy: RoutingPolicy) -> None:
        if policy.name in self._policies:
            raise ValueError(f"Policy already registered: {policy.name}")
        self._policies[policy.name] = policy

    def get(self, name: str) -> RoutingPolicy:
        try:
            return self._policies[name]
        except KeyError as exc:
            raise KeyError(f"Unknown policy: {name}") from exc

    def list_names(self) -> List[str]:
        return sorted(self._policies.keys())


DEFAULT_POLICY = RoutingPolicy(
    name="default",
    steps=[
        "Normalize",
        "Decompose",
        "AcquireEvidence",
        "Compute",
        "Verify",
        "Synthesize",
        "Audit",
    ],
)


def default_registry() -> PolicyRegistry:
    registry = PolicyRegistry()
    registry.register(DEFAULT_POLICY)
    return registry


def select_policy_name(problem_spec: Mapping[str, object], fallback: str = "default") -> str:
    settings = problem_spec.get("settings") if isinstance(
        problem_spec, dict) else None
    if isinstance(settings, dict):
        value = settings.get("policy_profile")
        if isinstance(value, str) and value:
            return value
    return fallback


def resolve_steps(
    problem_spec: Mapping[str, object],
    registry: PolicyRegistry | None = None,
    fallback: str = "default",
) -> StepList:
    """Resolve deterministic step ordering for a problem spec."""
    registry = registry or default_registry()
    policy_name = select_policy_name(problem_spec, fallback=fallback)
    return list(registry.get(policy_name).steps)


def ensure_steps_known(steps: Iterable[str], known_steps: Iterable[str]) -> None:
    known = set(known_steps)
    unknown = [step for step in steps if step not in known]
    if unknown:
        raise ValueError(f"Unknown steps in policy: {unknown}")
