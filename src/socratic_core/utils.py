"""Utility functions and classes for Socratic Core.

Provides common utilities like caching, ID generation, and datetime handling.
"""

import functools
import threading
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple

# ============================================================================
# Datetime Utilities
# ============================================================================


def serialize_datetime(dt: datetime) -> str:
    """
    Serialize a datetime object to ISO format string.

    Args:
        dt: datetime object to serialize

    Returns:
        ISO format string (YYYY-MM-DDTHH:MM:SS.ffffff or with timezone)
    """
    return dt.isoformat()


def deserialize_datetime(iso_string: str) -> datetime:
    """
    Deserialize an ISO format string to datetime object.

    Supports both ISO format and legacy space-separated format.

    Args:
        iso_string: ISO format string or legacy format

    Returns:
        datetime object

    Raises:
        ValueError: If string cannot be parsed as datetime
    """
    # Handle legacy format: "2025-12-09 10:30:45.123456"
    if " " in iso_string and "T" not in iso_string:
        iso_string = iso_string.replace(" ", "T", 1)

    return datetime.fromisoformat(iso_string)


# ============================================================================
# ID Generation
# ============================================================================


class ProjectIDGenerator:
    """Generates unique project IDs."""

    @staticmethod
    def generate(owner: Optional[str] = None) -> str:
        """
        Generate a unique project ID.

        Args:
            owner: Optional owner identifier to include in ID

        Returns:
            Unique project ID in format: proj_{owner_prefix}_{uuid}
        """
        unique_part = str(uuid.uuid4())[:8]
        if owner:
            # Sanitize owner string (remove special chars, limit length)
            owner_safe = "".join(c if c.isalnum() else "" for c in owner)[:10].lower()
            return f"proj_{owner_safe}_{unique_part}"
        return f"proj_{unique_part}"


class UserIDGenerator:
    """Generates unique user IDs."""

    @staticmethod
    def generate() -> str:
        """
        Generate a unique user ID.

        Returns:
            Unique user ID in format: user_{uuid}
        """
        unique_part = str(uuid.uuid4())[:8]
        return f"user_{unique_part}"


# ============================================================================
# TTL Cache
# ============================================================================


class TTLCache:
    """
    A cache with time-to-live (TTL) support.

    Stores cached values with an expiration time. Expired entries are
    automatically considered invalid but not immediately removed.
    """

    def __init__(self, ttl_minutes: float = 5):
        """
        Initialize TTL cache.

        Args:
            ttl_minutes: Time-to-live in minutes (default: 5)
        """
        self._cache: Dict[Any, Tuple[Any, datetime]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._lock = threading.Lock()

    def get(self, key: Any) -> Tuple[bool, Any]:
        """
        Get a value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Tuple of (found: bool, value: Any)
        """
        with self._lock:
            if key not in self._cache:
                return False, None

            value, expiry_time = self._cache[key]
            if datetime.now() > expiry_time:
                # Expired
                del self._cache[key]
                return False, None

            return True, value

    def set(self, key: Any, value: Any) -> None:
        """
        Set a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            expiry_time = datetime.now() + self._ttl
            self._cache[key] = (value, expiry_time)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, (_, expiry_time) in self._cache.items() if now > expiry_time
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)


def cached(ttl_minutes: Optional[float] = None, ttl: Optional[float] = None) -> Callable:
    """
    Decorator for caching function results with TTL.

    Caches function results based on arguments. Cached results expire
    after the specified TTL.

    Args:
        ttl_minutes: Time-to-live in minutes (default: 5)
        ttl: Time-to-live in seconds (alias for ttl_minutes, converts to minutes)

    Returns:
        Decorator function
    """
    # Handle both ttl (in seconds) and ttl_minutes (in minutes)
    if ttl is not None:
        ttl_minutes_value = ttl / 60.0
    elif ttl_minutes is not None:
        ttl_minutes_value = ttl_minutes
    else:
        ttl_minutes_value = 5

    def decorator(func: Callable) -> Callable:
        """Actual decorator."""
        cache = TTLCache(ttl_minutes=ttl_minutes_value)
        stats = {"hits": 0, "misses": 0}
        stats_lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper with caching."""
            # Create cache key from args and kwargs
            try:
                # Try to hash args and kwargs
                key = (args, tuple(sorted(kwargs.items())))
                # Verify the key is actually hashable
                hash(key)
            except TypeError:
                # Unhashable arguments - skip cache
                return func(*args, **kwargs)

            # Try to get from cache
            try:
                found, cached_value = cache.get(key)
                if found:
                    with stats_lock:
                        stats["hits"] += 1
                    return cached_value
            except TypeError:
                # If cache.get fails due to unhashable key, skip cache
                return func(*args, **kwargs)

            # Call function and cache result
            result = func(*args, **kwargs)
            try:
                cache.set(key, result)
            except TypeError:
                # If cache.set fails, just return result without caching
                pass

            with stats_lock:
                stats["misses"] += 1

            return result

        def cache_clear() -> None:
            """Clear the cache."""
            cache.clear()
            with stats_lock:
                stats["hits"] = 0
                stats["misses"] = 0

        def cache_stats() -> Dict[str, Any]:
            """Get cache statistics."""
            with stats_lock:
                total = stats["hits"] + stats["misses"]
                hit_rate = (stats["hits"] / total * 100) if total > 0 else 0

                return {
                    "hits": stats["hits"],
                    "misses": stats["misses"],
                    "total_calls": total,
                    "hit_rate": f"{hit_rate:.1f}%",
                    "ttl_minutes": ttl_minutes,
                }

        def cache_info() -> str:
            """Get readable cache info string."""
            stats_dict = cache_stats()
            return (
                f"Cache: {len(cache._cache)} entries, "
                f"hit rate {stats_dict['hit_rate']}, "
                f"TTL {ttl_minutes} minutes"
            )

        # Attach cache management methods
        wrapper.cache_clear = cache_clear  # type: ignore
        wrapper.cache_stats = cache_stats  # type: ignore
        wrapper.cache_info = cache_info  # type: ignore
        wrapper._cache = cache  # type: ignore

        return wrapper

    return decorator


__all__ = [
    "serialize_datetime",
    "deserialize_datetime",
    "ProjectIDGenerator",
    "UserIDGenerator",
    "TTLCache",
    "cached",
]
