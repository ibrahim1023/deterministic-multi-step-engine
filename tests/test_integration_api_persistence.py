import os

import pytest
from fastapi.testclient import TestClient


DATABASE_URL = os.environ.get("DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")
def test_execute_persists_trace() -> None:
    os.environ.setdefault("DATABASE_URL", DATABASE_URL or "")
    from src.api import app
    from src.persistence import PostgresTraceStore

    store = PostgresTraceStore(DATABASE_URL or "")
    store.init_schema()

    payload = {
        "problem_spec": {
            "version": "1.0.0",
            "id": "req-integration-1",
            "created_at": "2026-02-02T00:00:00Z",
            "inputs": {"prompt": "Hello world"},
        },
        "trace_id": "trace-integration-1",
        "engine_version": "0.1.0",
        "now": "2026-02-02T00:00:00Z",
    }

    with TestClient(app) as client:
        response = client.post("/v1/execute", json=payload)
        assert response.status_code == 200

    trace_id, trace, final_state = store.load_trace_by_request_id("req-integration-1")
    assert trace_id
    assert trace
    assert final_state is not None
