"""
Redis cache management.
"""
import redis
import json
import logging
from typing import Optional, Any
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching disabled.")
    redis_client = None


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache."""
    if not redis_client:
        return None

    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = settings.CACHE_TTL) -> bool:
    """Set value in cache with TTL."""
    if not redis_client:
        return False

    try:
        redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )
        return True
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")
        return False


def delete_cache(key: str) -> bool:
    """Delete key from cache."""
    if not redis_client:
        return False

    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error for key {key}: {e}")
        return False


def cache_response(ttl: int = settings.CACHE_TTL, key_prefix: str = ""):
    """
    Decorator to cache function responses.

    Usage:
        @cache_response(ttl=300, key_prefix="airport")
        async def get_airport_data(code: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached = get_cache(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached

            # Call function and cache result
            result = await func(*args, **kwargs)
            set_cache(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key}")

            return result
        return wrapper
    return decorator


def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching pattern.
    Returns number of keys deleted.
    """
    if not redis_client:
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache invalidate error for pattern {pattern}: {e}")
        return 0
