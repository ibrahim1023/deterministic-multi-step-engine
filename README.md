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
- Example trace generator: `examples/trace_demo.py`.
- Tests: `tests/test_trace.py`, `tests/test_routing.py`, `tests/test_steps.py`.

## Setup

- Python 3.12+ recommended.

## Run Demo

```bash
python examples/trace_demo.py
```

## Run Tests

```bash
python -m pytest
```
