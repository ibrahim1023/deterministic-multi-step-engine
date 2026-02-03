# Deterministic Multi-Step Reasoning Engine

This repo defines the scope, design, and initial implementation for a
deterministic, testable multi-step reasoning engine / SDK. It is intentionally
non-conversational and designed to be embedded in other systems.

## What This Is

- A deterministic reasoning engine with structured, validated steps
- Fully traceable and replayable execution with strict schemas
- A programmatic API (not a chatbot or UI)

## What This Is Not

- A chat UI or conversational agent
- Free-form text generation without validation
- LLM-controlled execution flow

## Status

Current phase: Planning & Design (select core utilities implemented)

## Implementation Snapshot

- Python core utilities live in `src/`.
- Append-only trace format + hashing utilities: `src/trace.py`.
- Deterministic routing policies: `src/routing.py`.
- Core steps (Normalize, Decompose, Verify): `src/steps.py`.
- Invariant validation utilities: `src/invariants.py`.
- Fixed-order execution graph: `src/execution.py`.
- Deterministic execution runner: `src/engine.py`.
- FastAPI API layer: `src/api.py`.
- PostgreSQL persistence utilities: `src/persistence.py`.
- Example trace generator: `examples/trace_demo.py`.
- Tests: `tests/test_trace.py`, `tests/test_routing.py`, `tests/test_steps.py`,
  `tests/test_execution.py`, `tests/test_golden_trace.py`,
  `tests/test_invariants.py`, `tests/test_api.py`.

## Setup

- Python 3.12+ recommended.
- Install dependencies: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and set `DATABASE_URL` for persistence.

## Run Demo

```bash
python examples/trace_demo.py
```

## Run Tests

```bash
python -m pytest
```

Golden determinism tests compare generated traces against
`tests/golden/trace_demo.ndjson`.

## Run API

```bash
uvicorn src.api:app --reload
```

Example request:

```bash
curl -X POST http://127.0.0.1:8000/v1/execute \\
  -H 'Content-Type: application/json' \\
  -d '{\"problem_spec\":{\"version\":\"1.0.0\",\"id\":\"req-1\",\"created_at\":\"2026-02-02T00:00:00Z\",\"inputs\":{\"prompt\":\"Hello world\"}},\"trace_id\":\"trace-1\",\"now\":\"2026-02-02T00:00:00Z\"}'
```

## Persistence

The PostgreSQL persistence module stores trace headers and records. Initialize
schema before use:

```bash
python -c 'from src.persistence import PostgresTraceStore; PostgresTraceStore(\"postgresql://user:pass@localhost:5432/engine\").init_schema()'
```

If `DATABASE_URL` is set, the API automatically stores every trace.
