import json
from typing import Any, Optional

import redis
from app.config import settings

_redis: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


class Cache:
    def __init__(self, default_ttl: int = 0):
        self.default_ttl = default_ttl or settings.cache_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        try:
            r = get_redis()
            raw = r.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        try:
            r = get_redis()
            ttl = ttl or self.default_ttl
            r.setex(key, ttl, json.dumps(value, default=str))
        except (redis.RedisError, TypeError):
            pass

    def delete(self, key: str) -> None:
        try:
            get_redis().delete(key)
        except redis.RedisError:
            pass

    def delete_pattern(self, pattern: str) -> None:
        try:
            r = get_redis()
            for key in r.scan_iter(match=pattern):
                r.delete(key)
        except redis.RedisError:
            pass


cache = Cache()
