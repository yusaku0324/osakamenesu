from __future__ import annotations

import asyncio
import time
import uuid
import logging
from collections import deque
from typing import Deque, Dict, Optional, Tuple

from redis.asyncio import Redis
from redis.exceptions import RedisError


class RateLimiter:
    """Sliding-window rate limiter with optional Redis backend."""

    def __init__(
        self,
        max_events: int,
        window_sec: float,
        redis_client: Optional[Redis] = None,
        namespace: str = "rate",
        redis_error_cooldown: float = 5.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.max_events = max_events
        self.window = window_sec
        self.redis = redis_client
        self.namespace = namespace.rstrip(":") + ":"
        self._events: Dict[str, Deque[float]] = {}
        self.redis_error_cooldown = max(0.0, redis_error_cooldown)
        self._redis_disabled_until = 0.0
        self._logger = logger or logging.getLogger(__name__)
        self._last_warning_at = 0.0

    async def close(self) -> None:
        if self.redis:
            await self.redis.close()

    async def allow(self, key: str) -> Tuple[bool, float]:
        if self.redis:
            now = time.time()
            if now < self._redis_disabled_until:
                return self._allow_memory(key)
            try:
                allowed, retry = await self._allow_redis(key)
                if self._redis_disabled_until and self._logger:
                    self._logger.info("Rate limiter redis backend recovered")
                self._redis_disabled_until = 0.0
                return allowed, retry
            except asyncio.CancelledError:
                raise
            except RedisError as exc:
                if self.redis_error_cooldown:
                    self._redis_disabled_until = now + self.redis_error_cooldown
                if self._logger and now - self._last_warning_at >= 5.0:
                    self._logger.warning("Rate limiter falling back to memory: %s", exc)
                    self._last_warning_at = now
                return self._allow_memory(key)
            except Exception as exc:  # pragma: no cover - defensive catch-all
                if self.redis_error_cooldown:
                    self._redis_disabled_until = now + self.redis_error_cooldown
                if self._logger and now - self._last_warning_at >= 5.0:
                    self._logger.warning("Rate limiter unexpected redis error: %s", exc)
                    self._last_warning_at = now
                return self._allow_memory(key)
        return self._allow_memory(key)

    def _allow_memory(self, key: str) -> Tuple[bool, float]:
        now = time.time()
        dq = self._events.setdefault(key, deque())
        cutoff = now - self.window
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= self.max_events:
            retry_after = max(0.0, self.window - (now - dq[0]))
            return False, retry_after
        dq.append(now)
        return True, 0.0

    async def _allow_redis(self, key: str) -> Tuple[bool, float]:
        assert self.redis is not None
        now = time.time()
        redis_key = f"{self.namespace}{key}"
        member = f"{now}:{uuid.uuid4()}"
        min_score = now - self.window

        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(redis_key, 0, min_score)
        pipeline.zadd(redis_key, {member: now})
        pipeline.zcard(redis_key)
        pipeline.expire(redis_key, int(self.window) + 1)
        _, _, count, _ = await pipeline.execute()

        if count > self.max_events:
            await self.redis.zrem(redis_key, member)
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = max(0.0, self.window - (now - oldest[0][1]))
            else:
                retry_after = self.window
            return False, retry_after

        return True, 0.0


def create_rate_limiter(
    max_events: int,
    window_sec: float,
    redis_client: Optional[Redis],
    namespace: str,
    *,
    redis_error_cooldown: float = 5.0,
    logger: Optional[logging.Logger] = None,
) -> RateLimiter:
    return RateLimiter(
        max_events=max_events,
        window_sec=window_sec,
        redis_client=redis_client,
        namespace=namespace,
        redis_error_cooldown=redis_error_cooldown,
        logger=logger,
    )


async def shutdown_rate_limiter(limiter: RateLimiter) -> None:
    await limiter.close()
