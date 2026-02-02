from src.steps import decompose, normalize, verify


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
