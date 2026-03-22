#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RQ Worker Entry Point.

Starts RQ workers to process background jobs from Redis queues.

Usage:
    python -m app.jobs.worker                    # Default (1 worker, default queue)
    python -m app.jobs.worker --high            # High priority queue
    python -m app.jobs.worker --workers 4       # 4 workers
    python -m app.jobs.worker --burst            # Process all queued jobs and exit

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import argparse
import logging
import os
import sys
import signal
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from redis import Redis
from rq import Worker
from rq.logutils import setup_loghandlers

from app.config import settings
from app.jobs.queue import QueueName

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rq.worker")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SLMGEN Background Job Worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--queue", "-q",
        choices=[q.value for q in QueueName],
        default=QueueName.DEFAULT.value,
        help="Queue to process (default: default)",
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="Number of worker threads (default: 1)",
    )
    
    parser.add_argument(
        "--burst", "-b",
        action="store_true",
        help="Run in burst mode (process all jobs and exit)",
    )
    
    parser.add_argument(
        "--url",
        default=None,
        help="Redis URL (default: from settings.redis_url)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    return parser.parse_args()


def get_redis_connection(url: str = None) -> Redis:
    """Create Redis connection for worker."""
    redis_url = url or settings.redis_url
    return Redis.from_url(redis_url, decode_responses=False)


def setup_signal_handlers(workers: list):
    """Setup graceful shutdown handlers."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        for w in workers:
            logger.info(f"Shutting down worker {w.name}...")
            w.request_stop()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def main():
    """Main entry point for RQ worker."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info("SLMGEN Background Job Worker")
    logger.info("=" * 60)
    logger.info(f"Queue: {args.queue}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Burst mode: {args.burst}")
    logger.info(f"Redis URL: {args.url or settings.redis_url}")
    logger.info("=" * 60)
    
    # Create Redis connection
    try:
        conn = get_redis_connection(args.url)
        conn.ping()
        logger.info(f"Connected to Redis at {args.url or settings.redis_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    
    # Create workers
    queues = [args.queue]
    
    # For multiple workers, we create separate worker instances
    # Note: In production, you'd typically run multiple processes
    worker_instances = []
    
    for i in range(args.workers):
        worker_name = f"slmgen:{args.queue}:worker-{i+1}"
        worker = Worker(
            queues,
            connection=conn,
            name=worker_name,
            log_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        worker_instances.append(worker)
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers(worker_instances)
    
    logger.info(f"Starting {len(worker_instances)} worker(s) on queue '{args.queue}'...")
    
    # Run workers
    try:
        if args.burst:
            # Process all queued jobs and exit
            logger.info("Running in burst mode...")
            for worker in worker_instances:
                worker.work(burst=True)
        else:
            # Run indefinitely
            for worker in worker_instances:
                worker.work()
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
        for worker in worker_instances:
            worker.request_stop()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)
    
    logger.info("Worker shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
