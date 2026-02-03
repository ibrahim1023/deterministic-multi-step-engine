import json

from src.trace import (
    canonical_json,
    compute_record_hash,
    create_trace_header,
    create_trace_control,
    create_trace_step,
    hash_json,
)


def test_canonical_json_is_deterministic() -> None:
    obj = {"b": 2, "a": 1, "c": {"z": 0, "y": 1}}
    first = canonical_json(obj)
    second = canonical_json(obj)
    assert first == second
    assert first == '{"a":1,"b":2,"c":{"y":1,"z":0}}'


def test_record_hash_excludes_record_hash_field() -> None:
    record = {"type": "header", "version": "1.0.0", "record_hash": "ignored"}
    expected = hash_json({"type": "header", "version": "1.0.0"})
    assert compute_record_hash(record) == expected


def test_trace_header_hash_chain() -> None:
    problem_spec = {"version": "1.0.0", "id": "p1",
                    "created_at": "2026-02-02T00:00:00Z", "inputs": {"prompt": "hi"}}
    state = {"version": "1.0.0", "problem": problem_spec, "step_index": 0, "status": "pending", "metadata": {
        "trace_id": "t1", "created_at": "2026-02-02T00:00:00Z", "updated_at": "2026-02-02T00:00:00Z"}}
    header = create_trace_header(
        version="1.0.0",
        trace_id="t1",
        created_at="2026-02-02T00:00:00Z",
        engine_version="0.1.0",
        problem_spec=problem_spec,
        initial_state=state,
    )
    assert header["type"] == "header"
    assert header["record_hash"] == compute_record_hash(header)


def test_trace_step_hash_chain() -> None:
    result = {
        "version": "1.0.0",
        "step": "Normalize",
        "status": "success",
        "input_hash": "in",
        "output_hash": "out",
        "started_at": "2026-02-02T00:00:00Z",
        "finished_at": "2026-02-02T00:00:01Z",
        "output": {"text": "ok"},
    }
    before = {"version": "1.0.0", "step_index": 0}
    after = {"version": "1.0.0", "step_index": 1}
    step = create_trace_step(
        index=1,
        step_index=0,
        result=result,
        state_before=before,
        state_after=after,
        prev_hash="prev",
    )
    assert step["record_hash"] == compute_record_hash(step)


def test_trace_control_hash_chain() -> None:
    state = {"version": "1.0.0", "step_index": 3, "status": "running"}
    control = create_trace_control(
        index=2,
        control_type="loop",
        action="repeat",
        loop_iteration=1,
        start_step="AcquireEvidence",
        end_step="Verify",
        stop_path="artifacts.verification.status",
        stop_operator="equals",
        stop_value="passed",
        state=state,
        prev_hash="prev",
    )
    assert control["record_hash"] == compute_record_hash(control)


def test_canonical_json_rejects_nan() -> None:
    data = {"value": float("nan")}
    try:
        canonical_json(data)
    except ValueError as exc:
        assert "Non-canonical JSON value" in str(exc)
    else:
        raise AssertionError("Expected ValueError for NaN")
