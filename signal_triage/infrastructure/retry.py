"""
Retry Strategy for API calls.

Implements exponential backoff with jitter for transient failures.
Configurable retry attempts and backoff parameters.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, Any, Optional


logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    Exponential backoff retry strategy with jitter.
    
    Automatically retries failed calls with increasing delays.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retryable_exceptions: tuple[type, ...] = (Exception,),
        retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts.
            backoff_factor: Exponential backoff multiplier (delay *= backoff_factor).
            initial_delay: Initial retry delay in seconds.
            max_delay: Maximum retry delay in seconds.
            jitter: Add random jitter to delay to avoid thundering herd.
            retryable_exceptions: Exception types to retry.
            retryable_status_codes: HTTP status codes to retry (for requests).
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.retryable_status_codes = retryable_status_codes
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate retry delay for attempt number.
        
        Args:
            attempt: Current attempt number (0-indexed).
        
        Returns:
            Delay in seconds (with optional jitter).
        """
        delay = min(
            self.initial_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add jitter: delay * random(0.5, 1.5)
            delay *= (0.5 + random.random())
        
        return delay
    
    def _is_retryable(self, exception: Exception) -> bool:
        """
        Check if exception is retryable.
        
        Args:
            exception: Exception that was raised.
        
        Returns:
            True if should retry, False otherwise.
        """
        # Check if exception type is retryable
        if not isinstance(exception, self.retryable_exceptions):
            return False
        
        # For requests HTTPError, check status code
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            status_code = exception.response.status_code
            return status_code in self.retryable_status_codes
        
        # For other exceptions, retry if it's in retryable_exceptions
        return True
    
    def call(
        self,
        func: Callable,
        *args,
        on_retry: Optional[Callable[[Exception, int, float], None]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute.
            *args: Positional arguments for function.
            on_retry: Optional callback called on each retry (exception, attempt, delay).
            **kwargs: Keyword arguments for function.
        
        Returns:
            Result of function call.
        
        Raises:
            Exception: Last exception if all retries exhausted.
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Don't retry if exception is not retryable
                if not self._is_retryable(e):
                    logger.debug(f"Exception not retryable: {type(e).__name__}: {e}")
                    raise
                
                # Don't retry if this was the last attempt
                if attempt >= self.max_retries:
                    logger.warning(
                        f"Max retries ({self.max_retries}) exhausted for {func.__name__}. "
                        f"Last error: {type(e).__name__}: {e}"
                    )
                    raise
                
                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                logger.info(
                    f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} "
                    f"after {delay:.2f}s. Error: {type(e).__name__}: {e}"
                )
                
                # Call retry callback if provided
                if on_retry:
                    try:
                        on_retry(e, attempt + 1, delay)
                    except Exception as callback_error:
                        logger.warning(f"on_retry callback failed: {callback_error}")
                
                time.sleep(delay)
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic error: no exception but all attempts failed")


def create_retry_strategy_from_config() -> RetryStrategy:
    """
    Create retry strategy from global configuration.
    
    Returns:
        RetryStrategy instance configured from config.
    """
    from signal_triage.config import get_config
    config = get_config()
    
    return RetryStrategy(
        max_retries=config.api.max_retries,
        backoff_factor=config.api.retry_backoff_factor,
        initial_delay=1.0,
        max_delay=60.0,
        jitter=True,
        retryable_exceptions=(Exception,),
        retryable_status_codes=config.api.retry_statuses
    )


# Global retry strategy instance
_retry_strategy: Optional[RetryStrategy] = None


def get_retry_strategy() -> RetryStrategy:
    """
    Get global retry strategy instance (singleton pattern).
    
    Returns:
        RetryStrategy instance.
    """
    global _retry_strategy
    if _retry_strategy is None:
        _retry_strategy = create_retry_strategy_from_config()
    return _retry_strategy
