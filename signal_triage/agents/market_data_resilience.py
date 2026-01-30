"""
Production resilience features: rate limiting, circuit breakers, metrics.

Critical for production deployment to prevent:
- Rate limit exhaustion
- Cascading failures
- Resource waste on failing APIs
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ===== Rate Limit Tracking =====


class RateLimiter:
    """
    Track API usage against rate limits.
    
    Prevents exhausting free tier limits:
    - Alpha Vantage: 25/day
    - Polygon: 5/minute
    - FMP: 250/day
    - Finnhub: 60/minute
    """
    
    def __init__(self):
        self._daily_counts: dict[str, deque] = defaultdict(lambda: deque())
        self._minute_counts: dict[str, deque] = defaultdict(lambda: deque())
        self._lock = Lock()
        
        # Rate limit definitions
        self._limits = {
            'alphavantage': {'daily': 25, 'minute': None},
            'polygon': {'daily': None, 'minute': 5},
            'fmp': {'daily': 250, 'minute': None},
            'finnhub': {'daily': None, 'minute': 60},
            'fred': {'daily': None, 'minute': 120},  # Conservative estimate
            'sec_edgar': {'daily': None, 'minute': 10},  # SEC rate limiting
        }
    
    def can_make_request(self, api_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed within rate limits.
        
        Args:
            api_name: API identifier (e.g., 'alphavantage')
            
        Returns:
            (allowed, reason) tuple
        """
        with self._lock:
            now = time.time()
            limits = self._limits.get(api_name, {})
            
            # Check daily limit
            if limits.get('daily'):
                self._cleanup_old_requests(api_name, 'daily', now)
                if len(self._daily_counts[api_name]) >= limits['daily']:
                    return False, f"Daily limit reached ({limits['daily']}/day)"
            
            # Check minute limit
            if limits.get('minute'):
                self._cleanup_old_requests(api_name, 'minute', now)
                if len(self._minute_counts[api_name]) >= limits['minute']:
                    return False, f"Rate limit reached ({limits['minute']}/min)"
            
            return True, None
    
    def record_request(self, api_name: str):
        """Record that a request was made."""
        with self._lock:
            now = time.time()
            if self._limits.get(api_name, {}).get('daily'):
                self._daily_counts[api_name].append(now)
            if self._limits.get(api_name, {}).get('minute'):
                self._minute_counts[api_name].append(now)
    
    def _cleanup_old_requests(self, api_name: str, period: str, now: float):
        """Remove timestamps outside the window."""
        if period == 'daily':
            window = 86400  # 24 hours
            counts = self._daily_counts[api_name]
        else:  # minute
            window = 60
            counts = self._minute_counts[api_name]
        
        while counts and (now - counts[0]) > window:
            counts.popleft()
    
    def get_usage_stats(self, api_name: str) -> dict[str, Any]:
        """Get current usage statistics for an API."""
        with self._lock:
            now = time.time()
            self._cleanup_old_requests(api_name, 'daily', now)
            self._cleanup_old_requests(api_name, 'minute', now)
            
            limits = self._limits.get(api_name, {})
            return {
                'api': api_name,
                'daily_used': len(self._daily_counts[api_name]),
                'daily_limit': limits.get('daily'),
                'minute_used': len(self._minute_counts[api_name]),
                'minute_limit': limits.get('minute'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }


# Global rate limiter instance
_rate_limiter = RateLimiter()


def check_rate_limit(api_name: str) -> tuple[bool, Optional[str]]:
    """Check if API request is allowed."""
    return _rate_limiter.can_make_request(api_name)


def record_api_call(api_name: str):
    """Record that an API call was made."""
    _rate_limiter.record_request(api_name)


def get_rate_limit_stats(api_name: str) -> dict[str, Any]:
    """Get rate limit usage statistics."""
    return _rate_limiter.get_usage_stats(api_name)


# ===== Circuit Breaker =====


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent wasting resources on failing APIs.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, stop trying
    - HALF_OPEN: Testing recovery after cooldown
    
    Example:
        If Yahoo Finance fails 5 times in a row, stop trying for 60 seconds.
        After 60s, test with one request (HALF_OPEN).
        If succeeds, go back to CLOSED. If fails, stay OPEN for another 60s.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
    ):
        """
        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes needed in HALF_OPEN to close circuit
            timeout_seconds: How long to stay OPEN before testing recovery
        """
        self._state: dict[str, CircuitState] = defaultdict(lambda: CircuitState.CLOSED)
        self._failure_count: dict[str, int] = defaultdict(int)
        self._success_count: dict[str, int] = defaultdict(int)
        self._last_failure_time: dict[str, float] = {}
        self._lock = Lock()
        
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout_seconds
    
    def can_execute(self, api_name: str) -> tuple[bool, Optional[str]]:
        """
        Check if API call should be attempted.
        
        Returns:
            (allowed, reason) tuple
        """
        with self._lock:
            state = self._state[api_name]
            
            if state == CircuitState.CLOSED:
                return True, None
            
            if state == CircuitState.OPEN:
                # Check if enough time has passed to try recovery
                if api_name in self._last_failure_time:
                    elapsed = time.time() - self._last_failure_time[api_name]
                    if elapsed >= self._timeout:
                        # Transition to HALF_OPEN
                        self._state[api_name] = CircuitState.HALF_OPEN
                        self._success_count[api_name] = 0
                        logger.info(f"Circuit HALF_OPEN for {api_name} (testing recovery)")
                        return True, None
                
                return False, f"Circuit OPEN (failed {self._failure_count[api_name]} times)"
            
            # HALF_OPEN state
            return True, None
    
    def record_success(self, api_name: str):
        """Record successful API call."""
        with self._lock:
            state = self._state[api_name]
            
            if state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count[api_name] = 0
            
            elif state == CircuitState.HALF_OPEN:
                self._success_count[api_name] += 1
                if self._success_count[api_name] >= self._success_threshold:
                    # Recovery confirmed, close circuit
                    self._state[api_name] = CircuitState.CLOSED
                    self._failure_count[api_name] = 0
                    logger.info(f"✅ Circuit CLOSED for {api_name} (recovered)")
    
    def record_failure(self, api_name: str):
        """Record failed API call."""
        with self._lock:
            state = self._state[api_name]
            
            if state == CircuitState.CLOSED:
                self._failure_count[api_name] += 1
                if self._failure_count[api_name] >= self._failure_threshold:
                    # Open circuit
                    self._state[api_name] = CircuitState.OPEN
                    self._last_failure_time[api_name] = time.time()
                    logger.warning(
                        f"🚨 Circuit OPEN for {api_name} "
                        f"({self._failure_count[api_name]} failures, "
                        f"cooldown: {self._timeout}s)"
                    )
            
            elif state == CircuitState.HALF_OPEN:
                # Failed during recovery test, back to OPEN
                self._state[api_name] = CircuitState.OPEN
                self._last_failure_time[api_name] = time.time()
                self._success_count[api_name] = 0
                logger.warning(f"❌ Circuit OPEN for {api_name} (recovery test failed)")
    
    def get_status(self, api_name: str) -> dict[str, Any]:
        """Get circuit breaker status for an API."""
        with self._lock:
            state = self._state[api_name]
            return {
                'api': api_name,
                'state': state.value,
                'failure_count': self._failure_count[api_name],
                'success_count': self._success_count[api_name],
                'last_failure': self._last_failure_time.get(api_name),
                'can_execute': state != CircuitState.OPEN or (
                    time.time() - self._last_failure_time.get(api_name, 0) >= self._timeout
                ),
            }


# Global circuit breaker instance
_circuit_breaker = CircuitBreaker()


def check_circuit(api_name: str) -> tuple[bool, Optional[str]]:
    """Check if circuit breaker allows execution."""
    return _circuit_breaker.can_execute(api_name)


def record_success(api_name: str):
    """Record successful API call for circuit breaker."""
    _circuit_breaker.record_success(api_name)


def record_failure(api_name: str):
    """Record failed API call for circuit breaker."""
    _circuit_breaker.record_failure(api_name)


def get_circuit_status(api_name: str) -> dict[str, Any]:
    """Get circuit breaker status."""
    return _circuit_breaker.get_status(api_name)


# ===== Metrics Collection =====


class MetricsCollector:
    """
    Collect metrics on API performance.
    
    Tracks:
    - Success/failure counts
    - Latency (p50, p95, p99)
    - Error rates
    - Cache hit ratios
    """
    
    def __init__(self):
        self._success_counts: dict[str, int] = defaultdict(int)
        self._failure_counts: dict[str, int] = defaultdict(int)
        self._latencies: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._cache_hits: dict[str, int] = defaultdict(int)
        self._cache_misses: dict[str, int] = defaultdict(int)
        self._lock = Lock()
    
    def record_success(self, api_name: str, latency_ms: float):
        """Record successful API call with latency."""
        with self._lock:
            self._success_counts[api_name] += 1
            self._latencies[api_name].append(latency_ms)
    
    def record_failure(self, api_name: str):
        """Record failed API call."""
        with self._lock:
            self._failure_counts[api_name] += 1
    
    def record_cache_hit(self, api_name: str):
        """Record cache hit."""
        with self._lock:
            self._cache_hits[api_name] += 1
    
    def record_cache_miss(self, api_name: str):
        """Record cache miss."""
        with self._lock:
            self._cache_misses[api_name] += 1
    
    def get_metrics(self, api_name: str) -> dict[str, Any]:
        """Get metrics for an API."""
        with self._lock:
            total_calls = self._success_counts[api_name] + self._failure_counts[api_name]
            success_rate = (
                self._success_counts[api_name] / total_calls * 100
                if total_calls > 0 else 0
            )
            
            latencies = sorted(self._latencies[api_name])
            p50 = latencies[len(latencies) // 2] if latencies else None
            p95 = latencies[int(len(latencies) * 0.95)] if latencies else None
            p99 = latencies[int(len(latencies) * 0.99)] if latencies else None
            
            total_cache_ops = self._cache_hits[api_name] + self._cache_misses[api_name]
            cache_hit_rate = (
                self._cache_hits[api_name] / total_cache_ops * 100
                if total_cache_ops > 0 else 0
            )
            
            return {
                'api': api_name,
                'total_calls': total_calls,
                'success_count': self._success_counts[api_name],
                'failure_count': self._failure_counts[api_name],
                'success_rate_pct': round(success_rate, 2),
                'latency_p50_ms': round(p50, 2) if p50 else None,
                'latency_p95_ms': round(p95, 2) if p95 else None,
                'latency_p99_ms': round(p99, 2) if p99 else None,
                'cache_hits': self._cache_hits[api_name],
                'cache_misses': self._cache_misses[api_name],
                'cache_hit_rate_pct': round(cache_hit_rate, 2),
            }
    
    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all APIs."""
        apis = set(
            list(self._success_counts.keys()) +
            list(self._failure_counts.keys())
        )
        return {api: self.get_metrics(api) for api in apis}


# Global metrics collector
_metrics = MetricsCollector()


def record_api_success(api_name: str, latency_ms: float):
    """Record successful API call with latency."""
    _metrics.record_success(api_name, latency_ms)


def record_api_failure(api_name: str):
    """Record failed API call."""
    _metrics.record_failure(api_name)


def record_cache_hit(api_name: str):
    """Record cache hit."""
    _metrics.record_cache_hit(api_name)


def record_cache_miss(api_name: str):
    """Record cache miss."""
    _metrics.record_cache_miss(api_name)


def get_metrics(api_name: Optional[str] = None) -> dict[str, Any]:
    """
    Get metrics for API(s).
    
    Args:
        api_name: Specific API or None for all
        
    Returns:
        Metrics dict
    """
    if api_name:
        return _metrics.get_metrics(api_name)
    return _metrics.get_all_metrics()


# ===== Resilient API Call Wrapper =====


def resilient_api_call(
    api_name: str,
    func: Callable,
    *args,
    **kwargs
) -> tuple[Any, bool]:
    """
    Execute API call with full resilience:
    - Rate limit checking
    - Circuit breaker
    - Metrics collection
    - Automatic retries (via _retry_with_backoff)
    
    Args:
        api_name: API identifier for tracking
        func: Function to execute
        *args, **kwargs: Arguments to func
        
    Returns:
        (result, success) tuple
    """
    # Check rate limit
    allowed, reason = check_rate_limit(api_name)
    if not allowed:
        logger.warning(f"⚠️ Rate limit: {api_name} - {reason}")
        return {'error': f'Rate limit: {reason}', 'source': api_name}, False
    
    # Check circuit breaker
    allowed, reason = check_circuit(api_name)
    if not allowed:
        logger.warning(f"⚠️ Circuit breaker: {api_name} - {reason}")
        return {'error': f'Circuit breaker: {reason}', 'source': api_name}, False
    
    # Execute with metrics
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        latency_ms = (time.time() - start_time) * 1000
        
        # Record success
        record_api_call(api_name)
        record_success(api_name)
        record_api_success(api_name, latency_ms)
        
        logger.debug(f"✅ {api_name} succeeded ({latency_ms:.0f}ms)")
        return result, True
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        
        # Record failure
        record_failure(api_name)
        record_api_failure(api_name)
        
        logger.error(f"❌ {api_name} failed ({latency_ms:.0f}ms): {e}")
        return {'error': str(e), 'source': api_name}, False
