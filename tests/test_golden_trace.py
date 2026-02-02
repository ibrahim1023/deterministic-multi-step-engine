from pathlib import Path

from src.trace import append_record, create_trace_header, create_trace_step


def test_golden_trace_replay(tmp_path: Path) -> None:
    problem_spec = {
        "version": "1.0.0",
        "id": "demo-1",
        "created_at": "2026-02-02T00:00:00Z",
        "inputs": {"prompt": "Summarize the problem."},
    }
    state0 = {
        "version": "1.0.0",
        "problem": problem_spec,
        "step_index": 0,
        "status": "pending",
        "metadata": {
            "trace_id": "trace-demo-1",
            "created_at": "2026-02-02T00:00:00Z",
            "updated_at": "2026-02-02T00:00:00Z",
        },
    }

    header = create_trace_header(
        version="1.0.0",
        trace_id="trace-demo-1",
        created_at="2026-02-02T00:00:00Z",
        engine_version="0.1.0",
        problem_spec=problem_spec,
        initial_state=state0,
    )

    result = {
        "version": "1.0.0",
        "step": "Normalize",
        "status": "success",
        "input_hash": "in",
        "output_hash": "out",
        "started_at": "2026-02-02T00:00:01Z",
        "finished_at": "2026-02-02T00:00:02Z",
        "output": {"normalized_prompt": "summarize the problem"},
    }
    state1 = {
        "version": "1.0.0",
        "problem": problem_spec,
        "step_index": 1,
        "status": "running",
        "metadata": {
            "trace_id": "trace-demo-1",
            "created_at": "2026-02-02T00:00:00Z",
            "updated_at": "2026-02-02T00:00:02Z",
        },
    }

    step = create_trace_step(
        index=1,
        step_index=0,
        result=result,
        state_before=state0,
        state_after=state1,
        prev_hash=header["record_hash"],
    )

    output_path = tmp_path / "trace_demo.ndjson"
    append_record(str(output_path), header)
    append_record(str(output_path), step)

    golden = Path(__file__).parent / "golden" / "trace_demo.ndjson"
    assert output_path.read_bytes() == golden.read_bytes()
