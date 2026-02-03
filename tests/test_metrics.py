from src.engine import execute_problem
from src.metrics import aggregate_trace_metrics


def test_aggregate_trace_metrics_counts_steps() -> None:
    spec = {
        "version": "1.0.0",
        "id": "req-metrics-1",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "Metrics test"},
    }
    result = execute_problem(spec, now=spec["created_at"])
    metrics = aggregate_trace_metrics(result.trace)
    assert metrics["steps_total"] == 7
    assert metrics["step_counts"]["Normalize"] == 1
    assert metrics["step_status_counts"]["success"] == 7
    assert metrics["controls_total"] == 0
    assert metrics["trace_duration_ms"] >= 0


def test_aggregate_trace_metrics_counts_controls() -> None:
    spec = {
        "version": "1.0.0",
        "id": "req-metrics-2",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "Metrics test"},
        "settings": {
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
            }
        },
    }
    result = execute_problem(spec, now=spec["created_at"])
    metrics = aggregate_trace_metrics(result.trace)
    assert metrics["controls_total"] == 1
    assert metrics["control_counts"]["loop"] == 1
    assert metrics["control_action_counts"]["stop"] == 1
