"""
Timeout Manager for Step Execution

Provides timeout enforcement with:
- Per-step timeout configuration
- Graceful cancellation
- Fallback value support
- Timeout event logging
- Context cleanup
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TimeoutStrategy(str, Enum):
    """Strategy when timeout occurs"""
    FAIL = "fail"          # Raise TimeoutError
    FALLBACK = "fallback"  # Use fallback value
    SKIP = "skip"          # Skip step and continue


@dataclass
class TimeoutConfig:
    """Configuration for timeout behavior"""

    timeout_seconds: float  # Timeout duration
    strategy: TimeoutStrategy = TimeoutStrategy.FAIL
    fallback_value: Optional[Any] = None
    cleanup_callback: Optional[Callable] = None  # Called on timeout for cleanup


@dataclass
class TimeoutResult:
    """Result of timeout-enforced execution"""

    success: bool
    result: Optional[Any]
    timed_out: bool
    execution_time_seconds: float
    timeout_seconds: float
    error_message: Optional[str] = None


class TimeoutManager:
    """
    Manages timeout enforcement for async operations

    Features:
    - Configurable timeout per operation
    - Graceful cancellation
    - Fallback value support
    - Cleanup callbacks
    - Comprehensive logging
    """

    def __init__(self):
        """Initialize timeout manager"""
        self.timeout_stats = {
            "total_executions": 0,
            "timeouts": 0,
            "successful": 0,
            "failed_non_timeout": 0,
            "fallbacks_used": 0,
        }

    async def execute_with_timeout(
        self,
        func: Callable,
        config: TimeoutConfig,
        *args,
        **kwargs
    ) -> TimeoutResult:
        """
        Execute async function with timeout enforcement

        Args:
            func: Async function to execute
            config: Timeout configuration
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            TimeoutResult with execution outcome
        """
        start_time = asyncio.get_event_loop().time()
        self.timeout_stats["total_executions"] += 1

        try:
            # Execute with timeout
            logger.debug(f"Executing with {config.timeout_seconds}s timeout")

            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=config.timeout_seconds
            )

            # Success
            execution_time = asyncio.get_event_loop().time() - start_time
            self.timeout_stats["successful"] += 1

            logger.debug(f"✅ Execution completed in {execution_time:.3f}s")

            return TimeoutResult(
                success=True,
                result=result,
                timed_out=False,
                execution_time_seconds=execution_time,
                timeout_seconds=config.timeout_seconds
            )

        except asyncio.TimeoutError:
            # Timeout occurred
            execution_time = asyncio.get_event_loop().time() - start_time
            self.timeout_stats["timeouts"] += 1

            logger.warning(
                f"⏱️  Timeout after {execution_time:.3f}s "
                f"(limit: {config.timeout_seconds}s)"
            )

            # Execute cleanup if provided
            if config.cleanup_callback:
                try:
                    if asyncio.iscoroutinefunction(config.cleanup_callback):
                        await config.cleanup_callback()
                    else:
                        config.cleanup_callback()
                    logger.debug("Cleanup callback executed")
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")

            # Handle based on strategy
            if config.strategy == TimeoutStrategy.FALLBACK and config.fallback_value is not None:
                # Use fallback value
                self.timeout_stats["fallbacks_used"] += 1
                logger.info(f"Using fallback value: {config.fallback_value}")

                return TimeoutResult(
                    success=True,
                    result=config.fallback_value,
                    timed_out=True,
                    execution_time_seconds=execution_time,
                    timeout_seconds=config.timeout_seconds
                )

            elif config.strategy == TimeoutStrategy.SKIP:
                # Skip and continue
                logger.info("Skipping step due to timeout")

                return TimeoutResult(
                    success=False,
                    result=None,
                    timed_out=True,
                    execution_time_seconds=execution_time,
                    timeout_seconds=config.timeout_seconds,
                    error_message=f"Step skipped: timeout after {config.timeout_seconds}s"
                )

            else:
                # Fail (raise error)
                return TimeoutResult(
                    success=False,
                    result=None,
                    timed_out=True,
                    execution_time_seconds=execution_time,
                    timeout_seconds=config.timeout_seconds,
                    error_message=f"Timeout after {config.timeout_seconds}s"
                )

        except asyncio.CancelledError:
            # Task was cancelled externally
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.warning(f"Task cancelled after {execution_time:.3f}s")
            raise  # Re-raise cancellation

        except Exception as e:
            # Other error (not timeout)
            execution_time = asyncio.get_event_loop().time() - start_time
            self.timeout_stats["failed_non_timeout"] += 1

            logger.error(f"❌ Execution failed after {execution_time:.3f}s: {e}")

            return TimeoutResult(
                success=False,
                result=None,
                timed_out=False,
                execution_time_seconds=execution_time,
                timeout_seconds=config.timeout_seconds,
                error_message=str(e)
            )

    def get_stats(self) -> Dict[str, int]:
        """
        Get timeout statistics

        Returns:
            Dictionary of timeout stats
        """
        return self.timeout_stats.copy()

    def reset_stats(self):
        """Reset timeout statistics"""
        for key in self.timeout_stats:
            self.timeout_stats[key] = 0


# Utility function for simple timeout
async def with_timeout(
    func: Callable,
    timeout_seconds: float,
    *args,
    **kwargs
) -> Any:
    """
    Simple timeout wrapper (raises TimeoutError on timeout)

    Args:
        func: Async function to execute
        timeout_seconds: Timeout duration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout
    """
    return await asyncio.wait_for(
        func(*args, **kwargs),
        timeout=timeout_seconds
    )


# Utility function for timeout with fallback
async def with_timeout_fallback(
    func: Callable,
    timeout_seconds: float,
    fallback_value: Any,
    *args,
    **kwargs
) -> Any:
    """
    Timeout wrapper with fallback value

    Args:
        func: Async function to execute
        timeout_seconds: Timeout duration
        fallback_value: Value to return on timeout
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from func or fallback_value on timeout
    """
    manager = TimeoutManager()
    config = TimeoutConfig(
        timeout_seconds=timeout_seconds,
        strategy=TimeoutStrategy.FALLBACK,
        fallback_value=fallback_value
    )

    result = await manager.execute_with_timeout(func, config, *args, **kwargs)
    return result.result


# Decorator for timeout enforcement
def timeout(seconds: float, fallback: Optional[Any] = None):
    """
    Decorator for adding timeout to async functions

    Args:
        seconds: Timeout duration
        fallback: Optional fallback value (if None, raises TimeoutError)

    Example:
        @timeout(30.0)
        async def fetch_data():
            # Your code here
            pass

        @timeout(10.0, fallback=[])
        async def get_items():
            # Returns [] if timeout occurs
            pass
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            manager = TimeoutManager()

            if fallback is not None:
                config = TimeoutConfig(
                    timeout_seconds=seconds,
                    strategy=TimeoutStrategy.FALLBACK,
                    fallback_value=fallback
                )
            else:
                config = TimeoutConfig(
                    timeout_seconds=seconds,
                    strategy=TimeoutStrategy.FAIL
                )

            result = await manager.execute_with_timeout(func, config, *args, **kwargs)

            if not result.success and not result.timed_out:
                # Non-timeout error, raise original exception
                raise RuntimeError(result.error_message)
            elif result.timed_out and fallback is None:
                # Timeout with no fallback, raise TimeoutError
                raise asyncio.TimeoutError(f"Function timed out after {seconds}s")

            return result.result

        return wrapper
    return decorator
