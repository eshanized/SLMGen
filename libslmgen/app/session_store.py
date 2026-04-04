#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple In-Memory Session Store.

Production-grade session storage using simple in-memory dict with threading.Lock.
Sessions expire after TTL (default 30 minutes) via background cleanup.

This is the simplest possible implementation suitable for single-instance deployments.
For horizontal scaling, migrate to Redis-backed storage.

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import re
import uuid
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from threading import Thread, Lock
from typing import Any, Optional

from fastapi import HTTPException

from .config import settings

logger = logging.getLogger(__name__)

# Regex for validating UUID v4 session IDs
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Session TTL in seconds
SESSION_TTL_SECONDS = settings.session_ttl_seconds  # 1800 seconds = 30 minutes


def _validate_session_id(session_id: str) -> None:
    """Validate that session_id is a well-formed UUID v4."""
    if not isinstance(session_id, str) or not _UUID_RE.match(session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID format.",
        )


class InMemorySessionStore:
    """
    Simple in-memory session store.
    
    Uses threading.Lock for thread-safe access and background thread
    for cleaning up expired sessions.
    
    Usage:
        store = InMemorySessionStore()
        
        session_id = await store.create_session({"raw_data": [...]})
        session = await store.get_session(session_id)
        await store.update_session(session_id, {"stats": {...}})
        await store.delete_session(session_id)
    """

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS):
        self._sessions: dict[str, dict] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_seconds
        self._cleanup_thread: Optional[Thread] = None
        self._running = True

    def start(self) -> None:
        """Start the cleanup background thread."""
        self._cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info(f"In-memory session store started (TTL: {self._ttl_seconds}s)")

    def stop(self) -> None:
        """Stop the cleanup background thread."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        logger.info("In-memory session store stopped")

    def _cleanup_loop(self) -> None:
        """Background thread to clean up expired sessions."""
        while self._running:
            time.sleep(60)  # Check every minute
            self._cleanup_expired()

    def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        now = time.time()
        expired = []
        
        with self._lock:
            for session_id, session in self._sessions.items():
                expires_at = session.get("_expires_at", 0)
                if now > expires_at:
                    expired.append(session_id)
        
        for session_id in expired:
            with self._lock:
                self._sessions.pop(session_id, None)
            logger.debug(f"Expired session: {session_id}")

    def _get_or_raise(self, session_id: str) -> dict:
        """Get session or raise 404."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found or expired.",
                )
            # Check expiration
            if time.time() > session.get("_expires_at", 0):
                self._sessions.pop(session_id, None)
                raise HTTPException(
                    status_code=404,
                    detail="Session not found or expired.",
                )
            return session

    async def create_session(
        self,
        data: Optional[dict] = None,
        owner_id: Optional[str] = None,
    ) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        session = {
            "id": session_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "owner_id": owner_id,
            "data": data or {},
            "_expires_at": time.time() + self._ttl_seconds,
        }
        
        with self._lock:
            self._sessions[session_id] = session
        
        logger.info(
            f"Created session: {session_id} "
            f"(owner: {owner_id or 'anonymous'}, ttl: {self._ttl_seconds}s)"
        )
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get a session by ID."""
        _validate_session_id(session_id)
        
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            # Check expiration
            if time.time() > session.get("_expires_at", 0):
                self._sessions.pop(session_id, None)
                return None
            # Refresh TTL (sliding expiration)
            session["_expires_at"] = time.time() + self._ttl_seconds
            return session.copy()

    async def get_session_with_owner(
        self,
        session_id: str,
        user_id: Optional[str],
    ) -> Optional[dict]:
        """Get session only if user has access."""
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

    async def update_session(self, session_id: str, updates: dict) -> None:
        """Update a session."""
        _validate_session_id(session_id)
        
        session = self._get_or_raise(session_id)
        
        now = datetime.now(timezone.utc)
        session["updated_at"] = now.isoformat()
        
        # Merge updates into the data sub-object
        if "data" not in session:
            session["data"] = {}
        session["data"].update(updates)
        
        # Refresh TTL
        session["_expires_at"] = time.time() + self._ttl_seconds

    async def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        _validate_session_id(session_id)
        
        with self._lock:
            self._sessions.pop(session_id, None)
        
        logger.info(f"Deleted session: {session_id}")

    async def generate_download_token(self, session_id: str) -> Optional[str]:
        """Generate a secure download token."""
        _validate_session_id(session_id)
        
        session = await self.get_session(session_id)
        if session is None:
            return None
        
        token = secrets.token_urlsafe(32)
        token_expires = (
            datetime.now(timezone.utc) + timedelta(minutes=settings.download_token_ttl_minutes)
        ).isoformat()
        
        if "data" not in session:
            session["data"] = {}
        session["data"]["download_token"] = token
        session["data"]["download_token_expires"] = token_expires
        
        logger.info(f"Generated download token for session {session_id}")
        return token

    async def validate_download_token(self, session_id: str, token: str) -> bool:
        """Validate a download token."""
        _validate_session_id(session_id)
        
        session = await self.get_session(session_id)
        if session is None:
            return False
        
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

    async def get_active_count(self) -> int:
        """Count active sessions."""
        with self._lock:
            return len(self._sessions)


# Global singleton instance
session_store = InMemorySessionStore()