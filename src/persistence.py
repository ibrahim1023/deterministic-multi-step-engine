"""PostgreSQL persistence for traces, metadata, and hashes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

import psycopg
from psycopg.types.json import Json
from psycopg.rows import dict_row


@dataclass(frozen=True)
class TraceMetadata:
    trace_id: str
    created_at: str
    engine_version: str
    problem_spec_hash: str
    initial_state_hash: str
    head_hash: str
    record_count: int


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS traces (
  trace_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  problem_spec_hash TEXT NOT NULL,
  initial_state_hash TEXT NOT NULL,
  head_hash TEXT NOT NULL,
  record_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS trace_records (
  trace_id TEXT NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
  index INTEGER NOT NULL,
  record_hash TEXT NOT NULL,
  prev_hash TEXT,
  record JSONB NOT NULL,
  PRIMARY KEY (trace_id, index)
);

CREATE INDEX IF NOT EXISTS trace_records_trace_id_idx ON trace_records(trace_id);
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
        created_at=str(header.get("created_at")),
        engine_version=str(header.get("engine_version")),
        problem_spec_hash=str(header.get("problem_spec_hash")),
        initial_state_hash=str(header.get("initial_state_hash")),
        head_hash=head_hash,
        record_count=len(records),
    )


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

    def store_trace(self, trace: Iterable[Mapping[str, Any]]) -> TraceMetadata:
        metadata = extract_trace_metadata(trace)
        records = prepare_trace_records(trace)
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO traces (
                      trace_id,
                      created_at,
                      engine_version,
                      problem_spec_hash,
                      initial_state_hash,
                      head_hash,
                      record_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trace_id) DO UPDATE SET
                      created_at = EXCLUDED.created_at,
                      engine_version = EXCLUDED.engine_version,
                      problem_spec_hash = EXCLUDED.problem_spec_hash,
                      initial_state_hash = EXCLUDED.initial_state_hash,
                      head_hash = EXCLUDED.head_hash,
                      record_count = EXCLUDED.record_count
                    """,
                    (
                        metadata.trace_id,
                        metadata.created_at,
                        metadata.engine_version,
                        metadata.problem_spec_hash,
                        metadata.initial_state_hash,
                        metadata.head_hash,
                        metadata.record_count,
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
        return metadata

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
