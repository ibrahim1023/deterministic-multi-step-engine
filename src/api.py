"""FastAPI layer for deterministic execution."""

from __future__ import annotations

from typing import Any, Dict

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.cache import RedisCache
from src.config import (
    get_database_url,
    get_idempotency_ttl_seconds,
    get_redis_url,
    load_env,
)
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
_CACHE: RedisCache | None = None


def _init_trace_store() -> None:
    global _TRACE_STORE
    database_url = get_database_url()
    if not database_url:
        _TRACE_STORE = None
        return
    store = PostgresTraceStore(database_url)
    store.init_schema()
    _TRACE_STORE = store


def _init_cache() -> None:
    global _CACHE
    redis_url = get_redis_url()
    if not redis_url:
        _CACHE = None
        return
    cache = RedisCache.from_url(redis_url)
    cache.ping()
    _CACHE = cache


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _init_trace_store()
    _init_cache()
    yield


app = FastAPI(title="Deterministic Multi-Step Reasoning Engine", lifespan=_lifespan)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest) -> ExecuteResponse:
    try:
        trace_key = request.trace_id or str(request.problem_spec.get("id"))
        if _CACHE is not None and trace_key:
            cached = _CACHE.get_json(f"trace:{trace_key}")
            if cached is not None:
                return ExecuteResponse(**cached)
        result = execute_problem(
            request.problem_spec,
            trace_id=request.trace_id,
            engine_version=request.engine_version or ENGINE_VERSION,
            now=request.now,
        )
        response_payload = {
            "trace_id": result.trace_id,
            "engine_version": result.engine_version,
            "trace": result.trace,
            "final_state": result.final_state,
        }
        if _TRACE_STORE is not None:
            _TRACE_STORE.store_trace(
                result.trace,
                problem_spec=request.problem_spec,
                final_state=result.final_state,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if _CACHE is not None and trace_key:
        _CACHE.set_json(
            f"trace:{trace_key}",
            response_payload,
            ttl_seconds=get_idempotency_ttl_seconds(),
        )

    return ExecuteResponse(**response_payload)


@app.get("/v1/replay/{request_id}", response_model=ExecuteResponse)
async def replay(request_id: str) -> ExecuteResponse:
    if _TRACE_STORE is None:
        raise HTTPException(status_code=400, detail="Persistence is not configured")
    trace_id, trace, final_state = _TRACE_STORE.load_trace_by_request_id(request_id)
    if not trace_id:
        raise HTTPException(status_code=404, detail="Trace not found")
    if final_state is None:
        raise HTTPException(status_code=409, detail="Final state missing for replay")
    return ExecuteResponse(
        trace_id=trace_id,
        engine_version=ENGINE_VERSION,
        trace=trace,
        final_state=final_state,
    )
