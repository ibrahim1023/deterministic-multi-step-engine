"""Redis caching and idempotency helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

import redis


def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class RedisCache:
    client: redis.Redis

    @classmethod
    def from_url(cls, url: str) -> "RedisCache":
        client = redis.Redis.from_url(url, decode_responses=True)
        return cls(client=client)

    def ping(self) -> None:
        self.client.ping()

    def get_json(self, key: str) -> Dict[str, Any] | None:
        raw = self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: Dict[str, Any], *, ttl_seconds: int | None = None) -> None:
        payload = _canonical_json(value)
        if ttl_seconds is None:
            self.client.set(key, payload)
        else:
            self.client.setex(key, ttl_seconds, payload)
