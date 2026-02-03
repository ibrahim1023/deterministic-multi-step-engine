"""PostgreSQL persistence for traces, metadata, and hashes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple

import psycopg
from psycopg.types.json import Json
from psycopg.rows import dict_row


@dataclass(frozen=True)
class TraceMetadata:
    trace_id: str
    request_id: str | None
    created_at: str
    engine_version: str
    problem_spec_hash: str
    initial_state_hash: str
    head_hash: str
    record_count: int


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS traces (
  trace_id TEXT PRIMARY KEY,
  request_id TEXT,
  created_at TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  problem_spec_hash TEXT NOT NULL,
  initial_state_hash TEXT NOT NULL,
  head_hash TEXT NOT NULL,
  record_count INTEGER NOT NULL,
  problem_spec JSONB,
  final_state JSONB
);

ALTER TABLE traces ADD COLUMN IF NOT EXISTS request_id TEXT;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS problem_spec JSONB;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS final_state JSONB;

CREATE TABLE IF NOT EXISTS trace_records (
  trace_id TEXT NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
  index INTEGER NOT NULL,
  record_hash TEXT NOT NULL,
  prev_hash TEXT,
  record JSONB NOT NULL,
  PRIMARY KEY (trace_id, index)
);

CREATE INDEX IF NOT EXISTS trace_records_trace_id_idx ON trace_records(trace_id);
CREATE INDEX IF NOT EXISTS traces_request_id_idx ON traces(request_id);
"""


def extract_trace_metadata(trace: Iterable[Mapping[str, Any]]) -> TraceMetadata:
    records = list(trace)
    if not records:
        raise ValueError("trace must include at least the header")
    header = records[0]
    if header.get("type") != "header":
        raise ValueError("trace must start with a header record")
    trace_id = header.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id:
        raise ValueError("header.trace_id is required")
    head_hash = records[-1].get("record_hash")
    if not isinstance(head_hash, str) or not head_hash:
        raise ValueError("last record must include record_hash")
    return TraceMetadata(
        trace_id=trace_id,
        request_id=None,
        created_at=str(header.get("created_at")),
        engine_version=str(header.get("engine_version")),
        problem_spec_hash=str(header.get("problem_spec_hash")),
        initial_state_hash=str(header.get("initial_state_hash")),
        head_hash=head_hash,
        record_count=len(records),
    )


def extract_request_id(problem_spec: Mapping[str, Any]) -> str:
    value = problem_spec.get("id")
    if not isinstance(value, str) or not value:
        raise ValueError("problem_spec.id is required for replay")
    return value


def prepare_trace_records(trace: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    prepared: List[Dict[str, Any]] = []
    for idx, record in enumerate(trace):
        record_hash = record.get("record_hash")
        if not isinstance(record_hash, str) or not record_hash:
            raise ValueError("record_hash is required for all records")
        prepared.append(
            {
                "index": idx,
                "record_hash": record_hash,
                "prev_hash": record.get("prev_hash"),
                "record": dict(record),
            }
        )
    return prepared


class PostgresTraceStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def init_schema(self) -> None:
        with psycopg.connect(self._dsn) as conn:
            conn.execute(_SCHEMA_SQL)
            conn.commit()

    def store_trace(
        self,
        trace: Iterable[Mapping[str, Any]],
        *,
        problem_spec: Mapping[str, Any] | None = None,
        final_state: Mapping[str, Any] | None = None,
    ) -> TraceMetadata:
        metadata = extract_trace_metadata(trace)
        request_id = extract_request_id(problem_spec) if problem_spec is not None else None
        records = prepare_trace_records(trace)
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO traces (
                      trace_id,
                      request_id,
                      created_at,
                      engine_version,
                      problem_spec_hash,
                      initial_state_hash,
                      head_hash,
                      record_count,
                      problem_spec,
                      final_state
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trace_id) DO UPDATE SET
                      request_id = EXCLUDED.request_id,
                      created_at = EXCLUDED.created_at,
                      engine_version = EXCLUDED.engine_version,
                      problem_spec_hash = EXCLUDED.problem_spec_hash,
                      initial_state_hash = EXCLUDED.initial_state_hash,
                      head_hash = EXCLUDED.head_hash,
                      record_count = EXCLUDED.record_count,
                      problem_spec = EXCLUDED.problem_spec,
                      final_state = EXCLUDED.final_state
                    """,
                    (
                        metadata.trace_id,
                        request_id,
                        metadata.created_at,
                        metadata.engine_version,
                        metadata.problem_spec_hash,
                        metadata.initial_state_hash,
                        metadata.head_hash,
                        metadata.record_count,
                        Json(problem_spec) if problem_spec is not None else None,
                        Json(final_state) if final_state is not None else None,
                    ),
                )
                for record in records:
                    cur.execute(
                        """
                        INSERT INTO trace_records (
                          trace_id,
                          index,
                          record_hash,
                          prev_hash,
                          record
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (trace_id, index) DO UPDATE SET
                          record_hash = EXCLUDED.record_hash,
                          prev_hash = EXCLUDED.prev_hash,
                          record = EXCLUDED.record
                        """,
                        (
                            metadata.trace_id,
                            record["index"],
                            record["record_hash"],
                            record.get("prev_hash"),
                            Json(record["record"]),
                        ),
                    )
            conn.commit()
        return TraceMetadata(
            trace_id=metadata.trace_id,
            request_id=request_id,
            created_at=metadata.created_at,
            engine_version=metadata.engine_version,
            problem_spec_hash=metadata.problem_spec_hash,
            initial_state_hash=metadata.initial_state_hash,
            head_hash=metadata.head_hash,
            record_count=metadata.record_count,
        )

    def load_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        if not trace_id:
            raise ValueError("trace_id is required")
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT index, record
                    FROM trace_records
                    WHERE trace_id = %s
                    ORDER BY index ASC
                    """,
                    (trace_id,),
                )
                rows = cur.fetchall()
        return [row["record"] for row in rows]

    def load_trace_bundle(self, trace_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any] | None]:
        if not trace_id:
            raise ValueError("trace_id is required")
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT final_state
                    FROM traces
                    WHERE trace_id = %s
                    """,
                    (trace_id,),
                )
                meta = cur.fetchone()
            trace = self.load_trace(trace_id)
        final_state = meta["final_state"] if meta else None
        return trace, final_state

    def load_trace_by_request_id(self, request_id: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any] | None]:
        if not request_id:
            raise ValueError("request_id is required")
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT trace_id, final_state
                    FROM traces
                    WHERE request_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (request_id,),
                )
                row = cur.fetchone()
            if not row:
                return "", [], None
            trace_id = row["trace_id"]
            trace = self.load_trace(trace_id)
            return trace_id, trace, row["final_state"]
