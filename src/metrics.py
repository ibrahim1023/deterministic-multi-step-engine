"""Trace metrics aggregation for evaluation dashboards."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping


def _parse_iso8601_utc(value: str | None) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _duration_ms(start: datetime | None, end: datetime | None) -> int | None:
    if not start or not end:
        return None
    return int((end - start).total_seconds() * 1000)


def aggregate_trace_metrics(trace: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    step_counts: Dict[str, int] = {}
    step_status_counts: Dict[str, int] = {}
    control_counts: Dict[str, int] = {}
    action_counts: Dict[str, int] = {}
    total_steps = 0
    total_controls = 0
    total_duration_ms = 0
    max_step_duration_ms = 0
    first_start: datetime | None = None
    last_finish: datetime | None = None

    for record in trace:
        record_type = record.get("type")
        if record_type == "step":
            total_steps += 1
            result = record.get("result") if isinstance(record.get("result"), Mapping) else {}
            step_name = result.get("step") or "unknown"
            step_counts[step_name] = step_counts.get(step_name, 0) + 1
            status = result.get("status") or "unknown"
            step_status_counts[status] = step_status_counts.get(status, 0) + 1

            started = _parse_iso8601_utc(result.get("started_at"))
            finished = _parse_iso8601_utc(result.get("finished_at"))
            duration = _duration_ms(started, finished)
            if duration is not None:
                total_duration_ms += duration
                if duration > max_step_duration_ms:
                    max_step_duration_ms = duration
            if started and (first_start is None or started < first_start):
                first_start = started
            if finished and (last_finish is None or finished > last_finish):
                last_finish = finished
        elif record_type == "control":
            total_controls += 1
            control_type = record.get("control_type") or "unknown"
            control_counts[control_type] = control_counts.get(control_type, 0) + 1
            action = record.get("action") or "unknown"
            action_counts[action] = action_counts.get(action, 0) + 1

    overall_duration_ms = _duration_ms(first_start, last_finish) or 0

    return {
        "steps_total": total_steps,
        "step_counts": step_counts,
        "step_status_counts": step_status_counts,
        "controls_total": total_controls,
        "control_counts": control_counts,
        "control_action_counts": action_counts,
        "total_step_duration_ms": total_duration_ms,
        "max_step_duration_ms": max_step_duration_ms,
        "trace_duration_ms": overall_duration_ms,
    }
