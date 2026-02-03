"""FastAPI layer for deterministic execution."""

from __future__ import annotations

from typing import Any, Dict

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import get_database_url, load_env
from src.engine import ENGINE_VERSION, execute_problem
from src.persistence import PostgresTraceStore

load_env()


class ExecuteRequest(BaseModel):
    problem_spec: Dict[str, Any]
    trace_id: str | None = None
    engine_version: str | None = None
    now: str | None = None


class ExecuteResponse(BaseModel):
    trace_id: str
    engine_version: str
    trace: list[Dict[str, Any]]
    final_state: Dict[str, Any]


_TRACE_STORE: PostgresTraceStore | None = None


def _init_trace_store() -> None:
    global _TRACE_STORE
    database_url = get_database_url()
    if not database_url:
        _TRACE_STORE = None
        return
    store = PostgresTraceStore(database_url)
    store.init_schema()
    _TRACE_STORE = store


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _init_trace_store()
    yield


app = FastAPI(title="Deterministic Multi-Step Reasoning Engine", lifespan=_lifespan)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest) -> ExecuteResponse:
    try:
        result = execute_problem(
            request.problem_spec,
            trace_id=request.trace_id,
            engine_version=request.engine_version or ENGINE_VERSION,
            now=request.now,
        )
        if _TRACE_STORE is not None:
            _TRACE_STORE.store_trace(result.trace)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ExecuteResponse(
        trace_id=result.trace_id,
        engine_version=result.engine_version,
        trace=result.trace,
        final_state=result.final_state,
    )
