#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background Job System.

Provides async job processing using RQ (Redis Queue).

Modules:
    queue: Job queue configuration and management
    tasks: Background job task functions
    worker: RQ worker entry point

Usage:
    # Start worker
    python -m app.jobs.worker
    
    # Or programmatically
    from app.jobs.queue import job_queue
    job_queue.enqueue("ingest_task", session_id="...")
"""

from app.jobs.queue import (
    job_queue,
    JobQueue,
    QueueName,
    get_job_queue,
)
from app.jobs.tasks import (
    ingest_task,
    analyze_task,
    recommend_task,
    generate_notebook_task,
    get_task_function,
)

__all__ = [
    "job_queue",
    "JobQueue",
    "QueueName",
    "get_job_queue",
    "ingest_task",
    "analyze_task",
    "recommend_task",
    "generate_notebook_task",
    "get_task_function",
]
