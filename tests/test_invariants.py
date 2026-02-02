import pytest

from src.invariants import validate_state, validate_step_result


def test_validate_state_requires_step_index_and_status() -> None:
    with pytest.raises(ValueError):
        validate_state({})

    with pytest.raises(ValueError):
        validate_state({"step_index": 0})

    validate_state({"step_index": 0, "status": "pending"})


def test_validate_state_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        validate_state({"step_index": -1, "status": "pending"})

    with pytest.raises(ValueError):
        validate_state({"step_index": 0, "status": "unknown"})


def test_validate_step_result_required_fields() -> None:
    with pytest.raises(ValueError):
        validate_step_result({"status": "success"})


def test_validate_step_result_status_constraints() -> None:
    base = {
        "version": "1.0.0",
        "step": "Normalize",
        "status": "success",
        "input_hash": "in",
        "output_hash": "out",
        "started_at": "2026-02-02T00:00:00Z",
        "finished_at": "2026-02-02T00:00:00Z",
    }
    with pytest.raises(ValueError):
        validate_step_result(base)

    success = dict(base)
    success["output"] = {"normalized_prompt": "ok"}
    validate_step_result(success)

    failed = dict(base)
    failed["status"] = "failed"
    failed["errors"] = [{"code": "x", "message": "y"}]
    validate_step_result(failed)

    skipped = dict(base)
    skipped["status"] = "skipped"
    validate_step_result(skipped)
