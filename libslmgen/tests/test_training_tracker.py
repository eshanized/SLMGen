#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for training tracker module.

Covers:
- Session creation and lifecycle
- Event addition and retrieval
- ETA estimation
- Session expiry
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Import with path adjustment for test environment
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.training_tracker import (
    TrainingTracker,
    TrainingSession,
    TrainingEvent,
    TrainingStatus,
)


class TestTrainingEvent:
    """Test TrainingEvent dataclass."""
    
    def test_event_creation(self):
        """Create an event with all fields."""
        event = TrainingEvent(
            step=100,
            loss=0.5,
            epoch=1,
            learning_rate=2e-4,
            grad_norm=1.2,
            tokens_per_second=450.0,
            gpu_memory_used=12.5,
        )
        assert event.step == 100
        assert event.loss == 0.5
        assert event.epoch == 1
        assert event.learning_rate == 2e-4
        assert event.grad_norm == 1.2
    
    def test_event_to_dict(self):
        """Convert event to dictionary."""
        event = TrainingEvent(step=50, loss=0.8, epoch=0, learning_rate=1e-4)
        d = event.to_dict()
        assert d["step"] == 50
        assert d["loss"] == 0.8
        assert "timestamp" in d


class TestTrainingSession:
    """Test TrainingSession class."""
    
    def test_session_creation(self):
        """Create a new training session."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=1000,
            total_epochs=3,
        )
        assert session.session_id == "test-123"
        assert session.status == TrainingStatus.PENDING
        assert session.current_step == 0
        assert session.progress_percent == 0.0
    
    def test_add_event_updates_status(self):
        """Adding first event changes status to RUNNING."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=1000,
            total_epochs=3,
        )
        
        event = TrainingEvent(step=10, loss=1.5, epoch=0, learning_rate=2e-4)
        session.add_event(event)
        
        assert session.status == TrainingStatus.RUNNING
        assert session.current_step == 10
        assert session.latest_loss == 1.5
    
    def test_progress_percent(self):
        """Calculate progress percentage correctly."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        event = TrainingEvent(step=25, loss=0.5, epoch=0, learning_rate=2e-4)
        session.add_event(event)
        
        assert session.progress_percent == 25.0
    
    def test_complete_session(self):
        """Mark session as completed."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        session.complete()
        assert session.status == TrainingStatus.COMPLETED
        assert session.completed_at is not None
    
    def test_fail_session(self):
        """Mark session as failed with error."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        session.fail("CUDA out of memory")
        assert session.status == TrainingStatus.FAILED
        assert session.error_message == "CUDA out of memory"
    
    def test_loss_history(self):
        """Get loss history for charting."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        for i in range(5):
            event = TrainingEvent(
                step=(i + 1) * 10,
                loss=1.0 - (i * 0.1),
                epoch=0,
                learning_rate=2e-4,
            )
            session.add_event(event)
        
        history = session.get_loss_history()
        assert len(history) == 5
        assert history[0] == (10, 1.0)
        assert history[4] == (50, 0.6)
    
    def test_to_dict(self):
        """Convert session to dictionary."""
        session = TrainingSession(
            session_id="test-123",
            job_id="job-456",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        d = session.to_dict()
        assert d["session_id"] == "test-123"
        assert d["status"] == "pending"
        assert d["total_steps"] == 100


class TestTrainingTracker:
    """Test TrainingTracker singleton."""
    
    def test_singleton_pattern(self):
        """TrainingTracker should be a singleton."""
        tracker1 = TrainingTracker()
        tracker2 = TrainingTracker()
        assert tracker1 is tracker2
    
    def test_start_session(self):
        """Start a new training session."""
        tracker = TrainingTracker()
        
        session = tracker.start_session(
            session_id="tracker-test-1",
            job_id="job-1",
            model_id="phi-4-mini",
            total_steps=500,
            total_epochs=2,
        )
        
        assert session.session_id == "tracker-test-1"
        assert tracker.get_session("tracker-test-1") is not None
        
        # Cleanup
        tracker._sessions.pop("tracker-test-1", None)
    
    def test_add_event(self):
        """Add event to an existing session."""
        tracker = TrainingTracker()
        
        tracker.start_session(
            session_id="tracker-test-2",
            job_id="job-2",
            model_id="phi-4-mini",
            total_steps=500,
            total_epochs=2,
        )
        
        success = tracker.add_event(
            session_id="tracker-test-2",
            step=10,
            loss=1.2,
            epoch=0,
            learning_rate=2e-4,
        )
        
        assert success is True
        
        events = tracker.get_events("tracker-test-2")
        assert len(events) == 1
        assert events[0]["step"] == 10
        
        # Cleanup
        tracker._sessions.pop("tracker-test-2", None)
    
    def test_add_event_nonexistent_session(self):
        """Adding event to nonexistent session returns False."""
        tracker = TrainingTracker()
        
        success = tracker.add_event(
            session_id="nonexistent-session",
            step=10,
            loss=1.2,
            epoch=0,
            learning_rate=2e-4,
        )
        
        assert success is False
    
    def test_get_latest(self):
        """Get latest event from session."""
        tracker = TrainingTracker()
        
        tracker.start_session(
            session_id="tracker-test-3",
            job_id="job-3",
            model_id="phi-4-mini",
            total_steps=500,
            total_epochs=2,
        )
        
        for i in range(3):
            tracker.add_event(
                session_id="tracker-test-3",
                step=(i + 1) * 10,
                loss=1.0 - (i * 0.1),
                epoch=0,
                learning_rate=2e-4,
            )
        
        latest = tracker.get_latest("tracker-test-3")
        assert latest["step"] == 30
        assert latest["loss"] == 0.8
        
        # Cleanup
        tracker._sessions.pop("tracker-test-3", None)
    
    def test_complete_session(self):
        """Complete a training session."""
        tracker = TrainingTracker()
        
        tracker.start_session(
            session_id="tracker-test-4",
            job_id="job-4",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        success = tracker.complete_session("tracker-test-4")
        assert success is True
        
        status = tracker.get_status("tracker-test-4")
        assert status["status"] == "completed"
        
        # Cleanup
        tracker._sessions.pop("tracker-test-4", None)
    
    def test_fail_session(self):
        """Fail a training session with error."""
        tracker = TrainingTracker()
        
        tracker.start_session(
            session_id="tracker-test-5",
            job_id="job-5",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        
        success = tracker.fail_session("tracker-test-5", "OOM error")
        assert success is True
        
        status = tracker.get_status("tracker-test-5")
        assert status["status"] == "failed"
        assert status["error_message"] == "OOM error"
        
        # Cleanup
        tracker._sessions.pop("tracker-test-5", None)
    
    def test_get_events_since_step(self):
        """Filter events by step number."""
        tracker = TrainingTracker()
        
        tracker.start_session(
            session_id="tracker-test-6",
            job_id="job-6",
            model_id="phi-4-mini",
            total_steps=500,
            total_epochs=2,
        )
        
        for i in range(5):
            tracker.add_event(
                session_id="tracker-test-6",
                step=(i + 1) * 10,
                loss=1.0,
                epoch=0,
                learning_rate=2e-4,
            )
        
        events = tracker.get_events("tracker-test-6", since_step=20)
        assert len(events) == 3  # Steps 30, 40, 50
        
        # Cleanup
        tracker._sessions.pop("tracker-test-6", None)
    
    def test_list_sessions(self):
        """List all active sessions."""
        tracker = TrainingTracker()
        
        # Clear any existing test sessions
        for key in list(tracker._sessions.keys()):
            if key.startswith("list-test"):
                del tracker._sessions[key]
        
        tracker.start_session(
            session_id="list-test-1",
            job_id="job-1",
            model_id="phi-4-mini",
            total_steps=100,
            total_epochs=1,
        )
        tracker.start_session(
            session_id="list-test-2",
            job_id="job-2",
            model_id="llama-3.2-3B",
            total_steps=200,
            total_epochs=2,
        )
        
        sessions = tracker.list_sessions()
        list_test_sessions = [s for s in sessions if s["session_id"].startswith("list-test")]
        assert len(list_test_sessions) >= 2
        
        # Cleanup
        tracker._sessions.pop("list-test-1", None)
        tracker._sessions.pop("list-test-2", None)
