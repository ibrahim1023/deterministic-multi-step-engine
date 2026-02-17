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
- Loop configuration + stop-condition evaluation: `src/looping.py`.
- FastAPI API layer: `src/api.py`.
- PostgreSQL persistence utilities: `src/persistence.py`.
- Extended step set (AcquireEvidence, Compute, Synthesize, Audit): `src/steps.py`.
- Pydantic contract schemas/versioning: `src/schemas.py`.
- Orchestration planning + LangGraph compilation: `src/orchestration.py`.
- Model abstraction over LiteLLM: `src/model_provider.py`.
- Structured generation + schema enforcement: `src/structured_generation.py`.
- CI determinism diff helpers: `src/determinism_ci.py`.
- Example trace generator: `examples/trace_demo.py`.
- Tests: `tests/test_trace.py`, `tests/test_routing.py`, `tests/test_steps.py`,
  `tests/test_execution.py`, `tests/test_golden_trace.py`,
  `tests/test_invariants.py`, `tests/test_api.py`.

## Setup

- Python 3.12+ recommended.
- Install dependencies: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and set `DATABASE_URL` for persistence.
- For structured generation through LiteLLM, set `MODEL_PROVIDER` and
  `MODEL_NAME` (optional).

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

Integration tests that hit Postgres require `DATABASE_URL` to be set.

Run only determinism-focused checks:

```bash
python -m pytest tests/test_trace.py tests/test_golden_trace.py
```

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

## Conditional Loops

The engine can repeat a deterministic segment until a stop condition is met or
`max_iterations` is reached. Configure this in `problem_spec.settings.loop`.

Example:

```json
{
  "settings": {
    "loop": {
      "enabled": true,
      "start_step": "AcquireEvidence",
      "end_step": "Verify",
      "max_iterations": 3,
      "stop_condition": {
        "path": "artifacts.verification.status",
        "operator": "equals",
        "value": "passed"
      }
    }
  }
}
```

Loop decisions are recorded as `control` trace records with action values
`repeat`, `stop`, or `max_iterations_reached`.

## Multi-Path Verification

Define multiple verification paths to compute parallel checks with an aggregate
result. Each path can override `evidence_required` and the engine returns per-
path status plus an aggregate status in `artifacts.verification`.

Example:

```json
{
  "settings": {
    "verification_paths": [
      {"name": "primary", "evidence_required": true},
      {"name": "secondary", "evidence_required": false}
    ]
  }
}
```

## Audit Reports

The `Audit` step produces a structured report under `artifacts.audit.report`
with input summary, step/artefact counts, verification status, and timestamps.

## Metrics

Use `src.metrics.aggregate_trace_metrics` to compute basic evaluation metrics
from a trace, including per-step counts, control action counts, and durations.

## Persistence

The PostgreSQL persistence module stores trace headers and records. Initialize
schema before use:

```bash
python -c 'from src.persistence import PostgresTraceStore; PostgresTraceStore(\"postgresql://user:pass@localhost:5432/engine\").init_schema()'
```

If `DATABASE_URL` is set, the API automatically stores every trace.

Replay by request ID:

```bash
curl http://127.0.0.1:8000/v1/replay/req-1
```

## Caching / Idempotency

If `REDIS_URL` is set, the API will cache responses by trace ID (or problem
spec ID) and return cached responses on repeated requests. Optional
`IDEMPOTENCY_TTL_SECONDS` controls expiry.

## Orchestration

Set `problem_spec.settings.orchestration_framework` to:

- `native` (default): deterministic engine execution path
- `langgraph`: validates and compiles a LangGraph execution graph before
  running deterministic steps

Example:

```json
{
  "settings": {
    "orchestration_framework": "langgraph"
  }
}
```

## Structured Generation

Synthesis supports schema-conformant generation when enabled:

```json
{
  "settings": {
    "structured_generation": true,
    "model_provider": "litellm",
    "model_name": "openai/gpt-4o-mini"
  }
}
```

If model output is not valid JSON or does not satisfy the target schema, the
step fails deterministically with `structured_generation_failed`.

## Determinism Regression Workflow

Use this flow to verify byte-for-byte replay behavior outside the test runner.

1. Generate a deterministic demo trace:

```bash
python examples/trace_demo.py
```

2. Compare against the golden fixture:

```bash
diff -u tests/golden/trace_demo.ndjson trace_demo.ndjson
```

Expected result: no diff output.

3. Run the golden replay test in CI/local:

```bash
python -m pytest tests/test_golden_trace.py
```

This enforces the contract that identical inputs produce identical NDJSON trace
bytes.

CI performs the same check with:

```bash
python scripts/check_trace_determinism.py
```

## Demo Checklist

- Install dependencies (`pip install -r requirements.txt`).
- Generate a demo trace (`python examples/trace_demo.py`).
- Start API (`uvicorn src.api:app --reload`).
- Execute `/v1/execute` sample request.
- Replay trace by ID (`GET /v1/replay/{request_id}`).
- Run determinism tests (`python -m pytest tests/test_golden_trace.py`).
