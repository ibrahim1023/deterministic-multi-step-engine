import pytest

from src.persistence import extract_request_id, extract_trace_metadata, prepare_trace_records


def test_extract_trace_metadata() -> None:
    trace = [
        {
            "type": "header",
            "trace_id": "trace-1",
            "created_at": "2026-02-02T00:00:00Z",
            "engine_version": "0.1.0",
            "problem_spec_hash": "spec-hash",
            "initial_state_hash": "state-hash",
            "record_hash": "hash-0",
        },
        {
            "type": "step",
            "record_hash": "hash-1",
            "prev_hash": "hash-0",
        },
    ]
    metadata = extract_trace_metadata(trace)
    assert metadata.trace_id == "trace-1"
    assert metadata.head_hash == "hash-1"
    assert metadata.record_count == 2


def test_prepare_trace_records_requires_hash() -> None:
    trace = [
        {
            "type": "header",
            "trace_id": "trace-1",
            "created_at": "2026-02-02T00:00:00Z",
            "engine_version": "0.1.0",
            "problem_spec_hash": "spec-hash",
            "initial_state_hash": "state-hash",
            "record_hash": "hash-0",
        }
    ]
    prepared = prepare_trace_records(trace)
    assert prepared[0]["record_hash"] == "hash-0"
    assert prepared[0]["index"] == 0


def test_extract_request_id() -> None:
    assert extract_request_id({"id": "req-1"}) == "req-1"


def test_extract_request_id_requires_value() -> None:
    with pytest.raises(ValueError):
        extract_request_id({"id": ""})
