from src.steps import (
    acquire_evidence,
    audit,
    compute,
    decompose,
    normalize,
    synthesize,
    verify,
)


def test_normalize_success() -> None:
    state = {
        "problem": {"inputs": {"prompt": "  Hello   World  "}},
        "step_index": 0,
        "status": "pending",
        "metadata": {"updated_at": "2026-02-02T00:00:00Z"},
    }
    next_state, result = normalize(state, now="2026-02-02T00:00:01Z")
    assert result["status"] == "success"
    assert result["output"]["normalized_prompt"] == "Hello World"
    assert next_state["artifacts"]["normalized"]["normalized_prompt"] == "Hello World"
    assert next_state["step_index"] == 1


def test_normalize_failure() -> None:
    state = {
        "problem": {"inputs": {"prompt": "  "}},
        "step_index": 0,
        "status": "pending",
    }
    next_state, result = normalize(state, now="2026-02-02T00:00:01Z")
    assert result["status"] == "failed"
    assert next_state["step_index"] == 0


def test_decompose_uses_goals() -> None:
    state = {
        "problem": {"inputs": {"prompt": "Do X", "goals": ["A", "B"]}},
        "step_index": 0,
        "status": "pending",
    }
    next_state, result = decompose(state, now="2026-02-02T00:00:02Z")
    assert result["output"]["tasks"] == ["A", "B"]
    assert next_state["artifacts"]["decomposition"]["tasks"] == ["A", "B"]


def test_decompose_falls_back_to_prompt() -> None:
    state = {
        "problem": {"inputs": {"prompt": "Do X", "goals": []}},
        "step_index": 0,
        "status": "pending",
    }
    next_state, result = decompose(state, now="2026-02-02T00:00:02Z")
    assert result["output"]["tasks"] == ["Do X"]
    assert next_state["step_index"] == 1


def test_verify_tasks_present() -> None:
    state = {
        "artifacts": {"decomposition": {"tasks": ["A"]}},
        "step_index": 1,
        "status": "running",
    }
    next_state, result = verify(state, now="2026-02-02T00:00:03Z")
    assert result["output"]["checks"]["tasks_present"] is True
    assert next_state["artifacts"]["verification"]["status"] == "passed"


def test_acquire_evidence_reads_context() -> None:
    state = {
        "problem": {"inputs": {"context": {"evidence": [{"id": "e1"}]}}},
        "step_index": 2,
        "status": "running",
    }
    next_state, result = acquire_evidence(state, now="2026-02-02T00:00:04Z")
    assert result["output"]["evidence_count"] == 1
    assert next_state["artifacts"]["evidence"]["evidence_count"] == 1


def test_compute_uses_task_count() -> None:
    state = {
        "artifacts": {"decomposition": {"tasks": ["A", "B"]}},
        "step_index": 3,
        "status": "running",
    }
    next_state, result = compute(state, now="2026-02-02T00:00:05Z")
    assert result["output"]["task_count"] == 2
    assert next_state["artifacts"]["computation"]["task_count"] == 2


def test_synthesize_uses_computation() -> None:
    state = {
        "artifacts": {"computation": {"task_count": 2}},
        "step_index": 4,
        "status": "running",
    }
    next_state, result = synthesize(state, now="2026-02-02T00:00:06Z")
    assert "Processed 2 task" in result["output"]["summary"]
    assert "summary" in next_state["artifacts"]["synthesis"]


def test_audit_records_artifact_keys() -> None:
    state = {
        "artifacts": {"normalized": {}, "decomposition": {}},
        "step_index": 5,
        "status": "running",
    }
    next_state, result = audit(state, now="2026-02-02T00:00:07Z")
    assert result["output"]["artifact_keys"] == ["decomposition", "normalized"]
    assert next_state["artifacts"]["audit"]["status"] == "ok"
