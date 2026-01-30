"""
Cache Manager for API responses.

Supports multiple backends (Redis, file-based, in-memory) with TTL and automatic expiration.
Thread-safe implementation for production use.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL (seconds)."""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend using dict (thread-safe)."""
    
    def __init__(self, max_items: int = 1000):
        """Initialize memory cache with size limit."""
        self._cache: dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = threading.Lock()
        self._max_items = max_items
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, return None if expired or not found."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check expiration
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL."""
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_items and key not in self._cache:
                # Remove first (oldest) item
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            expiry = time.time() + ttl if ttl is not None else None
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None


class FileCacheBackend(CacheBackend):
    """File-based cache backend (thread-safe, persistent across restarts)."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """Initialize file cache with directory."""
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def _get_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache file."""
        path = self._get_path(key)
        
        with self._lock:
            if not path.exists():
                return None
            
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                
                value, expiry = data["value"], data["expiry"]
                
                # Check expiration
                if expiry is not None and time.time() > expiry:
                    path.unlink()
                    return None
                
                return value
            except Exception:
                # Corrupt cache file, delete it
                path.unlink(missing_ok=True)
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache file."""
        path = self._get_path(key)
        expiry = time.time() + ttl if ttl is not None else None
        
        with self._lock:
            try:
                with open(path, "wb") as f:
                    pickle.dump({"value": value, "expiry": expiry}, f)
            except Exception:
                # Failed to write, ignore
                pass
    
    def delete(self, key: str):
        """Delete cache file."""
        path = self._get_path(key)
        with self._lock:
            path.unlink(missing_ok=True)
    
    def clear(self):
        """Clear all cache files."""
        with self._lock:
            for path in self._cache_dir.glob("*.cache"):
                path.unlink(missing_ok=True)
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None


class RedisCacheBackend(CacheBackend):
    """Redis cache backend (requires redis package)."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        """Initialize Redis cache connection."""
        try:
            import redis
            self._redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False
            )
            # Test connection
            self._redis.ping()
        except ImportError:
            raise ImportError("redis package required for Redis cache. Install: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            data = self._redis.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis with optional TTL."""
        try:
            data = pickle.dumps(value)
            if ttl is not None:
                self._redis.setex(key, ttl, data)
            else:
                self._redis.set(key, data)
        except Exception:
            pass
    
    def delete(self, key: str):
        """Delete key from Redis."""
        try:
            self._redis.delete(key)
        except Exception:
            pass
    
    def clear(self):
        """Clear all keys in current Redis DB."""
        try:
            self._redis.flushdb()
        except Exception:
            pass
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(self._redis.exists(key))
        except Exception:
            return False


class CacheManager:
    """
    High-level cache manager with automatic backend selection and key generation.
    """
    
    def __init__(self, backend: Optional[CacheBackend] = None):
        """
        Initialize cache manager.
        
        Args:
            backend: Cache backend instance (auto-detect from config if None).
        """
        if backend is None:
            backend = self._create_backend_from_config()
        self._backend = backend
    
    def _create_backend_from_config(self) -> CacheBackend:
        """Create cache backend based on configuration."""
        from signal_triage.config import get_config
        config = get_config()
        
        backend_type = config.cache.backend.lower()
        
        if backend_type == "redis":
            return RedisCacheBackend(
                host=config.cache.redis_host,
                port=config.cache.redis_port,
                db=config.cache.redis_db,
                password=config.cache.redis_password
            )
        elif backend_type == "file":
            return FileCacheBackend(config.cache.file_cache_dir)
        elif backend_type == "memory":
            return MemoryCacheBackend(config.cache.max_memory_cache_items)
        else:
            # Default to file cache
            return FileCacheBackend()
    
    def make_key(self, provider: str, endpoint: str, **params) -> str:
        """
        Generate cache key from provider, endpoint, and parameters.
        
        Args:
            provider: Provider name (e.g., "sec_edgar", "fred").
            endpoint: API endpoint or function name.
            **params: Parameters used in API call (sorted for consistency).
        
        Returns:
            Cache key string.
        """
        # Sort params for consistent key generation
        param_str = json.dumps(params, sort_keys=True)
        return f"{provider}:{endpoint}:{param_str}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key.
        
        Returns:
            Cached value or None if not found/expired.
        """
        return self._backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache (must be serializable).
            ttl: Time-to-live in seconds (None = no expiration).
        """
        self._backend.set(key, value, ttl)
    
    def get_or_fetch(self, key: str, fetch_func, ttl: Optional[int] = None) -> Any:
        """
        Get from cache or fetch and cache if not found.
        
        Args:
            key: Cache key.
            fetch_func: Callable to fetch data if not in cache.
            ttl: Time-to-live for cached result.
        
        Returns:
            Cached or freshly fetched data.
        """
        # Try cache first
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Fetch and cache
        result = fetch_func()
        self.set(key, result, ttl)
        return result
    
    def delete(self, key: str):
        """Delete key from cache."""
        self._backend.delete(key)
    
    def clear(self):
        """Clear all cache entries."""
        self._backend.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self._backend.exists(key)


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get global cache manager instance (singleton pattern).
    
    Returns:
        CacheManager instance.
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
