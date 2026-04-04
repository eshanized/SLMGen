#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background Job System (Simplified).

For MVP, we run tasks synchronously instead of using background jobs.
This module provides stubs for compatibility.

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

# Stub implementations - tasks run synchronously in the API routes


class StubJobQueue:
    """Stub job queue that does nothing (sync execution)."""
    
    @property
    def is_connected(self) -> bool:
        return False
    
    def enqueue(self, task_name: str, **kwargs):
        """Enqueue task (returns None for sync mode)."""
        return None


# Global stub instance
job_queue = StubJobQueue()


def get_job_queue() -> StubJobQueue:
    """Get job queue instance."""
    return job_queue


# Task functions are imported from routers directly for sync execution
def ingest_task(session_id: str):
    """Stub for ingest task."""
    pass


def analyze_task(session_id: str):
    """Stub for analyze task."""
    pass


def recommend_task(session_id: str):
    """Stub for recommend task."""
    pass


def generate_notebook_task(session_id: str, model_id: str = None):
    """Stub for generate task."""
    pass