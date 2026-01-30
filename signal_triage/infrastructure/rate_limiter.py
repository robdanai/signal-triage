"""
Rate Limiter for API calls.

Implements token bucket algorithm to prevent exceeding API rate limits.
Thread-safe and supports per-provider rate limiting.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a provider."""
    requests_per_period: int
    period_seconds: float = 1.0  # Default: requests per second


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Thread-safe implementation that enforces rate limits per provider.
    """
    
    def __init__(self):
        """Initialize rate limiter with empty buckets."""
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._buckets: dict[str, float] = {}
        self._last_update: dict[str, float] = {}
        self._config: dict[str, RateLimitConfig] = {}
    
    def configure(self, provider: str, requests_per_period: int, period_seconds: float = 1.0):
        """
        Configure rate limit for a provider.
        
        Args:
            provider: Provider identifier (e.g., "sec_edgar", "fred").
            requests_per_period: Maximum requests allowed per period.
            period_seconds: Period duration in seconds (default: 1.0 = per second).
        
        Examples:
            limiter.configure("sec_edgar", 10, 1.0)  # 10 requests per second
            limiter.configure("fred", 120, 60.0)  # 120 requests per minute
        """
        with self._locks[provider]:
            self._config[provider] = RateLimitConfig(requests_per_period, period_seconds)
            self._buckets[provider] = float(requests_per_period)
            self._last_update[provider] = time.time()
    
    def acquire(self, provider: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from rate limit bucket (blocking).
        
        Args:
            provider: Provider identifier.
            tokens: Number of tokens to acquire (default: 1 for single request).
            timeout: Maximum time to wait in seconds (None = wait indefinitely).
        
        Returns:
            True if tokens acquired, False if timeout exceeded.
        
        Raises:
            ValueError: If provider not configured.
        """
        if provider not in self._config:
            raise ValueError(f"Rate limiter not configured for provider: {provider}")
        
        start_time = time.time()
        
        with self._locks[provider]:
            config = self._config[provider]
            
            while True:
                # Refill bucket based on elapsed time
                now = time.time()
                elapsed = now - self._last_update[provider]
                refill_rate = config.requests_per_period / config.period_seconds
                self._buckets[provider] = min(
                    config.requests_per_period,
                    self._buckets[provider] + (elapsed * refill_rate)
                )
                self._last_update[provider] = now
                
                # Try to acquire tokens
                if self._buckets[provider] >= tokens:
                    self._buckets[provider] -= tokens
                    return True
                
                # Check timeout
                if timeout is not None and (time.time() - start_time) >= timeout:
                    return False
                
                # Calculate wait time
                tokens_needed = tokens - self._buckets[provider]
                wait_time = tokens_needed / refill_rate
                time.sleep(min(wait_time, 0.1))  # Sleep in small increments
    
    def try_acquire(self, provider: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.
        
        Args:
            provider: Provider identifier.
            tokens: Number of tokens to acquire.
        
        Returns:
            True if tokens acquired immediately, False otherwise.
        """
        return self.acquire(provider, tokens, timeout=0.0)
    
    def get_available_tokens(self, provider: str) -> float:
        """
        Get current number of available tokens for a provider.
        
        Args:
            provider: Provider identifier.
        
        Returns:
            Number of available tokens (may be fractional).
        """
        if provider not in self._config:
            return 0.0
        
        with self._locks[provider]:
            now = time.time()
            elapsed = now - self._last_update[provider]
            config = self._config[provider]
            refill_rate = config.requests_per_period / config.period_seconds
            return min(
                config.requests_per_period,
                self._buckets[provider] + (elapsed * refill_rate)
            )
    
    def reset(self, provider: str):
        """
        Reset rate limit bucket for a provider (fill to capacity).
        
        Args:
            provider: Provider identifier.
        """
        if provider not in self._config:
            return
        
        with self._locks[provider]:
            self._buckets[provider] = float(self._config[provider].requests_per_period)
            self._last_update[provider] = time.time()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance (singleton pattern).
    
    Returns:
        RateLimiter instance.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        # Configure default rate limits from config
        from signal_triage.config import get_config
        config = get_config()
        
        _rate_limiter.configure("sec_edgar", config.api.sec_rate_limit, 1.0)
        _rate_limiter.configure("fred", config.api.fred_rate_limit, 60.0)
        _rate_limiter.configure("alphavantage", config.api.alphavantage_rate_limit, 60.0)
        _rate_limiter.configure("iexcloud", config.api.iexcloud_rate_limit, 1.0)
        _rate_limiter.configure("ninefin", config.api.ninefin_rate_limit, 60.0)
        _rate_limiter.configure("bloomberg", config.api.bloomberg_rate_limit, 60.0)
    
    return _rate_limiter
