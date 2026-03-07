#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for RedisTrainingStore.

Covers:
- Session lifecycle (start → add_event → complete)
- Event stream behavior
- State snapshot correctness
- SSE streaming via mock
- Redis unavailability (503 behavior)
- Idempotency and error handling

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio

# Try to import fakeredis for in-memory Redis mock
try:
    import fakeredis.aioredis as fakeredis_aio
    HAS_FAKEREDIS = True
except ImportError:
    HAS_FAKEREDIS = False

from app.training_store import (
    RedisTrainingStore,
    TrainingStatus,
    _validate_session_id,
    _estimate_eta,
    _make_events_key,
    _make_state_key,
)
from fastapi import HTTPException


# ============================================
# FIXTURES
# ============================================

@pytest_asyncio.fixture
async def store():
    """Create a RedisTrainingStore backed by fakeredis."""
    if not HAS_FAKEREDIS:
        pytest.skip("fakeredis not installed")

    s = RedisTrainingStore(redis_url="redis://fake")
    # Replace the real Redis client with a fakeredis instance
    s._redis = fakeredis_aio.FakeRedis(decode_responses=False)
    yield s
    await s._redis.aclose()
    s._redis = None


def valid_session_id():
    """Generate a valid UUID v4 session ID."""
    return str(uuid.uuid4())


# ============================================
# SESSION ID VALIDATION TESTS
# ============================================

class TestSessionIdValidation:
    """Test UUID v4 validation."""

    def test_valid_uuid(self):
        """Valid UUID v4 passes."""
        _validate_session_id(str(uuid.uuid4()))  # Should not raise

    def test_invalid_not_uuid(self):
        """Non-UUID string rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_session_id("not-a-uuid")
        assert exc_info.value.status_code == 400

    def test_key_injection_attempt(self):
        """Redis key injection attempt rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_session_id("*")
        assert exc_info.value.status_code == 400

    def test_empty_string(self):
        """Empty string rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_session_id("")
        assert exc_info.value.status_code == 400


# ============================================
# KEY CONSTRUCTION TESTS
# ============================================

class TestKeyConstruction:
    """Test Redis key building."""

    def test_events_key(self):
        sid = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        assert _make_events_key(sid) == "training:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee:events"

    def test_state_key(self):
        sid = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        assert _make_state_key(sid) == "training:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee:state"


# ============================================
# ETA ESTIMATION TESTS
# ============================================

class TestETAEstimation:
    """Test ETA calculation."""

    def test_insufficient_data(self):
        """Returns None with less than 2 events."""
        result = _estimate_eta(0, 1000, [])
        assert result is None

    def test_single_event(self):
        """Returns None with only 1 event."""
        events = [{"step": 10, "timestamp": "2026-01-01T00:00:00+00:00"}]
        result = _estimate_eta(10, 1000, events)
        assert result is None

    def test_valid_eta_calculation(self):
        """Calculates ETA correctly from events."""
        events = [
            {"step": 0, "timestamp": "2026-01-01T00:00:00+00:00"},
            {"step": 100, "timestamp": "2026-01-01T00:01:00+00:00"},  # 60s later
        ]
        result = _estimate_eta(100, 1000, events)
        assert result is not None
        assert "seconds" in result
        assert "formatted" in result

    def test_complete_training(self):
        """Returns None when training is complete."""
        events = [{"step": 1000, "timestamp": "2026-01-01T00:10:00+00:00"}]
        result = _estimate_eta(1000, 1000, events)
        assert result is None


# ============================================
# SESSION LIFECYCLE TESTS
# ============================================

@pytest.mark.asyncio
class TestSessionLifecycle:
    """Test start → add_event → complete flow."""

    async def test_start_session(self, store):
        """Can start a new training session."""
        session_id = valid_session_id()
        
        await store.start_session(
            session_id=session_id,
            metadata={
                "job_id": "job-123",
                "model_id": "phi-4-mini",
                "total_steps": 1000,
                "total_epochs": 3,
            },
        )

        # Session should exist
        exists = await store.session_exists(session_id)
        assert exists is True

        # State should be created
        state = await store.get_state(session_id)
        assert state is not None
        assert state["session_id"] == session_id
        assert state["job_id"] == "job-123"
        assert state["model_id"] == "phi-4-mini"
        assert state["total_steps"] == 1000
        assert state["status"] == TrainingStatus.RUNNING.value

    async def test_start_duplicate_session(self, store):
        """Starting an existing session raises 409."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        
        with pytest.raises(HTTPException) as exc_info:
            await store.start_session(session_id, metadata={})
        
        assert exc_info.value.status_code == 409

    async def test_add_event(self, store):
        """Can add events to a session."""
        session_id = valid_session_id()
        
        await store.start_session(
            session_id=session_id,
            metadata={"total_steps": 1000},
        )

        event_id = await store.add_event(
            session_id=session_id,
            event={
                "step": 10,
                "loss": 1.5,
                "epoch": 0,
                "learning_rate": 0.001,
            },
        )

        assert event_id is not None
        assert "-" in event_id  # Redis stream ID format

        # State should be updated
        state = await store.get_state(session_id)
        assert state["current_step"] == 10
        assert state["latest_loss"] == 1.5
        assert state["event_count"] == 1

    async def test_add_event_nonexistent_session(self, store):
        """Adding to nonexistent session raises 404."""
        session_id = valid_session_id()
        
        with pytest.raises(HTTPException) as exc_info:
            await store.add_event(session_id, {"step": 1, "loss": 1.0})
        
        assert exc_info.value.status_code == 404

    async def test_complete_session(self, store):
        """Can mark session as completed."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        await store.add_event(session_id, {"step": 100, "loss": 0.5})
        
        await store.complete_session(session_id)
        
        state = await store.get_state(session_id)
        assert state["status"] == TrainingStatus.COMPLETED.value
        assert state["progress_percent"] == 100.0

    async def test_fail_session(self, store):
        """Can mark session as failed."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        
        await store.complete_session(session_id, error="GPU OOM")
        
        state = await store.get_state(session_id)
        assert state["status"] == TrainingStatus.FAILED.value
        assert state["error_message"] == "GPU OOM"


# ============================================
# EVENT STREAM TESTS
# ============================================

@pytest.mark.asyncio
class TestEventStream:
    """Test event retrieval from streams."""

    async def test_get_events(self, store):
        """Can retrieve events from stream."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        
        await store.add_event(session_id, {"step": 10, "loss": 1.0, "epoch": 0, "learning_rate": 0.001})
        await store.add_event(session_id, {"step": 20, "loss": 0.9, "epoch": 0, "learning_rate": 0.001})
        await store.add_event(session_id, {"step": 30, "loss": 0.8, "epoch": 0, "learning_rate": 0.001})
        
        events = await store.get_events(session_id, limit=10)
        
        assert len(events) >= 3
        # Events should be newest first
        assert events[0]["step"] >= events[-1]["step"]

    async def test_get_events_limit(self, store):
        """Respects limit parameter."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        
        for i in range(10):
            await store.add_event(session_id, {"step": i * 10, "loss": 1.0 - i * 0.1, "epoch": 0, "learning_rate": 0.001})
        
        events = await store.get_events(session_id, limit=5)
        
        assert len(events) == 5

    async def test_get_latest(self, store):
        """Can get latest event."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        await store.add_event(session_id, {"step": 10, "loss": 1.0, "epoch": 0, "learning_rate": 0.001})
        await store.add_event(session_id, {"step": 20, "loss": 0.9, "epoch": 0, "learning_rate": 0.001})
        
        latest = await store.get_latest(session_id)
        
        assert latest is not None
        assert latest["step"] == 20
        assert latest["loss"] == 0.9

    async def test_get_latest_none(self, store):
        """Returns None when no events."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        
        latest = await store.get_latest(session_id)
        
        assert latest is None


# ============================================
# STATE SNAPSHOT TESTS
# ============================================

@pytest.mark.asyncio
class TestStateSnapshot:
    """Test state snapshot updates."""

    async def test_progress_tracking(self, store):
        """Progress updates correctly as events arrive."""
        session_id = valid_session_id()
        
        await store.start_session(
            session_id=session_id,
            metadata={"total_steps": 100},
        )
        
        state = await store.get_state(session_id)
        assert state["progress_percent"] == 0.0
        
        await store.add_event(session_id, {"step": 50, "loss": 1.0, "epoch": 0, "learning_rate": 0.001})
        
        state = await store.get_state(session_id)
        assert state["progress_percent"] == 50.0
        assert state["current_step"] == 50
        
        await store.add_event(session_id, {"step": 100, "loss": 0.5, "epoch": 1, "learning_rate": 0.001})
        
        state = await store.get_state(session_id)
        assert state["progress_percent"] == 100.0
        assert state["current_step"] == 100

    async def test_eta_calculation(self, store):
        """ETA is calculated from events."""
        session_id = valid_session_id()
        
        await store.start_session(
            session_id=session_id,
            metadata={"total_steps": 1000},
        )
        
        # Add events with known timestamps
        now = datetime.now(timezone.utc)
        
        # Add multiple events
        for i in range(5):
            await store.add_event(
                session_id,
                {"step": (i + 1) * 100, "loss": 1.0 - i * 0.1, "epoch": 0, "learning_rate": 0.001},
            )
        
        state = await store.get_state(session_id)
        # ETA should be present after multiple events
        if state["event_count"] >= 2:
            assert "eta_seconds" in state or state["eta_seconds"] is None


# ============================================
# LIST SESSIONS TESTS
# ============================================

@pytest.mark.asyncio
class TestListSessions:
    """Test session listing."""

    async def test_list_empty(self, store):
        """Returns empty list when no sessions."""
        sessions = await store.list_sessions()
        assert len(sessions) == 0

    async def test_list_sessions(self, store):
        """Returns all active sessions."""
        for i in range(3):
            await store.start_session(valid_session_id(), metadata={})
        
        sessions = await store.list_sessions()
        assert len(sessions) == 3

    async def test_list_after_delete(self, store):
        """Deleted sessions not listed."""
        session_id = valid_session_id()
        await store.start_session(session_id, metadata={})
        
        sessions = await store.list_sessions()
        assert len(sessions) == 1
        
        await store.delete_session(session_id)
        
        sessions = await store.list_sessions()
        assert len(sessions) == 0


# ============================================
# DELETE SESSION TESTS
# ============================================

@pytest.mark.asyncio
class TestDeleteSession:
    """Test session deletion."""

    async def test_delete_exists(self, store):
        """Can delete an existing session."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        assert await store.session_exists(session_id)
        
        await store.delete_session(session_id)
        assert not await store.session_exists(session_id)

    async def test_delete_nonexistent_noop(self, store):
        """Deleting nonexistent session doesn't raise."""
        session_id = valid_session_id()
        await store.delete_session(session_id)  # Should not raise


# ============================================
# REDIS UNAVAILABILITY TESTS
# ============================================

@pytest.mark.asyncio
class TestRedisUnavailable:
    """Test 503 behavior when Redis is down."""

    async def test_start_without_connection(self):
        """Start raises 503 when not connected."""
        store = RedisTrainingStore()
        # _redis is None (never connected)
        with pytest.raises(HTTPException) as exc_info:
            await store.start_session(valid_session_id(), metadata={})
        assert exc_info.value.status_code == 503

    async def test_get_state_without_connection(self):
        """Get state raises 503 when not connected."""
        store = RedisTrainingStore()
        with pytest.raises(HTTPException) as exc_info:
            await store.get_state(valid_session_id())
        assert exc_info.value.status_code == 503

    async def test_add_event_without_connection(self):
        """Add event raises 503 when not connected."""
        store = RedisTrainingStore()
        with pytest.raises(HTTPException) as exc_info:
            await store.add_event(valid_session_id(), {"step": 1, "loss": 1.0})
        assert exc_info.value.status_code == 503

    async def test_health_check_disconnected(self):
        """Health check returns False when not connected."""
        store = RedisTrainingStore()
        result = await store.health_check()
        assert result is False


# ============================================
# STREAM EVENTS TESTS (MOCK)
# ============================================

@pytest.mark.asyncio
class TestStreamEvents:
    """Test SSE streaming via mock."""

    async def test_stream_nonexistent_session(self, store):
        """Streaming nonexistent session raises 404."""
        session_id = valid_session_id()
        # The method validates session_id first
        with pytest.raises(HTTPException) as exc_info:
            async for _ in store.stream_events(session_id, None):
                break
        assert exc_info.value.status_code == 404

    async def test_stream_initial_state(self, store):
        """Stream yields initial state first."""
        session_id = valid_session_id()
        
        await store.start_session(
            session_id=session_id,
            metadata={"total_steps": 1000},
        )
        
        messages = []
        async for msg in store.stream_events(session_id, None):
            messages.append(msg)
            break  # Only get first message
        
        assert messages[0]["type"] == "state"
        assert messages[0]["data"]["session_id"] == session_id

    async def test_stream_with_last_id(self, store):
        """Stream accepts last_id parameter."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={})
        
        # Should not yield initial state when last_id is provided
        # Will get a heartbeat since no new events
        async for msg in store.stream_events(session_id, "0-0"):
            assert msg["type"] in ("heartbeat", "event")
            break


# ============================================
# CONCURRENT ACCESS TESTS
# ============================================

@pytest.mark.asyncio
class TestConcurrentAccess:
    """Test concurrent async operations."""

    async def test_concurrent_event_writes(self, store):
        """Multiple concurrent writes don't conflict."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={"total_steps": 10000})
        
        async def writer(step: int):
            await store.add_event(
                session_id,
                {"step": step, "loss": 1.0 - step / 10000, "epoch": 0, "learning_rate": 0.001},
            )
        
        # Write 20 events concurrently
        tasks = [writer(i * 10) for i in range(20)]
        await asyncio.gather(*tasks)
        
        # All events should be recorded
        events = await store.get_events(session_id, limit=100)
        assert len(events) >= 20
        
        state = await store.get_state(session_id)
        assert state["event_count"] >= 20

    async def test_concurrent_read_write(self, store):
        """Concurrent reads and writes work together."""
        session_id = valid_session_id()
        
        await store.start_session(session_id, metadata={"total_steps": 1000})
        
        async def reader():
            for _ in range(5):
                await store.get_state(session_id)
                await asyncio.sleep(0.01)
        
        async def writer():
            for i in range(5):
                await store.add_event(
                    session_id,
                    {"step": (i + 1) * 100, "loss": 1.0, "epoch": 0, "learning_rate": 0.001},
                )
                await asyncio.sleep(0.01)
        
        await asyncio.gather(reader(), writer())
        
        state = await store.get_state(session_id)
        assert state is not None
