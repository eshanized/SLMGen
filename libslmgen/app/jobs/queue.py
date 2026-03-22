#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Queue Configuration.

Redis-based task queue using RQ (Redis Queue).
Provides priority-based job queuing with named queues.

Queue Priority:
- high: Critical operations (uploads, initial processing)
- default: Standard pipeline operations
- low: Background optimization tasks

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import logging
from enum import Enum
from typing import Optional

import redis
from rq import Queue

from app.config import settings

logger = logging.getLogger(__name__)


class QueueName(str, Enum):
    """Available queue names."""
    HIGH = "high"
    DEFAULT = "default"
    LOW = "low"


class JobQueue:
    """
    Redis-based job queue manager.
    
    Manages RQ queues for background job processing.
    Uses the same Redis connection as session storage for simplicity.
    
    Usage:
        queue = JobQueue()
        
        # Enqueue a job
        queue.enqueue("my_task", session_id="abc123")
        
        # Enqueue with priority
        queue.enqueue_to_high("urgent_task", session_id="xyz")
        
        # Get queue instance
        high_queue = queue.get_queue(QueueName.HIGH)
    """
    
    _instance: Optional["JobQueue"] = None
    _redis: Optional[redis.Redis] = None
    _queues: dict[QueueName, Queue] = {}
    
    def __new__(cls) -> "JobQueue":
        """Singleton pattern for queue manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize Redis connection and queues."""
        if self._initialized:
            return
        
        self._initialized = True
        self._connect()
    
    def _connect(self) -> None:
        """Establish Redis connection and create queues."""
        try:
            self._redis = redis.from_url(
                settings.redis_url,
                decode_responses=False,
            )
            self._redis.ping()
            logger.info(f"Connected to Redis at {settings.redis_url}")
            
            for qname in QueueName:
                self._queues[qname] = Queue(
                    qname.value,
                    connection=self._redis,
                    default_timeout=3600,
                )
                logger.info(f"Queue '{qname.value}' initialized")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Job queue unavailable. Jobs will not be processed.")
            self._redis = None
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            return True
        except redis.ConnectionError:
            return False
    
    def get_queue(self, name: QueueName = QueueName.DEFAULT) -> Optional[Queue]:
        """
        Get RQ queue by name.
        
        Args:
            name: Queue name (high, default, low)
            
        Returns:
            RQ Queue instance or None if not connected
        """
        if not self.is_connected:
            return None
        return self._queues.get(name)
    
    def enqueue(
        self,
        func_name: str,
        *args,
        timeout: int = 3600,
        result_ttl: int = 86400,
        **kwargs,
    ) -> Optional["rq.job.Job"]:
        """
        Enqueue a job to the default queue.
        
        Args:
            func_name: Name of the task function
            *args: Positional arguments for the task
            timeout: Job timeout in seconds (default 1 hour)
            result_ttl: Result retention time in seconds (default 24 hours)
            **kwargs: Keyword arguments for the task
            
        Returns:
            RQ Job instance or None if queue unavailable
        """
        return self._enqueue_to(QueueName.DEFAULT, func_name, *args, timeout=timeout, result_ttl=result_ttl, **kwargs)
    
    def enqueue_to_high(
        self,
        func_name: str,
        *args,
        timeout: int = 3600,
        result_ttl: int = 86400,
        **kwargs,
    ) -> Optional["rq.job.Job"]:
        """
        Enqueue a job to the high priority queue.
        
        Args:
            func_name: Name of the task function
            *args: Positional arguments for the task
            timeout: Job timeout in seconds
            **kwargs: Keyword arguments for the task
            
        Returns:
            RQ Job instance or None if queue unavailable
        """
        return self._enqueue_to(QueueName.HIGH, func_name, *args, timeout=timeout, result_ttl=result_ttl, **kwargs)
    
    def enqueue_to_low(
        self,
        func_name: str,
        *args,
        timeout: int = 3600,
        result_ttl: int = 86400,
        **kwargs,
    ) -> Optional["rq.job.Job"]:
        """
        Enqueue a job to the low priority queue.
        
        Args:
            func_name: Name of the task function
            *args: Positional arguments for the task
            timeout: Job timeout in seconds
            **kwargs: Keyword arguments for the task
            
        Returns:
            RQ Job instance or None if queue unavailable
        """
        return self._enqueue_to(QueueName.LOW, func_name, *args, timeout=timeout, result_ttl=result_ttl, **kwargs)
    
    def _enqueue_to(
        self,
        queue_name: QueueName,
        func_name: str,
        *args,
        timeout: int = 3600,
        result_ttl: int = 86400,
        **kwargs,
    ) -> Optional["rq.job.Job"]:
        """
        Internal method to enqueue to a specific queue.
        
        Args:
            queue_name: Target queue name
            func_name: Task function name
            *args: Task arguments
            timeout: Job timeout
            result_ttl: Result TTL
            **kwargs: Task keyword arguments
            
        Returns:
            RQ Job or None
        """
        queue = self.get_queue(queue_name)
        if queue is None:
            logger.error(f"Queue '{queue_name.value}' unavailable, cannot enqueue {func_name}")
            return None
        
        try:
            from app.jobs.tasks import get_task_function
            
            func = get_task_function(func_name)
            if func is None:
                logger.error(f"Task function '{func_name}' not found")
                return None
            
            job = queue.enqueue(
                func,
                *args,
                kwargs=kwargs,
                timeout=timeout,
                result_ttl=result_ttl,
            )
            
            logger.info(f"Enqueued job {job.id} ({func_name}) to '{queue_name.value}' queue")
            return job
            
        except Exception as e:
            logger.error(f"Failed to enqueue {func_name}: {e}")
            return None
    
    def enqueue_chain(
        self,
        steps: list[tuple[str, dict]],
        on_failure: Optional[str] = None,
    ) -> list[Optional["rq.job.Job"]]:
        """
        Enqueue a chain of jobs to execute sequentially.
        
        Args:
            steps: List of (func_name, kwargs) tuples
            on_failure: Callback function on chain failure
            
        Returns:
            List of enqueued jobs (first job triggers the chain)
        """
        if not steps:
            return []
        
        jobs = []
        for func_name, kwargs in steps:
            job = self.enqueue(func_name, **kwargs)
            jobs.append(job)
        
        return jobs
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """
        Get status of a job.
        
        Args:
            job_id: RQ job ID
            
        Returns:
            Dict with job status info or None
        """
        if not self.is_connected:
            return None
        
        try:
            from rq.job import Job
            
            job = Job.fetch(job_id, connection=self._redis)
            
            return {
                "id": job.id,
                "status": job.get_status(),
                "func_name": job.func_name,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.return_value if job.is_finished else None,
                "exc_info": job.exc_info if job.is_failed else None,
                "meta": job.meta,
            }
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.
        
        Args:
            job_id: RQ job ID
            
        Returns:
            True if cancelled, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            from rq.job import Job
            
            job = Job.fetch(job_id, connection=self._redis)
            job.cancel()
            logger.info(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_queue_stats(self) -> dict:
        """
        Get statistics for all queues.
        
        Returns:
            Dict with queue names as keys and job counts as values
        """
        stats = {}
        
        for qname in QueueName:
            queue = self.get_queue(qname)
            if queue:
                stats[qname.value] = {
                    "jobs": len(queue),
                    "failed_jobs": len(queue.failed_job_registry),
                    "finished_jobs": len(queue.finished_job_registry),
                }
            else:
                stats[qname.value] = {"error": "Queue unavailable"}
        
        return stats
    
    def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            self._redis.close()
            self._redis = None
            logger.info("Job queue connection closed")


# Global queue instance
job_queue = JobQueue()


def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    return job_queue
