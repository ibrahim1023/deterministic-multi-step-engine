"""Lightweight .env loader and config helpers."""

from __future__ import annotations

from pathlib import Path
import os


def load_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def get_redis_url() -> str | None:
    return os.environ.get("REDIS_URL")


def get_idempotency_ttl_seconds() -> int | None:
    raw = os.environ.get("IDEMPOTENCY_TTL_SECONDS")
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("IDEMPOTENCY_TTL_SECONDS must be an integer") from exc
    if value <= 0:
        raise ValueError("IDEMPOTENCY_TTL_SECONDS must be > 0") from None
    return value
