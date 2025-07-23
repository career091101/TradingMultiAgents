"""Retry handler with circuit breaker pattern for LLM calls"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Type, Union, List
from dataclasses import dataclass, field
from enum import Enum
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: timedelta = timedelta(minutes=1)  # Time before half-open
    success_threshold: int = 3  # Successes in half-open before closing
    
    
@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    min_wait: float = 1.0  # Min wait between retries (seconds)
    max_wait: float = 60.0  # Max wait between retries (seconds)
    multiplier: float = 2.0  # Exponential backoff multiplier
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError
    ])


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker")
        
    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker entering HALF_OPEN state")
                return False
            return True
        return False
        
    def record_success(self) -> None:
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.logger.info("Circuit breaker CLOSED - recovered successfully")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset on success
            
    def record_failure(self) -> None:
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning("Circuit breaker OPEN - half-open test failed")
        elif self.state == CircuitState.CLOSED and \
             self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker OPEN - {self.failure_count} failures")
            
    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state


class RetryHandler:
    """Handles retries with circuit breaker pattern"""
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None
    ):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_config or CircuitBreakerConfig())
        self.logger = logging.getLogger(f"{__name__}.RetryHandler")
        
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic and circuit breaker"""
        
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            raise ConnectionError("Circuit breaker is OPEN - service unavailable")
            
        # Create retry decorator
        retry_decorator = retry(
            stop=stop_after_attempt(self.retry_config.max_attempts),
            wait=wait_exponential(
                multiplier=self.retry_config.multiplier,
                min=self.retry_config.min_wait,
                max=self.retry_config.max_wait
            ),
            retry=retry_if_exception_type(tuple(self.retry_config.retryable_exceptions)),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
            after=after_log(self.logger, logging.INFO)
        )
        
        try:
            # Execute with retry
            result = await retry_decorator(func)(*args, **kwargs)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            self.logger.error(f"All retry attempts failed: {e}")
            raise
            
    def add_retryable_exception(self, exception_type: Type[Exception]) -> None:
        """Add an exception type to retry on"""
        if exception_type not in self.retry_config.retryable_exceptions:
            self.retry_config.retryable_exceptions.append(exception_type)
            
    def get_circuit_state(self) -> Dict[str, Any]:
        """Get circuit breaker state info"""
        return {
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "success_count": self.circuit_breaker.success_count,
            "last_failure": self.circuit_breaker.last_failure_time.isoformat() 
                           if self.circuit_breaker.last_failure_time else None
        }


class LLMRetryHandler(RetryHandler):
    """Specialized retry handler for LLM calls"""
    
    def __init__(self):
        # LLM-specific configuration
        retry_config = RetryConfig(
            max_attempts=3,
            min_wait=2.0,
            max_wait=30.0,
            multiplier=2.0,
            retryable_exceptions=[
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
                # Add OpenAI specific exceptions when available
            ]
        )
        
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=timedelta(minutes=2),
            success_threshold=2
        )
        
        super().__init__(retry_config, circuit_config)
        
    def is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error"""
        error_str = str(error).lower()
        return any(indicator in error_str for indicator in [
            "rate limit",
            "429",
            "too many requests"
        ])
        
    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable"""
        # Check standard retryable types
        if isinstance(error, tuple(self.retry_config.retryable_exceptions)):
            return True
            
        # Check for rate limit errors
        if self.is_rate_limit_error(error):
            return True
            
        # Check for specific error messages
        error_str = str(error).lower()
        retryable_messages = [
            "timeout",
            "connection",
            "unavailable",
            "500",
            "502",
            "503",
            "504"
        ]
        
        return any(msg in error_str for msg in retryable_messages)