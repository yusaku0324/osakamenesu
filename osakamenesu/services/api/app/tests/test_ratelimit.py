import asyncio
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pytest
from redis.exceptions import RedisError

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from utils import ratelimit as ratelimit_module  # type: ignore  # noqa: E402
from utils.ratelimit import RateLimiter  # type: ignore  # noqa: E402


class InMemoryRedis:
    """Minimal async Redis clone for exercising the rate limiter logic."""

    def __init__(self) -> None:
        self._zsets: Dict[str, Dict[str, float]] = {}
        self.closed = False

    def pipeline(self) -> "InMemoryPipeline":
        return InMemoryPipeline(self)

    async def close(self) -> None:
        self.closed = True

    async def zrem(self, key: str, member: str) -> int:
        zset = self._zsets.get(key)
        if not zset or member not in zset:
            return 0
        del zset[member]
        return 1

    async def zrange(
        self, key: str, start: int, end: int, *, withscores: bool = False
    ) -> List[Tuple[str, float]]:
        zset = self._zsets.get(key, {})
        sorted_items = sorted(zset.items(), key=lambda item: item[1])
        stop = end + 1 if end >= 0 else None
        slice_ = sorted_items[start:stop]
        if withscores:
            return slice_
        return [member for member, _ in slice_]

    # Internal helpers -------------------------------------------------
    def _ensure(self, key: str) -> Dict[str, float]:
        return self._zsets.setdefault(key, {})

    def _zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        zset = self._zsets.get(key)
        if not zset:
            return 0
        to_remove = [member for member, score in zset.items() if min_score <= score <= max_score]
        for member in to_remove:
            del zset[member]
        return len(to_remove)

    def _zadd(self, key: str, mapping: Dict[str, float]) -> int:
        zset = self._ensure(key)
        added = 0
        for member, score in mapping.items():
            if member not in zset:
                added += 1
            zset[member] = score
        return added

    def _zcard(self, key: str) -> int:
        return len(self._zsets.get(key, {}))

    def _expire(self, key: str, ttl: int) -> bool:  # noqa: ARG002 - parity method
        # TTL behaviour is not required for the tests.
        self._ensure(key)
        return True


class InMemoryPipeline:
    def __init__(self, redis: InMemoryRedis) -> None:
        self.redis = redis
        self.ops: List[Tuple[str, Tuple, Dict]] = []

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> "InMemoryPipeline":
        self.ops.append(("zremrangebyscore", (key, min_score, max_score), {}))
        return self

    def zadd(self, key: str, mapping: Dict[str, float]) -> "InMemoryPipeline":
        self.ops.append(("zadd", (key, mapping), {}))
        return self

    def zcard(self, key: str) -> "InMemoryPipeline":
        self.ops.append(("zcard", (key,), {}))
        return self

    def expire(self, key: str, ttl: int) -> "InMemoryPipeline":
        self.ops.append(("expire", (key, ttl), {}))
        return self

    async def execute(self) -> Iterable[int]:
        results: List[int] = []
        for op, args, kwargs in self.ops:
            method = getattr(self.redis, f"_{op}")
            results.append(method(*args, **kwargs))
        return results


class BoomRedisError(RedisError):
    pass


class FailingRedis(InMemoryRedis):
    def __init__(self) -> None:
        super().__init__()
        self.pipeline_calls = 0

    def pipeline(self) -> "FailingPipeline":  # type: ignore[override]
        self.pipeline_calls += 1
        return FailingPipeline()


class FailingPipeline:
    async def execute(self) -> Iterable[int]:
        raise BoomRedisError("boom")


class FakeTime:
    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def time(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def run(coro):
    return asyncio.run(coro)


def test_memory_rate_limiter_blocks_after_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = FakeTime(start=10.0)
    monkeypatch.setattr(ratelimit_module, "time", fake_time)

    limiter = RateLimiter(max_events=2, window_sec=60.0, redis_client=None, namespace="test")

    allowed1, retry1 = run(limiter.allow("k"))
    allowed2, retry2 = run(limiter.allow("k"))
    allowed3, retry3 = run(limiter.allow("k"))

    assert allowed1 is True and retry1 == 0.0
    assert allowed2 is True and retry2 == 0.0
    assert allowed3 is False and retry3 > 0

    fake_time.advance(61.0)
    allowed4, _ = run(limiter.allow("k"))
    assert allowed4 is True


def test_redis_rate_limiter_behaves_like_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = FakeTime(start=100.0)
    monkeypatch.setattr(ratelimit_module, "time", fake_time)

    redis = InMemoryRedis()
    limiter = RateLimiter(
        max_events=2,
        window_sec=60.0,
        redis_client=redis,
        namespace="test",
        redis_error_cooldown=0.0,
    )

    assert run(limiter.allow("k"))[0] is True
    assert run(limiter.allow("k"))[0] is True
    blocked, retry = run(limiter.allow("k"))
    assert blocked is False and retry > 0

    fake_time.advance(61.0)
    assert run(limiter.allow("k"))[0] is True


def test_rate_limiter_falls_back_on_redis_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = FakeTime(start=200.0)
    monkeypatch.setattr(ratelimit_module, "time", fake_time)

    redis = FailingRedis()
    limiter = RateLimiter(
        max_events=2,
        window_sec=60.0,
        redis_client=redis,
        namespace="test",
        redis_error_cooldown=30.0,
    )

    allowed1, _ = run(limiter.allow("k"))
    allowed2, _ = run(limiter.allow("k"))
    blocked, _ = run(limiter.allow("k"))

    assert allowed1 is True
    assert allowed2 is True
    assert blocked is False
    assert redis.pipeline_calls == 1  # second call skips redis during cooldown

    fake_time.advance(31.0)
    run(limiter.allow("another"))
    assert redis.pipeline_calls == 2
