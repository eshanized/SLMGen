#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Management.

Handles in-memory session storage with auto-expiry and cleanup.
We keep things simple here - no database, just a dict with some housekeeping.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import uuid
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from .config import settings
from .models import DatasetStats, DatasetCharacteristics, TaskType, DeploymentTarget

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Represents a single user Session with their data."""
    id: str
    created_at: datetime
    expires_at: datetime
    
    # File info
    file_path: str = ""
    original_filename: str = ""
    
    # Processed data - we clear raw_data after Processing to save memory
    raw_data: list[dict] = field(default_factory=list)
    stats: Optional[DatasetStats] = None
    characteristics: Optional[DatasetCharacteristics] = None
    
    # User selections
    task_type: Optional[TaskType] = None
    deployment_target: Optional[DeploymentTarget] = None
    selected_model_id: Optional[str] = None
    
    # Generated notebook Path
    notebook_path: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if session has Expired."""
        return datetime.utcnow() > self.expires_at
    
    def refresh(self) -> None:
        """Extend session expiry Time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=settings.session_ttl_minutes)


class SessionManager:
    """
    Manages all active Sessions.
    
    We keep a max of 25 sessions and cleanup expired ones on each Request.
    This is fine for a demo app - production would use Redis or something.
    """
    
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = __import__('threading').Lock()  # Thread safety for concurrent requests
        logger.info("SessionManager initialized")
    
    def _cleanup_expired(self) -> int:
        """Remove expired sessions, returns count Removed."""
        now = datetime.utcnow()
        expired_ids = [
            sid for sid, sess in self._sessions.items()
            if sess.is_expired()
        ]
        
        for sid in expired_ids:
            sess = self._sessions.pop(sid)
            # Clean up the uploaded File too
            if sess.file_path and Path(sess.file_path).exists():
                try:
                    Path(sess.file_path).unlink()
                    logger.debug(f"Cleaned up file: {sess.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup file {sess.file_path}: {e}")
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
        
        return len(expired_ids)
    
    def _enforce_limit(self) -> None:
        """Remove oldest sessions if we're over the Limit."""
        while len(self._sessions) >= settings.max_sessions:
            # Find the oldest Session
            oldest_id = min(
                self._sessions.keys(),
                key=lambda sid: self._sessions[sid].created_at
            )
            old_sess = self._sessions.pop(oldest_id)
            logger.info(f"Evicted old session {oldest_id} to make room")
            
            # Cleanup its File
            if old_sess.file_path and Path(old_sess.file_path).exists():
                try:
                    Path(old_sess.file_path).unlink()
                except Exception:
                    pass  # best effort
    
    def create(self) -> Session:
        """Create a new Session."""
        with self._lock:
            # Housekeeping first
            self._cleanup_expired()
            self._enforce_limit()
            
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            expires = now + timedelta(minutes=settings.session_ttl_minutes)
            
            session = Session(
                id=session_id,
                created_at=now,
                expires_at=expires,
            )
            
            self._sessions[session_id] = session
            logger.info(f"Created new session: {session_id}")
            
            return session
    
    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID, returns None if not Found or expired."""
        with self._lock:
            self._cleanup_expired()
            
            session = self._sessions.get(session_id)
            if session is None:
                return None
            
            if session.is_expired():
                # shouldn't happen after cleanup but just in Case
                self._sessions.pop(session_id, None)
                return None
            
            # Refresh expiry on Access
            session.refresh()
            return session
    
    def update(self, session: Session) -> None:
        """Update session in Store."""
        with self._lock:
            if session.id in self._sessions:
                self._sessions[session.id] = session
    
    def delete(self, session_id: str) -> bool:
        """Delete a session and its Files."""
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if session is None:
                return False
            
            # Cleanup files
            for path in [session.file_path, session.notebook_path]:
                if path and Path(path).exists():
                    try:
                        Path(path).unlink()
                    except Exception:
                        pass
            
            logger.info(f"Deleted session: {session_id}")
            return True
    
    @property
    def active_count(self) -> int:
        """Number of active Sessions."""
        self._cleanup_expired()
        return len(self._sessions)


# Global session manager Instance
session_manager = SessionManager()
