from src.cache import RedisCache


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ping_called = False

    def ping(self) -> None:
        self.ping_called = True

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.data[key] = value


def test_cache_roundtrip() -> None:
    fake = FakeRedis()
    cache = RedisCache(client=fake)  # type: ignore[arg-type]
    payload = {"trace_id": "trace-1", "engine_version": "0.1.0"}
    cache.set_json("trace:trace-1", payload)
    stored = cache.get_json("trace:trace-1")
    assert stored == payload
