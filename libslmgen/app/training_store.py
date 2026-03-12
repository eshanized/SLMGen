#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis Streams-Based Training Store.

Production-grade training progress tracking using Redis Streams and JSON state.

Architecture:
    - Each training session has its own Redis Stream: training:{session_id}:events
    - State snapshots stored as Redis JSON: training:{session_id}:state
    - Streams are capped (MAXLEN ~1000) to prevent unbounded growth
    - State snapshot updated on every event for fast reads
    - SSE streaming uses XREAD BLOCK for efficient real-time updates

Why Redis Streams:
    1. Append-only log - events never lost, can replay
    2. Consumer groups - multiple clients can consume independently
    3. Range queries - XRANGE for historical data
    4. Blocking reads - XREAD BLOCK for SSE without polling
    5. Persistence - survives restarts unlike in-memory dict
    6. Horizontal scaling - any Redis node can serve reads

Tradeoffs vs In-Memory:
    - Slight latency overhead (Redis round-trip)
    - Requires Redis running (added dependency)
    - More complex than dict.get()
    + Survives restarts
    + Multiple backend instances share state
    + Event history preserved for debugging
    + Real streaming without polling

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, AsyncGenerator, Optional

import orjson
import redis.asyncio as aioredis
from fastapi import HTTPException

from .config import settings

logger = logging.getLogger(__name__)

# Redis key patterns
_KEY_PREFIX = "training:"
_EVENTS_SUFFIX = ":events"
_STATE_SUFFIX = ":state"

# Stream configuration
MAX_STREAM_LENGTH = 1000  # Cap stream to prevent unbounded growth
SSE_BLOCK_MS = 2000  # XREAD BLOCK timeout for SSE
SSE_POLL_INTERVAL = 1.0  # Fallback polling interval in seconds

# Regex for validating session IDs (UUID v4)
_SESSION_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class TrainingStatus(str, Enum):
    """Status of a training session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _validate_session_id(session_id: str) -> None:
    """
    Validate session_id is a well-formed UUID v4.
    
    Raises:
        HTTPException(400): If session_id format is invalid.
    """
    if not isinstance(session_id, str) or not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")


def _redis_error_handler(func):
    """
    Decorator to catch Redis errors and convert to HTTP 503.
    
    Prevents leaking internal Redis errors to clients.
    """
    import asyncio
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        """Wrapper for sync calls - used for both regular and async functions."""
        try:
            result = func(*args, **kwargs)
            # If result is a coroutine, wrap it in an async function
            if asyncio.iscoroutine(result):
                async def async_wrapper():
                    try:
                        return await result
                    except HTTPException:
                        raise
                    except aioredis.ConnectionError as e:
                        logger.error(f"Redis connection error in {func.__name__}: {e}")
                        raise HTTPException(
                            status_code=503,
                            detail="Training service temporarily unavailable. Please try again later.",
                        )
                    except aioredis.RedisError as e:
                        logger.error(f"Redis error in {func.__name__}: {e}")
                        raise HTTPException(
                            status_code=503,
                            detail="Training service temporarily unavailable. Please try again later.",
                        )
                    except Exception as e:
                        logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                        raise HTTPException(
                            status_code=503,
                            detail="Training service temporarily unavailable. Please try again later.",
                        )
                return async_wrapper()
            # For non-coroutine results (like sync returns or generators), 
            # we just return them - errors would propagate normally
            return result
        except HTTPException:
            raise
        except aioredis.ConnectionError as e:
            logger.error(f"Redis connection error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=503,
                detail="Training service temporarily unavailable. Please try again later.",
            )
        except aioredis.RedisError as e:
            logger.error(f"Redis error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=503,
                detail="Training service temporarily unavailable. Please try again later.",
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Training service temporarily unavailable. Please try again later.",
            )
    return sync_wrapper


def _now_iso() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _make_events_key(session_id: str) -> str:
    """Build the Redis Stream key for a session's events."""
    return f"{_KEY_PREFIX}{session_id}{_EVENTS_SUFFIX}"


def _make_state_key(session_id: str) -> str:
    """Build the Redis key for a session's state snapshot."""
    return f"{_KEY_PREFIX}{session_id}{_STATE_SUFFIX}"


def _serialize(data: dict) -> bytes:
    """Serialize data using orjson."""
    return orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS)


def _deserialize(raw: bytes) -> dict:
    """Deserialize data using orjson."""
    return orjson.loads(raw)


def _estimate_eta(
    current_step: int,
    total_steps: int,
    events: list[dict],
) -> Optional[dict]:
    """
    Estimate time remaining based on recent event pace.
    
    Returns dict with 'seconds' and 'formatted' keys, or None if insufficient data.
    """
    if len(events) < 2:
        return None
    
    # Use last 20 events to calculate pace
    recent = events[-min(20, len(events)):]
    first = recent[0]
    last = recent[-1]
    
    # Parse timestamps
    try:
        t_first = datetime.fromisoformat(first.get("timestamp", _now_iso()))
        t_last = datetime.fromisoformat(last.get("timestamp", _now_iso()))
    except (ValueError, TypeError):
        return None
    
    time_diff = (t_last - t_first).total_seconds()
    steps_diff = last.get("step", 0) - first.get("step", 0)
    
    if steps_diff <= 0 or time_diff <= 0:
        return None
    
    steps_per_second = steps_diff / time_diff
    remaining_steps = total_steps - current_step
    
    if remaining_steps <= 0:
        return None
    
    eta_seconds = remaining_steps / steps_per_second
    
    # Format ETA
    total_seconds = int(eta_seconds)
    if total_seconds < 60:
        formatted = f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted = f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        formatted = f"{hours}h {minutes}m"
    
    return {"seconds": eta_seconds, "formatted": formatted}


class RedisTrainingStore:
    """
    Redis Streams-based training progress store.
    
    Provides:
    - Persistent event logs via Redis Streams (XADD)
    - Fast state snapshots via Redis JSON
    - Real-time SSE streaming via XREAD BLOCK
    - Horizontal scalability (any Redis node)
    
    Usage:
        store = RedisTrainingStore(redis_url="redis://localhost:6379/0")
        await store.connect()
        
        await store.start_session(session_id, metadata)
        await store.add_event(session_id, event_data)
        
        async for event in store.stream_events(session_id, last_id):
            print(event)
        
        await store.close()
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_stream_length: int = MAX_STREAM_LENGTH,
        block_ms: int = SSE_BLOCK_MS,
    ):
        self._redis_url = redis_url
        self._max_stream_length = max_stream_length
        self._block_ms = block_ms
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """
        Initialize the Redis connection pool.
        
        Should be called once during application startup (FastAPI lifespan).
        """
        if self._redis is not None:
            return

        self._redis = aioredis.from_url(
            self._redis_url,
            decode_responses=False,
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

        try:
            await self._redis.ping()
            logger.info(f"Training store Redis connected: {self._redis_url}")
        except Exception as e:
            logger.error(f"Training store Redis connection failed: {e}")
            self._redis = None
            raise

    async def close(self) -> None:
        """
        Close the Redis connection pool.
        
        Should be called during application shutdown.
        """
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            logger.info("Training store Redis connection closed")

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        if self._redis is None:
            return False
        try:
            return await self._redis.ping()
        except Exception:
            return False

    def _require_connection(self) -> aioredis.Redis:
        """Get Redis client, raising 503 if not connected."""
        if self._redis is None:
            raise HTTPException(
                status_code=503,
                detail="Training service not initialized. Please try again later.",
            )
        return self._redis

    @_redis_error_handler
    async def start_session(
        self,
        session_id: str,
        metadata: dict,
    ) -> None:
        """
        Start a new training session.
        
        Creates both the stream and state snapshot for a session.
        
        Args:
            session_id: UUID of the training session (must be UUID v4).
            metadata: Dict with job_id, model_id, total_steps, total_epochs.
        
        Raises:
            HTTPException(400): If session_id format is invalid.
            HTTPException(409): If session already exists.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        events_key = _make_events_key(session_id)
        state_key = _make_state_key(session_id)
        
        # Check if session already exists
        existing = await r.exists(state_key)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Training session already exists.",
            )
        
        now = _now_iso()
        
        # Initialize state snapshot
        state = {
            "session_id": session_id,
            "job_id": metadata.get("job_id", ""),
            "model_id": metadata.get("model_id", ""),
            "total_steps": metadata.get("total_steps", 0),
            "total_epochs": metadata.get("total_epochs", 1),
            "status": TrainingStatus.RUNNING.value,
            "current_step": 0,
            "current_epoch": 0,
            "progress_percent": 0.0,
            "latest_loss": None,
            "eta_seconds": None,
            "eta_formatted": None,
            "started_at": now,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "error_message": None,
            "event_count": 0,
        }
        
        # Store state as JSON (Redis JSON if available, otherwise string)
        pipe = r.pipeline()
        pipe.set(state_key, _serialize(state))
        pipe.expire(state_key, 7200)  # 2 hour TTL
        
        # Initialize empty stream (creates the key)
        # Use MAXLEN to cap size - approximate is fine for our use case
        pipe.xadd(events_key, {"init": "session_started"}, maxlen=self._max_stream_length, approximate=True)
        pipe.expire(events_key, 7200)  # 2 hour TTL
        
        await pipe.execute()
        
        logger.info(f"Started training session: {session_id}")

    @_redis_error_handler
    async def add_event(
        self,
        session_id: str,
        event: dict,
    ) -> str:
        """
        Add a training event to the session's stream and update state snapshot.
        
        Args:
            session_id: UUID of the training session.
            event: Dict with step, loss, epoch, learning_rate, etc.
        
        Returns:
            The Redis event ID (e.g., "1703123456789-0").
        
        Raises:
            HTTPException(404): If session does not exist.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        events_key = _make_events_key(session_id)
        state_key = _make_state_key(session_id)
        
        # Verify session exists
        if not await r.exists(state_key):
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )
        
        now = _now_iso()
        step = event.get("step", 0)
        loss = event.get("loss", 0.0)
        epoch = event.get("epoch", 0)
        learning_rate = event.get("learning_rate", 0.0)
        grad_norm = event.get("grad_norm")
        tokens_per_second = event.get("tokens_per_second")
        gpu_memory_used = event.get("gpu_memory_used")
        
        # Serialize event data for stream
        event_data = {
            "event": "progress",
            "timestamp": now,
            "step": str(step),
            "loss": str(loss),
            "epoch": str(epoch),
            "learning_rate": str(learning_rate),
            "grad_norm": str(grad_norm) if grad_norm is not None else "",
            "tokens_per_second": str(tokens_per_second) if tokens_per_second is not None else "",
            "gpu_memory_used": str(gpu_memory_used) if gpu_memory_used is not None else "",
        }
        
        # Add to stream with MAXLEN cap
        event_id = await r.xadd(
            events_key,
            event_data,
            maxlen=self._max_stream_length,
            approximate=True,
        )
        
        # Handle bytes from Redis
        if isinstance(event_id, bytes):
            event_id = event_id.decode("utf-8")
        
        # Get recent events for ETA calculation
        recent_events = await self.get_events(session_id, limit=20)
        
        # Calculate ETA
        eta_info = _estimate_eta(step, event.get("total_steps", 0), recent_events)
        
        # Update state snapshot
        state_raw = await r.get(state_key)
        if state_raw:
            state = _deserialize(state_raw)
        else:
            state = {}
        
        state["updated_at"] = now
        state["current_step"] = step
        state["current_epoch"] = epoch
        state["latest_loss"] = loss
        state["event_count"] = state.get("event_count", 0) + 1
        
        # Calculate progress
        total_steps = state.get("total_steps", 0)
        if total_steps > 0:
            state["progress_percent"] = min(100.0, (step / total_steps) * 100)
        else:
            state["progress_percent"] = 0.0
        
        if eta_info:
            state["eta_seconds"] = eta_info["seconds"]
            state["eta_formatted"] = eta_info["formatted"]
        
        # If this is the first event, set started_at
        if state.get("status") == TrainingStatus.PENDING.value:
            state["status"] = TrainingStatus.RUNNING.value
            state["started_at"] = now
        
        await r.set(state_key, _serialize(state))
        
        logger.debug(f"Added event to session {session_id}: step={step}, loss={loss:.4f}")
        
        return event_id

    @_redis_error_handler
    async def complete_session(
        self,
        session_id: str,
        error: Optional[str] = None,
    ) -> None:
        """
        Mark a training session as completed or failed.
        
        Args:
            session_id: UUID of the training session.
            error: If provided, marks session as failed with this error message.
        
        Raises:
            HTTPException(404): If session does not exist.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        state_key = _make_state_key(session_id)
        events_key = _make_events_key(session_id)
        
        if not await r.exists(state_key):
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )
        
        now = _now_iso()
        state_raw = await r.get(state_key)
        
        if state_raw:
            state = _deserialize(state_raw)
        else:
            state = {}
        
        if error:
            state["status"] = TrainingStatus.FAILED.value
            state["error_message"] = error
            event_type = "error"
        else:
            state["status"] = TrainingStatus.COMPLETED.value
            state["progress_percent"] = 100.0
            event_type = "complete"
        
        state["updated_at"] = now
        state["completed_at"] = now
        state["eta_seconds"] = None
        state["eta_formatted"] = None
        
        await r.set(state_key, _serialize(state))
        
        # Add completion event to stream
        await r.xadd(
            events_key,
            {
                "event": event_type,
                "timestamp": now,
                "step": str(state.get("current_step", 0)),
                "loss": str(state.get("latest_loss", 0.0)),
                "epoch": str(state.get("current_epoch", 0)),
                "error": error or "",
            },
            maxlen=self._max_stream_length,
            approximate=True,
        )
        
        logger.info(f"Training session {session_id} marked as {state['status']}")

    @_redis_error_handler
    async def get_state(self, session_id: str) -> Optional[dict]:
        """
        Get the current state snapshot for a session.
        
        This is the fast path for status queries.
        
        Returns:
            State dict if session exists, None otherwise.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        state_key = _make_state_key(session_id)
        state_raw = await r.get(state_key)
        
        if state_raw is None:
            return None
        
        return _deserialize(state_raw)

    @_redis_error_handler
    async def get_events(
        self,
        session_id: str,
        limit: int = 100,
        after_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Get events from a session's stream.
        
        Args:
            session_id: UUID of the training session.
            limit: Maximum number of events to return (default 100).
            after_id: Return events after this ID (exclusive). Use for pagination.
        
        Returns:
            List of event dicts, newest first if using XREVRANGE.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        events_key = _make_events_key(session_id)
        
        # Use XREVRANGE for newest-first (most recent events first)
        if after_id:
            # Events after a specific ID (exclusive)
            events = await r.xrange(events_key, min=after_id, max="+", count=limit)
        else:
            # Get last N events (newest first)
            events = await r.xrevrange(events_key, max="+", min="-", count=limit)
        
        result = []
        for event_id, data in events:
            # Normalize data dict to use string keys (fakeredis may return bytes keys)
            normalized = {}
            for k, v in data.items():
                if isinstance(k, bytes):
                    k = k.decode("utf-8")
                normalized[k] = v
            
            data = normalized
            
            # Filter out init events
            if data.get("init"):
                continue
            
            # Handle bytes from Redis
            if isinstance(event_id, bytes):
                event_id = event_id.decode("utf-8")
            
            # Helper functions for parsing
            def get_str(key: str) -> str:
                val = data.get(key)
                if isinstance(val, bytes):
                    return val.decode("utf-8")
                return val or ""
            
            def get_float(key: str) -> float:
                val = data.get(key)
                if isinstance(val, bytes):
                    val = val.decode("utf-8")
                if val is None or val == "":
                    return 0.0
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0.0
            
            def get_int(key: str) -> int:
                val = data.get(key)
                if isinstance(val, bytes):
                    val = val.decode("utf-8")
                if val is None or val == "":
                    return 0
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    return 0
                except (ValueError, TypeError):
                    return 0
            
            event = {
                "id": event_id,
                "event": get_str("event") or "progress",
                "timestamp": get_str("timestamp"),
                "step": get_int("step"),
                "loss": get_float("loss"),
                "epoch": get_int("epoch"),
                "learning_rate": get_float("learning_rate"),
            }
            
            # Optional fields
            grad_norm = get_str("grad_norm")
            if grad_norm:
                event["grad_norm"] = float(grad_norm)
            
            tps = get_str("tokens_per_second")
            if tps:
                event["tokens_per_second"] = float(tps)
            
            gpu_mem = get_str("gpu_memory_used")
            if gpu_mem:
                event["gpu_memory_used"] = float(gpu_mem)
            
            error_str = get_str("error")
            if error_str:
                event["error"] = error_str
            
            result.append(event)
        
        return result

    @_redis_error_handler
    async def get_latest(self, session_id: str) -> Optional[dict]:
        """
        Get the most recent event from a session.
        
        Returns:
            The latest event dict, or None if no events.
        """
        events = await self.get_events(session_id, limit=1)
        return events[0] if events else None

    @_redis_error_handler
    async def stream_events(
        self,
        session_id: str,
        last_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream events from a session using Redis XREAD BLOCK.
        
        This is the SSE backend implementation. Uses blocking reads
        to efficiently wait for new events without polling.
        
        Args:
            session_id: UUID of the training session.
            last_id: Only return events after this ID. If None, returns
                    current state immediately then blocks for new events.
        
        Yields:
            Event dicts as they arrive.
        
        Note:
            This is an async generator. Caller must iterate with `async for`.
            The generator will continue until the session completes/fails
            or the caller breaks out.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        events_key = _make_events_key(session_id)
        
        # Track the last seen event ID
        current_id = last_id if last_id else "$"  # "$" means only new events
        
        # First, check if session exists
        state = await self.get_state(session_id)
        if state is None:
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )
        
        # If no last_id, yield current state immediately
        if last_id is None:
            yield {
                "type": "state",
                "data": state,
            }
        
        # Stream loop
        while True:
            try:
                # XREAD BLOCK waits for new events
                # Returns dict of stream -> [(id, data), ...]
                result = await r.xread(
                    {events_key: current_id},
                    block=self._block_ms,
                    count=100,
                )
                
                if not result:
                    # Timeout - no new events, send heartbeat
                    yield {"type": "heartbeat", "data": None}
                    continue
                
                for stream_key, events in result:
                    for event_id, data in events:
                        # Skip the init event
                        if data.get("init"):
                            current_id = event_id
                            continue
                        
                        current_id = event_id
                        
                        event = {
                            "type": "event",
                            "id": event_id,
                            "event": data.get("event", "progress"),
                            "timestamp": data.get("timestamp", ""),
                            "step": int(data.get("step", 0) or 0),
                            "loss": float(data.get("loss", 0.0) or 0.0),
                            "epoch": int(data.get("epoch", 0) or 0),
                            "learning_rate": float(data.get("learning_rate", 0.0) or 0.0),
                        }
                        
                        if data.get("grad_norm"):
                            event["grad_norm"] = float(data["grad_norm"])
                        if data.get("tokens_per_second"):
                            event["tokens_per_second"] = float(data["tokens_per_second"])
                        if data.get("gpu_memory_used"):
                            event["gpu_memory_used"] = float(data["gpu_memory_used"])
                        if data.get("error"):
                            event["error"] = data["error"]
                        
                        yield event
                
                # Check if session is complete
                state = await self.get_state(session_id)
                if state and state.get("status") in (
                    TrainingStatus.COMPLETED.value,
                    TrainingStatus.FAILED.value,
                ):
                    yield {
                        "type": "complete",
                        "data": state,
                    }
                    break
                    
            except asyncio.CancelledError:
                # Client disconnected
                logger.info(f"Client disconnected from stream: {session_id}")
                break
            except Exception as e:
                logger.error(f"Error in stream loop for {session_id}: {e}")
                yield {"type": "error", "data": str(e)}
                break

    @_redis_error_handler
    async def list_sessions(self) -> list[dict]:
        """
        List all active training sessions.
        
        Uses SCAN to find all state keys efficiently.
        
        Returns:
            List of session state dicts.
        """
        r = self._require_connection()
        
        sessions = []
        cursor = 0
        
        pattern = f"{_KEY_PREFIX}*{_STATE_SUFFIX}"
        
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
            
            for key in keys:
                state_raw = await r.get(key)
                if state_raw:
                    sessions.append(_deserialize(state_raw))
            
            if cursor == 0:
                break
        
        return sessions

    @_redis_error_handler
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a training session and all its data.
        
        This is idempotent - deleting a nonexistent session is a no-op.
        
        Args:
            session_id: UUID of the training session.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        events_key = _make_events_key(session_id)
        state_key = _make_state_key(session_id)
        
        pipe = r.pipeline()
        pipe.delete(events_key)
        pipe.delete(state_key)
        await pipe.execute()
        
        logger.info(f"Deleted training session: {session_id}")

    @_redis_error_handler
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a training session exists.
        
        Args:
            session_id: UUID of the training session.
        
        Returns:
            True if session exists, False otherwise.
        """
        _validate_session_id(session_id)
        r = self._require_connection()
        
        state_key = _make_state_key(session_id)
        return await r.exists(state_key) > 0


# ---------------------------------------------------------------------------
# Global singleton instance
# ---------------------------------------------------------------------------
training_store = RedisTrainingStore(
    redis_url=settings.redis_url,
)
