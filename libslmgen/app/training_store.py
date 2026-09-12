#!/usr/bin/env python3
"""
Simple In-Memory Training Store.

Wraps the core/training_tracker.py for compatibility with existing API.
Uses simple in-memory storage with background cleanup.

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import logging
import re
from collections.abc import AsyncGenerator
from threading import Thread

from fastapi import HTTPException

from core.training_tracker import (
    TrainingEvent,
    TrainingSession,
    TrainingStatus,
    training_tracker,
)

logger = logging.getLogger(__name__)

# Regex for validating session IDs (UUID v4)
_SESSION_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _validate_session_id(session_id: str) -> None:
    """Validate session_id is a well-formed UUID v4."""
    if not isinstance(session_id, str) or not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")


class SimpleTrainingStore:
    """
    Simple in-memory training store.

    Uses core/training_tracker.py internally.
    """

    def __init__(self):
        self._cleanup_thread: Thread | None = None
        self._running = True

    def start(self) -> None:
        """Start the store."""
        # Core tracker starts its own cleanup
        logger.info("Simple training store started")

    def stop(self) -> None:
        """Stop the store."""
        self._running = False
        logger.info("Simple training store stopped")

    async def start_session(self, session_id: str, metadata: dict) -> None:
        """Start a new training session."""
        _validate_session_id(session_id)

        # Check if already exists
        if training_tracker.has_session(session_id):
            raise HTTPException(
                status_code=409,
                detail="Training session already exists.",
            )

        training_tracker.create_session(
            session_id=session_id,
            job_id=metadata.get("job_id", ""),
            model_id=metadata.get("model_id", ""),
            total_steps=metadata.get("total_steps", 0),
            total_epochs=metadata.get("total_epochs", 1),
        )

        logger.info(f"Started training session: {session_id}")

    async def add_event(self, session_id: str, event: dict) -> str:
        """Add a training event."""
        _validate_session_id(session_id)

        if not training_tracker.has_session(session_id):
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )

        # Get session to access total_steps
        session = training_tracker.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )

        # Create event
        training_event = TrainingEvent(
            step=event.get("step", 0),
            loss=event.get("loss", 0.0),
            epoch=event.get("epoch", 0),
            learning_rate=event.get("learning_rate", 0.0),
            grad_norm=event.get("grad_norm"),
            tokens_per_second=event.get("tokens_per_second"),
            gpu_memory_used=event.get("gpu_memory_used"),
        )

        training_tracker.add_event(session_id, training_event)

        # Return event ID (string)
        return f"{event.get('step', 0)}"

    async def complete_session(self, session_id: str, error: str | None = None) -> None:
        """Mark training as completed or failed."""
        _validate_session_id(session_id)

        if not training_tracker.has_session(session_id):
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )

        if error:
            training_tracker.fail_session(session_id, error)
        else:
            training_tracker.complete_session(session_id)

    async def get_state(self, session_id: str) -> dict | None:
        """Get current state."""
        _validate_session_id(session_id)

        session = training_tracker.get_session(session_id)
        if session is None:
            return None

        return self._session_to_state(session)

    async def get_events(self, session_id: str, limit: int = 100, after_id: str | None = None) -> list[dict]:
        """Get events from session."""
        _validate_session_id(session_id)

        session = training_tracker.get_session(session_id)
        if session is None:
            return []

        events = []
        for event in session.events[-limit:]:
            events.append(event.to_dict())

        return events

    async def get_latest(self, session_id: str) -> dict | None:
        """Get most recent event."""
        _validate_session_id(session_id)

        session = training_tracker.get_session(session_id)
        if session is None or not session.events:
            return None

        return session.events[-1].to_dict()

    async def stream_events(self, session_id: str, last_id: str | None = None) -> AsyncGenerator[dict, None]:
        """Stream events (simple generator)."""
        _validate_session_id(session_id)

        if not training_tracker.has_session(session_id):
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )

        # Get initial state
        session = training_tracker.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Training session not found.",
            )

        # Yield current state
        yield {
            "type": "state",
            "data": self._session_to_state(session),
        }

        # Stream events with simple polling
        import asyncio
        last_step = -1

        while True:
            await asyncio.sleep(2)

            session = training_tracker.get_session(session_id)
            if session is None:
                break

            # Check for new events
            if session.events and session.events[-1].step > last_step:
                for event in session.events:
                    if event.step > last_step:
                        last_step = event.step
                        yield {
                            "type": "event",
                            "id": str(event.step),
                            "event": "progress",
                            "timestamp": event.timestamp.isoformat(),
                            "step": event.step,
                            "loss": event.loss,
                            "epoch": event.epoch,
                            "learning_rate": event.learning_rate,
                        }

            # Check if complete
            if session.status in (TrainingStatus.COMPLETED, TrainingStatus.FAILED):
                yield {
                    "type": "complete",
                    "data": self._session_to_state(session),
                }
                break

    async def list_sessions(self) -> list[dict]:
        """List all active sessions."""
        sessions = training_tracker.list_sessions()
        return [self._session_to_state(s) for s in sessions]

    async def delete_session(self, session_id: str) -> None:
        """Delete a training session."""
        _validate_session_id(session_id)
        training_tracker.delete_session(session_id)
        logger.info(f"Deleted training session: {session_id}")

    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        _validate_session_id(session_id)
        return training_tracker.has_session(session_id)

    def _session_to_state(self, session: TrainingSession) -> dict:
        """Convert session to state dict."""
        total_steps = session.total_steps
        current_step = session.events[-1].step if session.events else 0
        progress = (current_step / total_steps * 100) if total_steps > 0 else 0.0

        # Estimate ETA
        eta_seconds = None
        eta_formatted = None
        if session.events and session.status == TrainingStatus.RUNNING:
            # Simple ETA based on last event
            # This is a simplified ETA
            pass

        return {
            "session_id": session.session_id,
            "job_id": session.job_id,
            "model_id": session.model_id,
            "total_steps": total_steps,
            "total_epochs": session.total_epochs,
            "status": session.status.value,
            "current_step": current_step,
            "current_epoch": session.events[-1].epoch if session.events else 0,
            "progress_percent": min(100.0, progress),
            "latest_loss": session.events[-1].loss if session.events else None,
            "eta_seconds": eta_seconds,
            "eta_formatted": eta_formatted,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "created_at": session.created_at.isoformat(),
            "updated_at": session._last_activity.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "error_message": session.error_message,
            "event_count": len(session.events),
        }


# Global singleton instance
training_store = SimpleTrainingStore()
