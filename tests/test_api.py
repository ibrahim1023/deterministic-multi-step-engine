from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_execute_returns_trace_and_state() -> None:
    payload = {
        "problem_spec": {
            "version": "1.0.0",
            "id": "req-1",
            "created_at": "2026-02-02T00:00:00Z",
            "inputs": {"prompt": "Hello world"},
        },
        "trace_id": "trace-1",
        "engine_version": "0.1.0",
        "now": "2026-02-02T00:00:00Z",
    }
    response = client.post("/v1/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == "trace-1"
    assert data["engine_version"] == "0.1.0"
    assert data["trace"][0]["type"] == "header"
    assert len(data["trace"]) == 8
    assert data["final_state"]["status"] == "completed"
    assert data["final_state"]["step_index"] == 7


def test_execute_is_deterministic() -> None:
    payload = {
        "problem_spec": {
            "version": "1.0.0",
            "id": "req-2",
            "created_at": "2026-02-02T00:00:00Z",
            "inputs": {"prompt": "Hello world"},
        },
        "trace_id": "trace-2",
        "engine_version": "0.1.0",
        "now": "2026-02-02T00:00:00Z",
    }
    first = client.post("/v1/execute", json=payload)
    second = client.post("/v1/execute", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_execute_rejects_empty_prompt() -> None:
    payload = {
        "problem_spec": {
            "version": "1.0.0",
            "id": "req-3",
            "created_at": "2026-02-02T00:00:00Z",
            "inputs": {"prompt": "   "},
        },
        "now": "2026-02-02T00:00:00Z",
    }
    response = client.post("/v1/execute", json=payload)
    assert response.status_code == 400
