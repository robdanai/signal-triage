"""
Circuit Breaker Pattern for API calls.

Prevents cascading failures by automatically stopping requests to failing services
and allowing them time to recover.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are blocked
- HALF_OPEN: Testing if service has recovered
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Callable, Optional, Any


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for API calls.
    
    Tracks failures and automatically opens circuit when threshold is exceeded.
    After timeout, enters half-open state to test recovery.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit.
            recovery_timeout: Seconds to wait before attempting recovery (half-open).
            expected_exception: Exception type to count as failures.
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._update_state()
            return self._state
    
    def _update_state(self):
        """Update circuit state based on failures and timeout."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self._last_failure_time is not None and
                time.time() - self._last_failure_time >= self._recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._failure_count = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute.
            *args: Positional arguments for function.
            **kwargs: Keyword arguments for function.
        
        Returns:
            Result of function call.
        
        Raises:
            CircuitBreakerError: If circuit is open.
            Exception: Any exception raised by the function.
        """
        with self._lock:
            self._update_state()
            
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry after {self._recovery_timeout} seconds."
                )
            
            # Half-open: allow one request to test recovery
            if self._state == CircuitState.HALF_OPEN:
                pass  # Allow request through
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self._expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test, reopen circuit
                self._state = CircuitState.OPEN
    
    def reset(self):
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._state = CircuitState.CLOSED
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get circuit breaker statistics.
        
        Returns:
            Dict with state, failure_count, last_failure_time.
        """
        with self._lock:
            self._update_state()
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "last_failure_time": self._last_failure_time,
                "failure_threshold": self._failure_threshold,
                "recovery_timeout": self._recovery_timeout,
            }


# Global circuit breakers for each provider
_circuit_breakers: dict[str, CircuitBreaker] = {}
_circuit_breakers_lock = threading.Lock()


def get_circuit_breaker(provider: str) -> CircuitBreaker:
    """
    Get circuit breaker for a provider (creates if not exists).
    
    Args:
        provider: Provider identifier (e.g., "sec_edgar", "fred").
    
    Returns:
        CircuitBreaker instance for the provider.
    """
    with _circuit_breakers_lock:
        if provider not in _circuit_breakers:
            from signal_triage.config import get_config
            config = get_config()
            
            _circuit_breakers[provider] = CircuitBreaker(
                failure_threshold=config.api.circuit_breaker_failure_threshold,
                recovery_timeout=config.api.circuit_breaker_recovery_timeout,
                expected_exception=config.api.circuit_breaker_expected_exception
            )
        
        return _circuit_breakers[provider]
