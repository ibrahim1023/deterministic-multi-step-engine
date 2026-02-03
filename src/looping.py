"""Loop configuration and deterministic stop evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_ALLOWED_STOP_VALUE_TYPES = (str, int, bool)
_ALLOWED_OPERATORS = {"equals", "not_equals", "gt", "gte", "lt", "lte"}


@dataclass(frozen=True)
class LoopConfig:
    start_step: str
    end_step: str
    max_iterations: int
    stop_path: str
    stop_operator: str
    stop_value: Any


@dataclass(frozen=True)
class LoopBounds:
    start_index: int
    end_index: int

    @property
    def segment_length(self) -> int:
        return self.end_index - self.start_index + 1


def _require_non_empty_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def parse_loop_config(problem_spec: Mapping[str, Any]) -> LoopConfig | None:
    settings = problem_spec.get("settings")
    if settings is None:
        return None
    if not isinstance(settings, Mapping):
        raise ValueError("problem_spec.settings must be an object")

    loop_settings = settings.get("loop")
    if loop_settings is None:
        return None
    if not isinstance(loop_settings, Mapping):
        raise ValueError("problem_spec.settings.loop must be an object")

    enabled = loop_settings.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(
            "problem_spec.settings.loop.enabled must be a boolean")
    if not enabled:
        return None

    start_step = _require_non_empty_str(
        loop_settings.get("start_step"), field="problem_spec.settings.loop.start_step"
    )
    end_step = _require_non_empty_str(
        loop_settings.get("end_step"), field="problem_spec.settings.loop.end_step"
    )
    max_iterations = loop_settings.get("max_iterations")
    if not isinstance(max_iterations, int) or max_iterations <= 0:
        raise ValueError(
            "problem_spec.settings.loop.max_iterations must be > 0")

    stop_condition = loop_settings.get("stop_condition")
    if not isinstance(stop_condition, Mapping):
        raise ValueError(
            "problem_spec.settings.loop.stop_condition must be an object")
    stop_path = _require_non_empty_str(
        stop_condition.get("path"), field="problem_spec.settings.loop.stop_condition.path"
    )
    if not stop_path.startswith("artifacts."):
        raise ValueError(
            "problem_spec.settings.loop.stop_condition.path must start with 'artifacts.'"
        )
    has_equals = "equals" in stop_condition
    has_operator = "operator" in stop_condition
    has_value = "value" in stop_condition
    if has_equals and (has_operator or has_value):
        raise ValueError(
            "problem_spec.settings.loop.stop_condition must use either equals or operator/value"
        )
    if has_equals:
        stop_operator = "equals"
        stop_value = stop_condition.get("equals")
    else:
        stop_operator = _require_non_empty_str(
            stop_condition.get("operator"),
            field="problem_spec.settings.loop.stop_condition.operator",
        )
        if stop_operator not in _ALLOWED_OPERATORS:
            raise ValueError(
                "problem_spec.settings.loop.stop_condition.operator must be one of: "
                f"{sorted(_ALLOWED_OPERATORS)}"
            )
        stop_value = stop_condition.get("value")

    if stop_operator in {"gt", "gte", "lt", "lte"}:
        if not isinstance(stop_value, int) or isinstance(stop_value, bool):
            raise ValueError(
                "problem_spec.settings.loop.stop_condition.value must be an integer for comparison operators"
            )
    else:
        if not isinstance(stop_value, _ALLOWED_STOP_VALUE_TYPES):
            raise ValueError(
                "problem_spec.settings.loop.stop_condition.value must be a string, integer, or boolean"
            )

    return LoopConfig(
        start_step=start_step,
        end_step=end_step,
        max_iterations=max_iterations,
        stop_path=stop_path,
        stop_operator=stop_operator,
        stop_value=stop_value,
    )


def resolve_loop_bounds(steps: list[str], config: LoopConfig) -> LoopBounds:
    try:
        start_index = steps.index(config.start_step)
    except ValueError as exc:
        raise ValueError(
            f"loop start_step '{config.start_step}' not found in steps") from exc
    try:
        end_index = steps.index(config.end_step)
    except ValueError as exc:
        raise ValueError(
            f"loop end_step '{config.end_step}' not found in steps") from exc
    if start_index > end_index:
        raise ValueError("loop start_step must appear before end_step")
    return LoopBounds(start_index=start_index, end_index=end_index)


def resolve_path(payload: Mapping[str, Any], path: str) -> Any:
    current: Any = payload
    for segment in path.split("."):
        if not isinstance(current, Mapping) or segment not in current:
            return None
        current = current[segment]
    return current


def stop_condition_met(state: Mapping[str, Any], config: LoopConfig) -> bool:
    value = resolve_path(state, config.stop_path)
    if value is None:
        return False
    operator = config.stop_operator
    target = config.stop_value
    if operator == "equals":
        return value == target
    if operator == "not_equals":
        return value != target
    if operator == "gt":
        return isinstance(value, int) and not isinstance(value, bool) and value > target
    if operator == "gte":
        return isinstance(value, int) and not isinstance(value, bool) and value >= target
    if operator == "lt":
        return isinstance(value, int) and not isinstance(value, bool) and value < target
    if operator == "lte":
        return isinstance(value, int) and not isinstance(value, bool) and value <= target
    return False
