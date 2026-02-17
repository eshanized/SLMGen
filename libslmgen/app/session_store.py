#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis-Backed Session Store.

Production-grade session storage using Redis with async support.

Architecture & Tradeoffs:
    - Uses redis.asyncio for non-blocking I/O compatible with FastAPI's async model
    - Sessions stored as JSON-serialized strings under keys `session:{uuid}`
    - orjson used for ~2-6x faster serialization vs stdlib json
    - Sliding TTL: every read/write refreshes the expiration window
    - Redis handles expiry natively (no background cleanup threads needed)
    - Session IDs validated as UUID v4 to prevent key injection attacks
    - All Redis errors wrapped in HTTP 503 to avoid leaking internal state
    - Singleton connection pattern: one connection pool shared across all requests

Why not Redis Hashes?
    We store the full session as a single JSON blob rather than using Redis hashes
    because (a) we almost always read/write the full session, and (b) orjson
    serialization of the full object is faster than multiple HGET/HSET calls.
    For write-heavy partial updates, hashes would be better — but our access
    pattern is read-heavy with occasional full-object writes.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import uuid
import logging
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Optional

import orjson
import redis.asyncio as aioredis
from fastapi import HTTPException

from .config import settings

logger = logging.getLogger(__name__)

# Regex for validating UUID v4 session IDs — prevents key injection
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Redis key prefix
_KEY_PREFIX = "session:"


def _validate_session_id(session_id: str) -> None:
    """
    Validate that session_id is a well-formed UUID v4.

    Prevents Redis key injection by rejecting any string that doesn't
    match the UUID v4 pattern. This is critical because we interpolate
    session_id directly into Redis key names.

    Raises:
        HTTPException(400): If session_id is not a valid UUID v4.
    """
    if not isinstance(session_id, str) or not _UUID_RE.match(session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID format.",
        )


def _redis_error_handler(func):
    """
    Decorator that catches Redis connection/operational errors and converts
    them to HTTP 503 responses. Prevents leaking internal Redis errors to clients.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise our own HTTP exceptions (400, 404, etc.)
            raise
        except aioredis.ConnectionError as e:
            logger.error(f"Redis connection error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=503,
                detail="Session service temporarily unavailable. Please try again later.",
            )
        except aioredis.RedisError as e:
            logger.error(f"Redis error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=503,
                detail="Session service temporarily unavailable. Please try again later.",
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail="Session service temporarily unavailable. Please try again later.",
            )
    return wrapper


def _serialize(data: dict) -> bytes:
    """Serialize session data to bytes using orjson."""
    return orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS)


def _deserialize(raw: bytes) -> dict:
    """Deserialize session data from bytes using orjson."""
    return orjson.loads(raw)


def _make_key(session_id: str) -> str:
    """Build the Redis key for a session."""
    return f"{_KEY_PREFIX}{session_id}"


def _now_iso() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class RedisSessionStore:
    """
    Async Redis-backed session store for SLMGEN.

    Provides CRUD operations for user sessions with:
    - Automatic TTL management (sliding expiration)
    - UUID v4 session ID validation (key injection prevention)
    - orjson serialization for performance
    - Graceful degradation when Redis is unavailable (HTTP 503)
    - Singleton connection pool pattern

    Usage:
        store = RedisSessionStore(redis_url="redis://localhost:6379/0")
        await store.connect()

        session_id = await store.create_session({"raw_data": [...]})
        session = await store.get_session(session_id)
        await store.update_session(session_id, {"stats": {...}})
        await store.delete_session(session_id)

        await store.close()
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 1800,
    ):
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """
        Initialize the Redis connection pool.

        Should be called once during application startup (FastAPI lifespan).
        Creates a connection pool that is reused across all requests.
        """
        if self._redis is not None:
            return

        self._redis = aioredis.from_url(
            self._redis_url,
            decode_responses=False,  # We handle decoding via orjson
            max_connections=20,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

        # Verify connectivity
        try:
            await self._redis.ping()
            logger.info(f"✅ Redis connected: {self._redis_url}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._redis = None
            raise

    async def close(self) -> None:
        """
        Close the Redis connection pool.

        Should be called during application shutdown (FastAPI lifespan).
        """
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            logger.info("Redis connection closed")

    async def health_check(self) -> bool:
        """
        Check if Redis is reachable.

        Returns:
            True if Redis responds to PING, False otherwise.
        """
        if self._redis is None:
            return False
        try:
            return await self._redis.ping()
        except Exception:
            return False

    def _require_connection(self) -> aioredis.Redis:
        """Get the Redis client, raising 503 if not connected."""
        if self._redis is None:
            raise HTTPException(
                status_code=503,
                detail="Session service not initialized. Please try again later.",
            )
        return self._redis

    @_redis_error_handler
    async def create_session(
        self,
        data: Optional[dict] = None,
        owner_id: Optional[str] = None,
    ) -> str:
        """
        Create a new session and store it in Redis.

        Args:
            data: Initial session data (file_path, raw_data, stats, etc.)
            owner_id: Optional user ID for ownership tracking.

        Returns:
            The generated session ID (UUID v4 string).
        """
        r = self._require_connection()

        session_id = str(uuid.uuid4())
        now = _now_iso()

        session = {
            "id": session_id,
            "created_at": now,
            "updated_at": now,
            "owner_id": owner_id,
            "data": data or {},
        }

        key = _make_key(session_id)
        await r.set(key, _serialize(session), ex=self._ttl_seconds)

        logger.info(
            f"Created session: {session_id} "
            f"(owner: {owner_id or 'anonymous'}, ttl: {self._ttl_seconds}s)"
        )
        return session_id

    @_redis_error_handler
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve a session by ID. Refreshes TTL on access (sliding window).

        Args:
            session_id: The session UUID.

        Returns:
            The session dict if found, None if expired or nonexistent.
        """
        _validate_session_id(session_id)
        r = self._require_connection()

        key = _make_key(session_id)
        raw = await r.get(key)

        if raw is None:
            return None

        # Refresh TTL (sliding expiration)
        await r.expire(key, self._ttl_seconds)

        return _deserialize(raw)

    async def get_session_with_owner(
        self,
        session_id: str,
        user_id: Optional[str],
    ) -> Optional[dict]:
        """
        Get session only if the user has access.

        Access is granted if:
        - Session has no owner (anonymous session)
        - Session owner matches user_id
        - user_id is None and session is anonymous

        Args:
            session_id: The session UUID.
            user_id: The requesting user's ID (None for anonymous).

        Returns:
            The session dict if accessible, None otherwise.
        """
        session = await self.get_session(session_id)
        if session is None:
            return None

        session_owner = session.get("owner_id")

        # Anonymous sessions can be accessed by anyone
        if session_owner is None:
            return session

        # Owned sessions require matching user
        if session_owner == user_id:
            return session

        logger.warning(f"Session {session_id} access denied for user {user_id}")
        return None

    @_redis_error_handler
    async def update_session(self, session_id: str, updates: dict) -> None:
        """
        Merge updates into an existing session. Refreshes TTL.

        The `updates` dict is merged into `session["data"]`. To update
        top-level session fields (owner_id, etc.), pass them explicitly.

        Args:
            session_id: The session UUID.
            updates: Dict of fields to merge into session["data"].

        Raises:
            HTTPException(404): If the session does not exist.
        """
        _validate_session_id(session_id)
        r = self._require_connection()

        key = _make_key(session_id)
        raw = await r.get(key)

        if raw is None:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired.",
            )

        session = _deserialize(raw)
        session["updated_at"] = _now_iso()

        # Merge updates into the data sub-object
        if "data" not in session:
            session["data"] = {}
        session["data"].update(updates)

        await r.set(key, _serialize(session), ex=self._ttl_seconds)

    @_redis_error_handler
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session from Redis.

        This is idempotent — deleting a nonexistent session is a no-op.

        Args:
            session_id: The session UUID.
        """
        _validate_session_id(session_id)
        r = self._require_connection()

        key = _make_key(session_id)
        deleted = await r.delete(key)

        if deleted:
            logger.info(f"Deleted session: {session_id}")

    @_redis_error_handler
    async def generate_download_token(self, session_id: str) -> Optional[str]:
        """
        Generate a secure, time-limited download token for a session.

        The token is stored within the session data and validated via
        `validate_download_token`. Token TTL is controlled by the
        `download_token_ttl_minutes` setting.

        Args:
            session_id: The session UUID.

        Returns:
            The generated token string, or None if session not found.
        """
        _validate_session_id(session_id)
        r = self._require_connection()

        key = _make_key(session_id)
        raw = await r.get(key)

        if raw is None:
            return None

        session = _deserialize(raw)
        token = secrets.token_urlsafe(32)
        token_expires = (
            datetime.now(timezone.utc)
            + timedelta(minutes=settings.download_token_ttl_minutes)
        ).isoformat()

        if "data" not in session:
            session["data"] = {}
        session["data"]["download_token"] = token
        session["data"]["download_token_expires"] = token_expires
        session["updated_at"] = _now_iso()

        await r.set(key, _serialize(session), ex=self._ttl_seconds)

        logger.info(f"Generated download token for session {session_id}")
        return token

    @_redis_error_handler
    async def validate_download_token(
        self, session_id: str, token: str
    ) -> bool:
        """
        Validate a download token for a session.

        Args:
            session_id: The session UUID.
            token: The token string to validate.

        Returns:
            True if the token is valid and not expired.
        """
        _validate_session_id(session_id)
        r = self._require_connection()

        key = _make_key(session_id)
        raw = await r.get(key)

        if raw is None:
            return False

        session = _deserialize(raw)
        data = session.get("data", {})

        stored_token = data.get("download_token")
        if stored_token != token:
            return False

        expires_str = data.get("download_token_expires")
        if not expires_str:
            return False

        try:
            expires_at = datetime.fromisoformat(expires_str)
            if datetime.now(timezone.utc) > expires_at:
                return False
        except (ValueError, TypeError):
            return False

        return True

    @_redis_error_handler
    async def get_active_count(self) -> int:
        """
        Count active sessions using SCAN (non-blocking).

        Uses SCAN instead of KEYS to avoid blocking Redis on large keyspaces.

        Returns:
            Number of active session keys.
        """
        r = self._require_connection()

        count = 0
        async for _ in r.scan_iter(match=f"{_KEY_PREFIX}*", count=100):
            count += 1
        return count


# ---------------------------------------------------------------------------
# Global singleton instance
# ---------------------------------------------------------------------------
session_store = RedisSessionStore(
    redis_url=settings.redis_url,
    ttl_seconds=settings.session_ttl_seconds,
)
