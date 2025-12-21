"""
Streaming Manager for Real-Time Progress Updates

Provides real-time execution updates via:
- WebSocket broadcasting
- Server-Sent Events (SSE)
- In-memory event streams
- Progress tracking
- Error streaming
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Set, AsyncIterator
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """Types of stream events"""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_SKIPPED = "step_skipped"
    PROGRESS_UPDATE = "progress_update"
    LOG_MESSAGE = "log_message"
    ERROR_MESSAGE = "error_message"


@dataclass
class StreamEvent:
    """Single stream event"""

    event_type: StreamEventType
    execution_id: str
    timestamp: str  # ISO format
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event": self.event_type.value,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp,
            "data": self.data
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class StreamingManager:
    """
    Manages real-time execution event streaming

    Features:
    - Multi-subscriber support (many clients per execution)
    - Event history buffering
    - Automatic cleanup of old streams
    - WebSocket and SSE compatible
    - Thread-safe event broadcasting
    """

    def __init__(self, max_history: int = 1000, cleanup_after_seconds: int = 3600):
        """
        Initialize streaming manager

        Args:
            max_history: Maximum events to keep in history per execution
            cleanup_after_seconds: Auto-cleanup streams after this duration
        """
        self.max_history = max_history
        self.cleanup_after_seconds = cleanup_after_seconds

        # Subscribers: execution_id -> set of callbacks
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)

        # Event history: execution_id -> list of events
        self.event_history: Dict[str, List[StreamEvent]] = defaultdict(list)

        # Event queues for async iteration: execution_id -> asyncio.Queue
        self.event_queues: Dict[str, asyncio.Queue] = {}

        # Stream metadata
        self.stream_metadata: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.stats = {
            "total_streams": 0,
            "active_streams": 0,
            "total_events": 0,
            "total_subscribers": 0,
        }

    async def create_stream(self, execution_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a new event stream for an execution

        Args:
            execution_id: Unique execution identifier
            metadata: Optional metadata about the execution
        """
        if execution_id in self.stream_metadata:
            logger.warning(f"Stream {execution_id} already exists")
            return

        self.stream_metadata[execution_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "status": "active"
        }

        self.event_queues[execution_id] = asyncio.Queue()
        self.stats["total_streams"] += 1
        self.stats["active_streams"] += 1

        logger.info(f"📡 Created stream for execution {execution_id}")

    async def broadcast_event(self, execution_id: str, event: StreamEvent):
        """
        Broadcast event to all subscribers

        Args:
            execution_id: Execution identifier
            event: Event to broadcast
        """
        # Add to history
        history = self.event_history[execution_id]
        history.append(event)

        # Trim history if too large
        if len(history) > self.max_history:
            self.event_history[execution_id] = history[-self.max_history:]

        self.stats["total_events"] += 1

        # Add to queue for async iteration
        if execution_id in self.event_queues:
            await self.event_queues[execution_id].put(event)

        # Broadcast to subscribers
        subscribers = self.subscribers.get(execution_id, set())
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Subscriber callback failed: {e}")

        logger.debug(f"📤 Broadcasted {event.event_type} to {len(subscribers)} subscribers")

    async def broadcast_execution_started(
        self,
        execution_id: str,
        total_steps: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Broadcast execution started event"""
        event = StreamEvent(
            event_type=StreamEventType.EXECUTION_STARTED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "total_steps": total_steps,
                **(metadata or {})
            }
        )
        await self.broadcast_event(execution_id, event)

    async def broadcast_execution_completed(
        self,
        execution_id: str,
        total_time_ms: float,
        output: Optional[Dict[str, Any]] = None
    ):
        """Broadcast execution completed event"""
        event = StreamEvent(
            event_type=StreamEventType.EXECUTION_COMPLETED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "total_time_ms": total_time_ms,
                "output": output
            }
        )
        await self.broadcast_event(execution_id, event)

        # Mark stream as completed
        if execution_id in self.stream_metadata:
            self.stream_metadata[execution_id]["status"] = "completed"

    async def broadcast_execution_failed(
        self,
        execution_id: str,
        error_message: str,
        error_step: Optional[int] = None
    ):
        """Broadcast execution failed event"""
        event = StreamEvent(
            event_type=StreamEventType.EXECUTION_FAILED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "error_message": error_message,
                "error_step": error_step
            }
        )
        await self.broadcast_event(execution_id, event)

        # Mark stream as failed
        if execution_id in self.stream_metadata:
            self.stream_metadata[execution_id]["status"] = "failed"

    async def broadcast_step_started(
        self,
        execution_id: str,
        step_number: int,
        step_name: str
    ):
        """Broadcast step started event"""
        event = StreamEvent(
            event_type=StreamEventType.STEP_STARTED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "step_number": step_number,
                "step_name": step_name
            }
        )
        await self.broadcast_event(execution_id, event)

    async def broadcast_step_completed(
        self,
        execution_id: str,
        step_number: int,
        step_name: str,
        execution_time_ms: float,
        output: Optional[Dict[str, Any]] = None
    ):
        """Broadcast step completed event"""
        event = StreamEvent(
            event_type=StreamEventType.STEP_COMPLETED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "step_number": step_number,
                "step_name": step_name,
                "execution_time_ms": execution_time_ms,
                "output": output
            }
        )
        await self.broadcast_event(execution_id, event)

    async def broadcast_step_failed(
        self,
        execution_id: str,
        step_number: int,
        step_name: str,
        error_message: str
    ):
        """Broadcast step failed event"""
        event = StreamEvent(
            event_type=StreamEventType.STEP_FAILED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "step_number": step_number,
                "step_name": step_name,
                "error_message": error_message
            }
        )
        await self.broadcast_event(execution_id, event)

    async def broadcast_progress_update(
        self,
        execution_id: str,
        completed_steps: int,
        total_steps: int,
        progress_percent: float
    ):
        """Broadcast progress update event"""
        event = StreamEvent(
            event_type=StreamEventType.PROGRESS_UPDATE,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "completed_steps": completed_steps,
                "total_steps": total_steps,
                "progress_percent": progress_percent
            }
        )
        await self.broadcast_event(execution_id, event)

    async def broadcast_log_message(
        self,
        execution_id: str,
        level: str,
        message: str
    ):
        """Broadcast log message event"""
        event = StreamEvent(
            event_type=StreamEventType.LOG_MESSAGE,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "level": level,
                "message": message
            }
        )
        await self.broadcast_event(execution_id, event)

    def subscribe(self, execution_id: str, callback: Callable):
        """
        Subscribe to execution events

        Args:
            execution_id: Execution identifier
            callback: Callback function (sync or async)
                     Signature: def callback(event: StreamEvent)
        """
        self.subscribers[execution_id].add(callback)
        self.stats["total_subscribers"] += 1
        logger.info(f"➕ Subscriber added to execution {execution_id}")

    def unsubscribe(self, execution_id: str, callback: Callable):
        """
        Unsubscribe from execution events

        Args:
            execution_id: Execution identifier
            callback: Callback function to remove
        """
        if execution_id in self.subscribers:
            self.subscribers[execution_id].discard(callback)
            self.stats["total_subscribers"] -= 1
            logger.info(f"➖ Subscriber removed from execution {execution_id}")

    async def stream_events(self, execution_id: str) -> AsyncIterator[StreamEvent]:
        """
        Async iterator for execution events

        Args:
            execution_id: Execution identifier

        Yields:
            StreamEvent objects as they occur

        Example:
            async for event in manager.stream_events(execution_id):
                print(f"Event: {event.event_type}")
        """
        # Send event history first
        for event in self.event_history.get(execution_id, []):
            yield event

        # Then stream new events
        if execution_id not in self.event_queues:
            logger.warning(f"No event queue for execution {execution_id}")
            return

        queue = self.event_queues[execution_id]

        try:
            while True:
                # Get event from queue (with timeout to allow checking stream status)
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event

                    # Check if execution is complete
                    metadata = self.stream_metadata.get(execution_id, {})
                    if metadata.get("status") in ["completed", "failed"]:
                        # Drain remaining events then stop
                        while not queue.empty():
                            yield queue.get_nowait()
                        break

                except asyncio.TimeoutError:
                    # Check if stream still active
                    metadata = self.stream_metadata.get(execution_id, {})
                    if metadata.get("status") in ["completed", "failed"]:
                        break
                    continue

        finally:
            logger.info(f"Stream ended for execution {execution_id}")

    def get_event_history(self, execution_id: str) -> List[StreamEvent]:
        """
        Get event history for an execution

        Args:
            execution_id: Execution identifier

        Returns:
            List of historical events
        """
        return self.event_history.get(execution_id, []).copy()

    async def close_stream(self, execution_id: str):
        """
        Close stream and cleanup resources

        Args:
            execution_id: Execution identifier
        """
        # Remove subscribers
        if execution_id in self.subscribers:
            del self.subscribers[execution_id]

        # Clear event queue
        if execution_id in self.event_queues:
            del self.event_queues[execution_id]

        # Keep metadata and history for a while (for replay)
        if execution_id in self.stream_metadata:
            self.stream_metadata[execution_id]["status"] = "closed"
            self.stream_metadata[execution_id]["closed_at"] = datetime.utcnow().isoformat()

        self.stats["active_streams"] -= 1

        logger.info(f"🔒 Closed stream for execution {execution_id}")

    async def cleanup_old_streams(self):
        """Cleanup old completed/failed streams"""
        now = datetime.utcnow()
        to_remove = []

        for execution_id, metadata in self.stream_metadata.items():
            if metadata.get("status") in ["closed", "completed", "failed"]:
                created_at = datetime.fromisoformat(metadata["created_at"])
                age_seconds = (now - created_at).total_seconds()

                if age_seconds > self.cleanup_after_seconds:
                    to_remove.append(execution_id)

        for execution_id in to_remove:
            # Remove from all collections
            self.event_history.pop(execution_id, None)
            self.stream_metadata.pop(execution_id, None)
            self.subscribers.pop(execution_id, None)
            self.event_queues.pop(execution_id, None)

            logger.info(f"🗑️  Cleaned up old stream {execution_id}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get streaming statistics

        Returns:
            Dictionary of streaming stats
        """
        return {
            **self.stats,
            "event_history_size": sum(len(h) for h in self.event_history.values()),
            "active_subscribers": sum(len(s) for s in self.subscribers.values()),
        }


# Global streaming manager instance
_global_streaming_manager: Optional[StreamingManager] = None


def get_streaming_manager() -> StreamingManager:
    """
    Get global streaming manager instance

    Returns:
        StreamingManager singleton
    """
    global _global_streaming_manager
    if _global_streaming_manager is None:
        _global_streaming_manager = StreamingManager()
    return _global_streaming_manager
