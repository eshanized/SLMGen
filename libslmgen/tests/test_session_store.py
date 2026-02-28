#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for RedisSessionStore.

Covers:
- CRUD lifecycle (create → get → update → delete)
- TTL / sliding expiration behavior
- Session ID validation (key injection prevention)
- Owner access control
- Download token generation and validation
- Redis unavailability (503 behavior)
- Serialization round-trips (Pydantic models via orjson)
- Concurrent async access
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio

# Try to import fakeredis for in-memory Redis mock
try:
    import fakeredis.aioredis as fakeredis_aio
    HAS_FAKEREDIS = True
except ImportError:
    HAS_FAKEREDIS = False

from app.session_store import (
    RedisSessionStore,
    _validate_session_id,
    _serialize,
    _deserialize,
    _make_key,
)
from fastapi import HTTPException


# ============================================
# FIXTURES
# ============================================

@pytest_asyncio.fixture
async def store():
    """Create a RedisSessionStore backed by fakeredis."""
    if not HAS_FAKEREDIS:
        pytest.skip("fakeredis not installed")

    s = RedisSessionStore(redis_url="redis://fake", ttl_seconds=60)
    # Replace the real Redis client with a fakeredis instance
    s._redis = fakeredis_aio.FakeRedis(decode_responses=False)
    yield s
    await s._redis.aclose()
    s._redis = None


@pytest.fixture
def valid_session_id():
    """Generate a valid UUID v4 session ID."""
    return str(uuid.uuid4())


# ============================================
# SERIALIZATION TESTS
# ============================================

class TestSerialization:
    """Test orjson serialization helpers."""

    def test_round_trip(self):
        """Data survives serialize → deserialize."""
        data = {
            "id": "abc-123",
            "created_at": "2026-01-01T00:00:00+00:00",
            "data": {
                "raw_data": [{"messages": [{"role": "user", "content": "hello"}]}],
                "stats": {"total_examples": 100, "quality_score": 0.95},
            },
        }
        raw = _serialize(data)
        assert isinstance(raw, bytes)
        result = _deserialize(raw)
        assert result == data

    def test_serialize_pydantic_model_dump(self):
        """Pydantic model_dump() dicts serialize correctly."""
        from app.models import DatasetStats

        stats = DatasetStats(
            total_examples=50,
            total_tokens=10000,
            avg_tokens_per_example=200,
            single_turn_pct=80,
            multi_turn_pct=20,
            has_system_prompts=True,
            quality_score=0.85,
            quality_issues=["some issue"],
        )
        dumped = stats.model_dump()
        raw = _serialize({"stats": dumped})
        result = _deserialize(raw)
        assert result["stats"]["total_examples"] == 50
        assert result["stats"]["quality_score"] == 0.85


# ============================================
# SESSION ID VALIDATION TESTS
# ============================================

class TestSessionIdValidation:
    """Test UUID v4 validation for key injection prevention."""

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

    def test_key_injection_with_prefix(self):
        """Key traversal attempt rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_session_id("../session:admin")
        assert exc_info.value.status_code == 400

    def test_empty_string(self):
        """Empty string rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_session_id("")
        assert exc_info.value.status_code == 400

    def test_none_value(self):
        """None rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_session_id(None)
        assert exc_info.value.status_code == 400


# ============================================
# KEY CONSTRUCTION TESTS
# ============================================

class TestKeyConstruction:
    """Test Redis key building."""

    def test_make_key(self):
        sid = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        assert _make_key(sid) == "session:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


# ============================================
# CRUD LIFECYCLE TESTS
# ============================================

@pytest.mark.asyncio
class TestCRUDLifecycle:
    """Test create → get → update → delete flow."""

    async def test_create_and_get(self, store):
        """Create a session and retrieve it."""
        session_id = await store.create_session(
            data={"raw_data": [{"msg": "hello"}]},
            owner_id="user-1",
        )

        assert isinstance(session_id, str)
        # Verify it's a valid UUID
        uuid.UUID(session_id)

        session = await store.get_session(session_id)
        assert session is not None
        assert session["id"] == session_id
        assert session["owner_id"] == "user-1"
        assert session["data"]["raw_data"] == [{"msg": "hello"}]
        assert "created_at" in session
        assert "updated_at" in session

    async def test_get_nonexistent(self, store):
        """Getting a nonexistent session returns None."""
        fake_id = str(uuid.uuid4())
        result = await store.get_session(fake_id)
        assert result is None

    async def test_update_session(self, store):
        """Update merges data into session."""
        session_id = await store.create_session(data={"field_a": "original"})

        await store.update_session(session_id, {"field_b": "added", "field_a": "updated"})

        session = await store.get_session(session_id)
        assert session["data"]["field_a"] == "updated"
        assert session["data"]["field_b"] == "added"

    async def test_update_nonexistent_raises_404(self, store):
        """Updating a nonexistent session raises 404."""
        fake_id = str(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await store.update_session(fake_id, {"key": "value"})
        assert exc_info.value.status_code == 404

    async def test_delete_session(self, store):
        """Delete removes session."""
        session_id = await store.create_session(data={"temp": True})
        session = await store.get_session(session_id)
        assert session is not None

        await store.delete_session(session_id)
        session = await store.get_session(session_id)
        assert session is None

    async def test_delete_nonexistent_is_noop(self, store):
        """Deleting a nonexistent session doesn't raise."""
        fake_id = str(uuid.uuid4())
        await store.delete_session(fake_id)  # Should not raise

    async def test_create_anonymous_session(self, store):
        """Create session without owner_id."""
        session_id = await store.create_session(data={"x": 1})
        session = await store.get_session(session_id)
        assert session["owner_id"] is None

    async def test_create_empty_data(self, store):
        """Create session with no initial data."""
        session_id = await store.create_session()
        session = await store.get_session(session_id)
        assert session["data"] == {}


# ============================================
# OWNER ACCESS CONTROL TESTS
# ============================================

@pytest.mark.asyncio
class TestOwnerAccess:
    """Test get_session_with_owner access control."""

    async def test_anonymous_session_accessible_by_anyone(self, store):
        """Anonymous sessions (no owner) are accessible by any user."""
        session_id = await store.create_session(data={"public": True})
        result = await store.get_session_with_owner(session_id, "any-user")
        assert result is not None

    async def test_anonymous_session_accessible_by_none(self, store):
        """Anonymous sessions accessible when user_id is None."""
        session_id = await store.create_session(data={"public": True})
        result = await store.get_session_with_owner(session_id, None)
        assert result is not None

    async def test_owned_session_accessible_by_owner(self, store):
        """Owned session accessible by the owner."""
        session_id = await store.create_session(data={}, owner_id="owner-1")
        result = await store.get_session_with_owner(session_id, "owner-1")
        assert result is not None

    async def test_owned_session_denied_for_other_user(self, store):
        """Owned session denied for different user."""
        session_id = await store.create_session(data={}, owner_id="owner-1")
        result = await store.get_session_with_owner(session_id, "other-user")
        assert result is None

    async def test_owned_session_denied_for_anonymous(self, store):
        """Owned session denied when user_id is None."""
        session_id = await store.create_session(data={}, owner_id="owner-1")
        result = await store.get_session_with_owner(session_id, None)
        assert result is None


# ============================================
# DOWNLOAD TOKEN TESTS
# ============================================

@pytest.mark.asyncio
class TestDownloadToken:
    """Test download token generation and validation."""

    async def test_generate_and_validate(self, store):
        """Generate token → validate succeeds."""
        session_id = await store.create_session(data={})
        token = await store.generate_download_token(session_id)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

        is_valid = await store.validate_download_token(session_id, token)
        assert is_valid is True

    async def test_wrong_token_rejected(self, store):
        """Wrong token is rejected."""
        session_id = await store.create_session(data={})
        await store.generate_download_token(session_id)
        is_valid = await store.validate_download_token(session_id, "wrong-token")
        assert is_valid is False

    async def test_no_token_generated(self, store):
        """Validation fails when no token was generated."""
        session_id = await store.create_session(data={})
        is_valid = await store.validate_download_token(session_id, "any-token")
        assert is_valid is False

    async def test_nonexistent_session(self, store):
        """Token generation for nonexistent session returns None."""
        fake_id = str(uuid.uuid4())
        token = await store.generate_download_token(fake_id)
        assert token is None

    async def test_token_regeneration(self, store):
        """New token replaces old one."""
        session_id = await store.create_session(data={})
        token1 = await store.generate_download_token(session_id)
        token2 = await store.generate_download_token(session_id)

        assert token1 != token2
        assert await store.validate_download_token(session_id, token1) is False
        assert await store.validate_download_token(session_id, token2) is True


# ============================================
# TTL BEHAVIOR TESTS
# ============================================

@pytest.mark.asyncio
class TestTTLBehavior:
    """Test TTL management and sliding expiration."""

    async def test_session_has_ttl(self, store):
        """Created session has a TTL set in Redis."""
        session_id = await store.create_session(data={})
        key = _make_key(session_id)
        ttl = await store._redis.ttl(key)
        assert ttl > 0
        assert ttl <= 60  # Our fixture uses 60s TTL

    async def test_get_refreshes_ttl(self, store):
        """Getting a session refreshes its TTL."""
        session_id = await store.create_session(data={})
        key = _make_key(session_id)

        # Artificially reduce TTL
        await store._redis.expire(key, 10)
        ttl_before = await store._redis.ttl(key)
        assert ttl_before <= 10

        # Get should refresh
        await store.get_session(session_id)
        ttl_after = await store._redis.ttl(key)
        assert ttl_after > ttl_before

    async def test_update_refreshes_ttl(self, store):
        """Updating a session refreshes its TTL."""
        session_id = await store.create_session(data={})
        key = _make_key(session_id)

        # Artificially reduce TTL
        await store._redis.expire(key, 5)

        # Update should refresh
        await store.update_session(session_id, {"new_field": True})
        ttl_after = await store._redis.ttl(key)
        assert ttl_after > 5


# ============================================
# ACTIVE COUNT TESTS
# ============================================

@pytest.mark.asyncio
class TestActiveCount:
    """Test session counting."""

    async def test_count_empty(self, store):
        """Zero sessions when empty."""
        count = await store.get_active_count()
        assert count == 0

    async def test_count_after_creates(self, store):
        """Count increases with new sessions."""
        await store.create_session(data={})
        await store.create_session(data={})
        await store.create_session(data={})
        count = await store.get_active_count()
        assert count == 3

    async def test_count_after_delete(self, store):
        """Count decreases after deletion."""
        s1 = await store.create_session(data={})
        s2 = await store.create_session(data={})
        await store.delete_session(s1)
        count = await store.get_active_count()
        assert count == 1


# ============================================
# REDIS UNAVAILABILITY TESTS
# ============================================

@pytest.mark.asyncio
class TestRedisUnavailable:
    """Test 503 behavior when Redis is down."""

    async def test_create_without_connection(self):
        """Create raises 503 when not connected."""
        store = RedisSessionStore()
        # _redis is None (never connected)
        with pytest.raises(HTTPException) as exc_info:
            await store.create_session(data={})
        assert exc_info.value.status_code == 503

    async def test_get_without_connection(self):
        """Get raises 503 when not connected."""
        store = RedisSessionStore()
        with pytest.raises(HTTPException) as exc_info:
            await store.get_session(str(uuid.uuid4()))
        assert exc_info.value.status_code == 503

    async def test_health_check_disconnected(self):
        """Health check returns False when not connected."""
        store = RedisSessionStore()
        result = await store.health_check()
        assert result is False


# ============================================
# CONCURRENT ACCESS TESTS
# ============================================

@pytest.mark.asyncio
class TestConcurrentAccess:
    """Test concurrent async operations."""

    async def test_concurrent_creates(self, store):
        """Multiple concurrent creates don't conflict."""
        tasks = [store.create_session(data={"i": i}) for i in range(10)]
        session_ids = await asyncio.gather(*tasks)

        # All should be unique
        assert len(set(session_ids)) == 10

        # All should be retrievable
        for sid in session_ids:
            session = await store.get_session(sid)
            assert session is not None

    async def test_concurrent_updates(self, store):
        """Concurrent updates to the same session (last-write-wins)."""
        session_id = await store.create_session(data={"counter": 0})

        async def updater(value: int):
            await store.update_session(session_id, {"field": value})

        tasks = [updater(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Session should still be valid
        session = await store.get_session(session_id)
        assert session is not None
        assert "field" in session["data"]

    async def test_concurrent_read_write(self, store):
        """Concurrent reads and writes don't crash."""
        session_id = await store.create_session(data={"value": "initial"})

        async def reader():
            for _ in range(5):
                await store.get_session(session_id)

        async def writer():
            for i in range(5):
                await store.update_session(session_id, {"value": f"v{i}"})

        await asyncio.gather(reader(), writer())

        session = await store.get_session(session_id)
        assert session is not None
