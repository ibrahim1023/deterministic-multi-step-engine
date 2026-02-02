"""Append-only trace format and hashing utilities."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def canonical_json(obj: Any) -> str:
    """Return canonical JSON per json-c14n-v1 (sorted keys, no whitespace)."""
    try:
        return json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except ValueError as exc:
        raise ValueError("Non-canonical JSON value (NaN/Infinity?)") from exc


def canonical_json_bytes(obj: Any) -> bytes:
    return canonical_json(obj).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_json(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def _record_without_hash(record: Dict[str, Any]) -> Dict[str, Any]:
    stripped = dict(record)
    stripped.pop("record_hash", None)
    return stripped


def compute_record_hash(record: Dict[str, Any]) -> str:
    return hash_json(_record_without_hash(record))


def create_trace_header(
    *,
    version: str,
    trace_id: str,
    created_at: str,
    engine_version: str,
    problem_spec: Dict[str, Any],
    initial_state: Dict[str, Any],
    hash_algorithm: str = "sha256",
    canonicalization: str = "json-c14n-v1",
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "type": "header",
        "version": version,
        "trace_id": trace_id,
        "created_at": created_at,
        "engine_version": engine_version,
        "hash_algorithm": hash_algorithm,
        "canonicalization": canonicalization,
        "problem_spec_hash": hash_json(problem_spec),
        "initial_state_hash": hash_json(initial_state),
    }
    record["record_hash"] = compute_record_hash(record)
    return record


def create_trace_step(
    *,
    index: int,
    step_index: int,
    result: Dict[str, Any],
    state_before: Dict[str, Any],
    state_after: Dict[str, Any],
    prev_hash: str,
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "type": "step",
        "index": index,
        "step_index": step_index,
        "result": result,
        "state_before_hash": hash_json(state_before),
        "state_after_hash": hash_json(state_after),
        "prev_hash": prev_hash,
    }
    record["record_hash"] = compute_record_hash(record)
    return record


def append_record(path: str, record: Dict[str, Any]) -> None:
    """Append a record as a single JSON line. Caller ensures append-only usage."""
    line = canonical_json(record)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.write("\n")
