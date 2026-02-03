#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Training Progress Tracker.

Manages real-time training progress from Colab notebooks via webhook callbacks.
Stores training events (loss, step, epoch) and provides ETA estimation.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class TrainingStatus(str, Enum):
    """Status of a training session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrainingEvent:
    """A single training event from the notebook."""
    step: int
    loss: float
    epoch: int
    learning_rate: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Optional metrics
    grad_norm: Optional[float] = None
    tokens_per_second: Optional[float] = None
    gpu_memory_used: Optional[float] = None  # In GB
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "step": self.step,
            "loss": self.loss,
            "epoch": self.epoch,
            "learning_rate": self.learning_rate,
            "timestamp": self.timestamp.isoformat(),
            "grad_norm": self.grad_norm,
            "tokens_per_second": self.tokens_per_second,
            "gpu_memory_used": self.gpu_memory_used,
        }


@dataclass
class TrainingSession:
    """A training session with all its events."""
    session_id: str
    job_id: str
    model_id: str
    total_steps: int
    total_epochs: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TrainingStatus = TrainingStatus.PENDING
    events: list[TrainingEvent] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # TTL for session cleanup (2 hours after last activity)
    _last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_event(self, event: TrainingEvent) -> None:
        """Add a training event to the session."""
        self.events.append(event)
        self._last_activity = datetime.now(timezone.utc)
        
        # Update status on first event
        if self.status == TrainingStatus.PENDING:
            self.status = TrainingStatus.RUNNING
            self.started_at = event.timestamp
    
    def complete(self) -> None:
        """Mark training as completed."""
        self.status = TrainingStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self._last_activity = self.completed_at
    
    def fail(self, error: str) -> None:
        """Mark training as failed."""
        self.status = TrainingStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
        self._last_activity = self.completed_at
    
    def is_expired(self, ttl_hours: int = 2) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) > self._last_activity + timedelta(hours=ttl_hours)
    
    @property
    def current_step(self) -> int:
        """Get the current step number."""
        if not self.events:
            return 0
        return self.events[-1].step
    
    @property
    def current_epoch(self) -> int:
        """Get the current epoch number."""
        if not self.events:
            return 0
        return self.events[-1].epoch
    
    @property
    def latest_loss(self) -> Optional[float]:
        """Get the latest loss value."""
        if not self.events:
            return None
        return self.events[-1].loss
    
    @property
    def progress_percent(self) -> float:
        """Get training progress as percentage."""
        if self.total_steps == 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100)
    
    def estimate_eta(self) -> Optional[timedelta]:
        """Estimate time remaining based on current pace."""
        if len(self.events) < 2:
            return None
        
        # Calculate average time per step from recent events
        recent_events = self.events[-min(20, len(self.events)):]
        if len(recent_events) < 2:
            return None
        
        time_diff = (recent_events[-1].timestamp - recent_events[0].timestamp).total_seconds()
        steps_diff = recent_events[-1].step - recent_events[0].step
        
        if steps_diff <= 0:
            return None
        
        seconds_per_step = time_diff / steps_diff
        remaining_steps = self.total_steps - self.current_step
        
        return timedelta(seconds=remaining_steps * seconds_per_step)
    
    def get_loss_history(self) -> list[tuple[int, float]]:
        """Get list of (step, loss) tuples for charting."""
        return [(e.step, e.loss) for e in self.events]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        eta = self.estimate_eta()
        return {
            "session_id": self.session_id,
            "job_id": self.job_id,
            "model_id": self.model_id,
            "status": self.status.value,
            "total_steps": self.total_steps,
            "total_epochs": self.total_epochs,
            "current_step": self.current_step,
            "current_epoch": self.current_epoch,
            "progress_percent": round(self.progress_percent, 2),
            "latest_loss": self.latest_loss,
            "eta_seconds": eta.total_seconds() if eta else None,
            "eta_formatted": self._format_eta(eta) if eta else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "event_count": len(self.events),
        }
    
    @staticmethod
    def _format_eta(eta: timedelta) -> str:
        """Format ETA as human-readable string."""
        total_seconds = int(eta.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class TrainingTracker:
    """
    Singleton manager for all training sessions.
    
    Provides thread-safe access to training sessions and handles cleanup
    of expired sessions.
    """
    
    _instance: Optional["TrainingTracker"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "TrainingTracker":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._sessions = {}
                    cls._instance._session_lock = threading.Lock()
                    logger.info("TrainingTracker singleton initialized")
        return cls._instance
    
    def start_session(
        self,
        session_id: str,
        job_id: str,
        model_id: str,
        total_steps: int,
        total_epochs: int,
    ) -> TrainingSession:
        """Start a new training session."""
        with self._session_lock:
            # Cleanup expired sessions first
            self._cleanup_expired()
            
            session = TrainingSession(
                session_id=session_id,
                job_id=job_id,
                model_id=model_id,
                total_steps=total_steps,
                total_epochs=total_epochs,
            )
            self._sessions[session_id] = session
            logger.info(f"Started training session: {session_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[TrainingSession]:
        """Get a training session by ID."""
        with self._session_lock:
            return self._sessions.get(session_id)
    
    def add_event(
        self,
        session_id: str,
        step: int,
        loss: float,
        epoch: int,
        learning_rate: float,
        grad_norm: Optional[float] = None,
        tokens_per_second: Optional[float] = None,
        gpu_memory_used: Optional[float] = None,
    ) -> bool:
        """
        Add a training event to a session.
        
        Returns True if event was added, False if session not found.
        """
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session is None:
                logger.warning(f"Training session not found: {session_id}")
                return False
            
            event = TrainingEvent(
                step=step,
                loss=loss,
                epoch=epoch,
                learning_rate=learning_rate,
                grad_norm=grad_norm,
                tokens_per_second=tokens_per_second,
                gpu_memory_used=gpu_memory_used,
            )
            session.add_event(event)
            logger.debug(f"Added event to session {session_id}: step={step}, loss={loss:.4f}")
            return True
    
    def complete_session(self, session_id: str) -> bool:
        """Mark a session as completed."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.complete()
            logger.info(f"Training session completed: {session_id}")
            return True
    
    def fail_session(self, session_id: str, error: str) -> bool:
        """Mark a session as failed."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.fail(error)
            logger.warning(f"Training session failed: {session_id} - {error}")
            return True
    
    def get_events(
        self,
        session_id: str,
        since_step: Optional[int] = None,
    ) -> list[dict]:
        """Get events from a session, optionally filtered by step."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session is None:
                return []
            
            events = session.events
            if since_step is not None:
                events = [e for e in events if e.step > since_step]
            
            return [e.to_dict() for e in events]
    
    def get_latest(self, session_id: str) -> Optional[dict]:
        """Get the latest event from a session."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session is None or not session.events:
                return None
            return session.events[-1].to_dict()
    
    def get_status(self, session_id: str) -> Optional[dict]:
        """Get the current status of a training session."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return session.to_dict()
    
    def list_sessions(self) -> list[dict]:
        """List all active training sessions."""
        with self._session_lock:
            self._cleanup_expired()
            return [s.to_dict() for s in self._sessions.values()]
    
    def _cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired_ids:
            del self._sessions[sid]
            logger.info(f"Cleaned up expired training session: {sid}")
        return len(expired_ids)
    
    @property
    def active_count(self) -> int:
        """Number of active training sessions."""
        with self._session_lock:
            self._cleanup_expired()
            return len(self._sessions)


# Global tracker instance
training_tracker = TrainingTracker()
