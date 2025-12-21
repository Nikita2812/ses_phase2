"""
Intelligent Retry Manager with Exponential Backoff

Handles transient failures with:
- Exponential backoff strategy
- Configurable retry limits
- Transient error detection
- Jitter to prevent thundering herd
- Comprehensive retry event logging
"""

import asyncio
import random
import time
import logging
from typing import Callable, Any, Tuple, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Classification of error types"""
    TRANSIENT = "transient"  # Temporary errors that may succeed on retry
    PERMANENT = "permanent"  # Errors that won't be fixed by retrying
    TIMEOUT = "timeout"      # Timeout errors
    UNKNOWN = "unknown"      # Unclassified errors


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    retry_count: int = 0  # Number of retry attempts (0 = no retry)
    base_delay_seconds: float = 1.0  # Initial delay before first retry
    max_delay_seconds: float = 60.0  # Maximum delay between retries
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add random jitter to delays
    retry_on_timeout: bool = True  # Retry on timeout errors
    retry_on_transient_only: bool = True  # Only retry transient errors

    def __post_init__(self):
        """Validate configuration"""
        if self.retry_count < 0 or self.retry_count > 10:
            raise ValueError("retry_count must be between 0 and 10")
        if self.base_delay_seconds < 0.1 or self.base_delay_seconds > 60.0:
            raise ValueError("base_delay_seconds must be between 0.1 and 60.0")
        if self.max_delay_seconds < 1.0 or self.max_delay_seconds > 3600.0:
            raise ValueError("max_delay_seconds must be between 1.0 and 3600.0")
        if self.exponential_base < 1.1 or self.exponential_base > 10.0:
            raise ValueError("exponential_base must be between 1.1 and 10.0")


@dataclass
class RetryAttempt:
    """Information about a single retry attempt"""

    attempt_number: int  # 1-based attempt number
    error_type: ErrorType
    error_message: str
    delay_seconds: float  # Delay before this attempt
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetryMetadata:
    """Metadata about retry execution"""

    total_attempts: int  # Total number of attempts (including initial)
    successful: bool
    final_error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    total_delay_seconds: float = 0.0
    attempts: List[RetryAttempt] = field(default_factory=list)


class RetryManager:
    """
    Manages intelligent retry logic with exponential backoff

    Features:
    - Exponential backoff with configurable parameters
    - Transient error detection
    - Jitter to prevent synchronized retries
    - Comprehensive logging
    - Async/await support
    """

    # Patterns that indicate transient errors
    TRANSIENT_ERROR_PATTERNS = [
        # Network errors
        "connection refused",
        "connection timeout",
        "connection reset",
        "connection aborted",
        "connection error",
        "temporary failure in name resolution",
        "network is unreachable",
        "host is unreachable",
        "no route to host",

        # HTTP errors (transient status codes)
        "429 too many requests",
        "500 internal server error",
        "502 bad gateway",
        "503 service unavailable",
        "504 gateway timeout",

        # Database errors (transient)
        "lock wait timeout exceeded",
        "deadlock found",
        "too many connections",
        "connection pool exhausted",
        "database is locked",

        # API rate limits
        "rate limit exceeded",
        "quota exceeded",
        "throttled",
        "too many requests",

        # Timeout indicators
        "timeout",
        "timed out",
        "deadline exceeded",
    ]

    # Errors that should never be retried
    PERMANENT_ERROR_PATTERNS = [
        "authentication failed",
        "unauthorized",
        "forbidden",
        "not found",
        "permission denied",
        "invalid argument",
        "invalid input",
        "validation error",
        "schema validation failed",
        "bad request",
        "invalid api key",
    ]

    def __init__(self):
        """Initialize retry manager"""
        self.retry_stats: Dict[str, int] = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "transient_errors": 0,
            "permanent_errors": 0,
        }

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify an error as transient or permanent

        Args:
            error: Exception to classify

        Returns:
            ErrorType classification
        """
        error_message = str(error).lower()

        # Check for timeout errors
        if isinstance(error, asyncio.TimeoutError) or "timeout" in error_message:
            return ErrorType.TIMEOUT

        # Check for permanent errors first (take precedence)
        for pattern in self.PERMANENT_ERROR_PATTERNS:
            if pattern.lower() in error_message:
                logger.debug(f"Classified as PERMANENT: {pattern} in {error_message}")
                return ErrorType.PERMANENT

        # Check for transient errors
        for pattern in self.TRANSIENT_ERROR_PATTERNS:
            if pattern.lower() in error_message:
                logger.debug(f"Classified as TRANSIENT: {pattern} in {error_message}")
                return ErrorType.TRANSIENT

        # Unknown classification - default to permanent to be safe
        logger.warning(f"Unknown error type: {error_message}")
        return ErrorType.UNKNOWN

    def calculate_backoff_delay(self, attempt: int, config: RetryConfig) -> float:
        """
        Calculate delay with exponential backoff and optional jitter

        Formula: delay = min(base_delay * (exponential_base ^ attempt), max_delay)

        Args:
            attempt: Attempt number (1-based)
            config: Retry configuration

        Returns:
            Delay in seconds

        Example with defaults (base=1.0, exp_base=2.0, max=60.0):
            Attempt 1: 2.0s
            Attempt 2: 4.0s
            Attempt 3: 8.0s
            Attempt 4: 16.0s
            Attempt 5: 32.0s
            Attempt 6+: 60.0s (capped)
        """
        # Calculate exponential delay
        delay = config.base_delay_seconds * (config.exponential_base ** attempt)

        # Cap at maximum
        delay = min(delay, config.max_delay_seconds)

        # Add jitter if enabled (50-100% of calculated delay)
        if config.jitter:
            jitter_factor = 0.5 + random.random() * 0.5
            delay *= jitter_factor

        logger.debug(f"Calculated backoff delay for attempt {attempt}: {delay:.2f}s")
        return delay

    def should_retry(
        self,
        error: Exception,
        attempt: int,
        config: RetryConfig,
        error_type: ErrorType
    ) -> bool:
        """
        Determine if an error should be retried

        Args:
            error: Exception that occurred
            attempt: Current attempt number (1-based)
            config: Retry configuration
            error_type: Classified error type

        Returns:
            True if should retry, False otherwise
        """
        # Check if retries are exhausted
        if attempt > config.retry_count:
            logger.info(f"Max retries ({config.retry_count}) exceeded")
            return False

        # Check error type constraints
        if error_type == ErrorType.PERMANENT:
            logger.info("Permanent error detected, not retrying")
            return False

        if error_type == ErrorType.TIMEOUT and not config.retry_on_timeout:
            logger.info("Timeout error and retry_on_timeout=False, not retrying")
            return False

        if error_type == ErrorType.UNKNOWN and config.retry_on_transient_only:
            logger.info("Unknown error and retry_on_transient_only=True, not retrying")
            return False

        logger.info(f"Will retry (attempt {attempt}/{config.retry_count})")
        return True

    async def execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig,
        *args,
        **kwargs
    ) -> Tuple[Any, RetryMetadata]:
        """
        Execute a function with retry logic

        Args:
            func: Async function to execute
            config: Retry configuration
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Tuple of (result, retry_metadata)

        Raises:
            Exception: The final exception if all retries failed
        """
        metadata = RetryMetadata(
            total_attempts=0,
            successful=False,
            attempts=[]
        )

        last_error: Optional[Exception] = None
        last_error_type: Optional[ErrorType] = None

        # Initial attempt + retries
        max_attempts = 1 + config.retry_count
        start_time = time.time()

        for attempt in range(1, max_attempts + 1):
            metadata.total_attempts = attempt

            try:
                logger.info(f"Executing function (attempt {attempt}/{max_attempts})")

                # Execute the function
                result = await func(*args, **kwargs)

                # Success!
                metadata.successful = True
                metadata.total_delay_seconds = time.time() - start_time

                if attempt > 1:
                    # Succeeded after retry
                    self.retry_stats["successful_retries"] += 1
                    logger.info(f"✅ Function succeeded on attempt {attempt} after {len(metadata.attempts)} retries")
                else:
                    logger.info("✅ Function succeeded on first attempt")

                return result, metadata

            except Exception as e:
                last_error = e
                last_error_type = self.classify_error(e)

                logger.warning(f"❌ Attempt {attempt} failed: {str(e)[:200]}")
                logger.debug(f"Error type: {last_error_type}")

                # Update stats
                if last_error_type == ErrorType.TRANSIENT:
                    self.retry_stats["transient_errors"] += 1
                elif last_error_type == ErrorType.PERMANENT:
                    self.retry_stats["permanent_errors"] += 1

                # Check if we should retry
                if attempt < max_attempts:
                    should_retry = self.should_retry(e, attempt, config, last_error_type)

                    if should_retry:
                        # Calculate backoff delay
                        delay = self.calculate_backoff_delay(attempt, config)
                        metadata.total_delay_seconds += delay

                        # Record retry attempt
                        retry_attempt = RetryAttempt(
                            attempt_number=attempt + 1,
                            error_type=last_error_type,
                            error_message=str(e),
                            delay_seconds=delay
                        )
                        metadata.attempts.append(retry_attempt)

                        logger.info(f"⏳ Waiting {delay:.2f}s before retry {attempt + 1}...")

                        # Wait before retry
                        await asyncio.sleep(delay)

                        self.retry_stats["total_retries"] += 1
                    else:
                        # Should not retry, fail immediately
                        logger.error(f"Not retrying: {last_error_type} error")
                        break

        # All attempts failed
        metadata.successful = False
        metadata.final_error = str(last_error) if last_error else "Unknown error"
        metadata.error_type = last_error_type
        metadata.total_delay_seconds = time.time() - start_time

        self.retry_stats["failed_retries"] += 1

        logger.error(
            f"❌ Function failed after {metadata.total_attempts} attempts "
            f"({metadata.total_delay_seconds:.2f}s total)"
        )

        # Re-raise the last error
        if last_error:
            raise last_error
        else:
            raise RuntimeError("Function failed with unknown error")

    def get_stats(self) -> Dict[str, int]:
        """
        Get retry statistics

        Returns:
            Dictionary of retry stats
        """
        return self.retry_stats.copy()

    def reset_stats(self):
        """Reset retry statistics"""
        for key in self.retry_stats:
            self.retry_stats[key] = 0


# Utility function for easy retry decoration
def with_retry(config: RetryConfig):
    """
    Decorator for adding retry logic to async functions

    Args:
        config: Retry configuration

    Example:
        @with_retry(RetryConfig(retry_count=3, base_delay_seconds=1.0))
        async def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            manager = RetryManager()
            result, metadata = await manager.execute_with_retry(func, config, *args, **kwargs)
            return result
        return wrapper
    return decorator
