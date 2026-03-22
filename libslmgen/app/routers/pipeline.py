#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Router.

Provides job status and pipeline management endpoints.

This handles the background job system, not the Supabase job CRUD operations.
See jobs.py for the Supabase-backed job history endpoints.

Endpoints:
    GET /pipeline/{session_id}/status - Get job status and progress
    POST /pipeline/{session_id}/analyze - Trigger analysis
    POST /pipeline/{session_id}/recommend - Trigger recommendations
    POST /pipeline/{session_id}/generate - Trigger notebook generation
    POST /pipeline/{session_id}/run - Run full pipeline
    DELETE /pipeline/{session_id} - Cancel job
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from app.session_store import session_store
from app.models import DatasetStats
from app.middleware.auth import get_optional_user, AuthenticatedUser, AnonymousUser
from app.jobs import job_queue

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


class JobStatus(str, Enum):
    """Job status values."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStep(str, Enum):
    """Pipeline step values."""
    INGEST = "ingest"
    ANALYZE = "analyze"
    RECOMMEND = "recommend"
    GENERATE = "generate"


@router.get("/{session_id}/status")
async def get_job_status(
    session_id: str,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Get the current status of a job/pipeline.
    
    Returns:
        - status: queued | processing | completed | failed
        - current_step: ingest | analyze | recommend | generate
        - progress: 0.0 to 1.0
        - stats: DatasetStats if available
        - error: Error message if failed
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied."
        )
    
    session_data = session.get("data", {})
    
    status = session_data.get("job_status", "queued")
    current_step = session_data.get("current_step", "ingest")
    progress = session_data.get("progress", 0.0)
    error = session_data.get("job_error")
    
    # Get stats if available
    stats = None
    stats_dict = session_data.get("stats")
    if stats_dict:
        try:
            stats = DatasetStats(**stats_dict)
        except Exception:
            pass
    
    # Build response
    response = {
        "session_id": session_id,
        "status": status,
        "current_step": current_step,
        "progress": progress,
        "steps": {
            "ingest": "completed" if session_data.get("ingest_done") else status,
            "analyze": "completed" if session_data.get("analyze_done") else "pending",
            "recommend": "completed" if session_data.get("recommend_done") else "pending",
            "generate": "completed" if session_data.get("notebook_path") else "pending",
        },
    }
    
    if stats:
        response["stats"] = stats
    
    if error:
        response["error"] = error
    
    # Add recommendations if available
    if session_data.get("recommendations"):
        response["recommendations"] = session_data.get("recommendations")
    
    # Add notebook info if generated
    if session_data.get("notebook_path"):
        response["notebook_path"] = session_data.get("notebook_path")
    
    return response


@router.post("/{session_id}/analyze")
async def trigger_analysis(
    session_id: str,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Trigger dataset analysis.
    
    Usually run automatically after ingest, but can be triggered manually.
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied."
        )
    
    session_data = session.get("data", {})
    
    if not session_data.get("ingest_done"):
        raise HTTPException(
            status_code=400,
            detail="Ingest not complete. Upload a dataset first."
        )
    
    if session_data.get("analyze_done"):
        return {
            "message": "Analysis already completed.",
            "status": "completed",
        }
    
    # Enqueue analyze task
    if not job_queue.is_connected:
        from app.jobs.tasks import analyze_task
        try:
            analyze_task(session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        job = job_queue.enqueue("analyze_task", session_id=session_id)
        if not job:
            raise HTTPException(status_code=503, detail="Job queue unavailable.")
    
    return {
        "message": "Analysis started.",
        "status": "queued",
    }


@router.post("/{session_id}/recommend")
async def trigger_recommendations(
    session_id: str,
    task_type: str = "general",
    deployment: str = "cloud",
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Trigger model recommendations.
    
    Args:
        task_type: Task type (general, instruction, chat, etc.)
        deployment: Deployment target (cloud, edge, mobile, browser)
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied."
        )
    
    session_data = session.get("data", {})
    
    if not session_data.get("analyze_done"):
        raise HTTPException(
            status_code=400,
            detail="Analysis not complete. Run analysis first."
        )
    
    if session_data.get("recommend_done"):
        return {
            "message": "Recommendations already generated.",
            "recommendations": session_data.get("recommendations"),
        }
    
    # Update session with parameters
    await session_store.update_session(session_id, {
        "task_type": task_type,
        "deployment_target": deployment,
    })
    
    # Enqueue recommend task
    if not job_queue.is_connected:
        from app.jobs.tasks import recommend_task
        try:
            recommend_task(session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        job = job_queue.enqueue("recommend_task", session_id=session_id)
        if not job:
            raise HTTPException(status_code=503, detail="Job queue unavailable.")
    
    return {
        "message": "Recommendations started.",
        "status": "queued",
    }


@router.post("/{session_id}/generate")
async def trigger_generation(
    session_id: str,
    model_id: Optional[str] = None,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Trigger notebook generation.
    
    Args:
        model_id: Optional model override. Uses selected model if not provided.
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied."
        )
    
    session_data = session.get("data", {})
    
    if not session_data.get("recommend_done"):
        raise HTTPException(
            status_code=400,
            detail="Recommendations not complete. Get recommendations first."
        )
    
    selected_model = model_id or session_data.get("selected_model_id")
    if not selected_model:
        raise HTTPException(
            status_code=400,
            detail="No model selected. Get recommendations first."
        )
    
    if session_data.get("notebook_path") and not model_id:
        return {
            "message": "Notebook already generated.",
            "notebook_path": session_data.get("notebook_path"),
        }
    
    # Enqueue generate task
    if not job_queue.is_connected:
        from app.jobs.tasks import generate_notebook_task
        try:
            generate_notebook_task(session_id, model_id=model_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        job = job_queue.enqueue("generate_notebook_task", session_id=session_id, model_id=model_id)
        if not job:
            raise HTTPException(status_code=503, detail="Job queue unavailable.")
    
    return {
        "message": "Notebook generation started.",
        "status": "queued",
    }


@router.post("/{session_id}/run")
async def run_full_pipeline(
    session_id: str,
    task_type: str = "general",
    deployment: str = "cloud",
    model_id: Optional[str] = None,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Run the full pipeline: analyze → recommend → generate.
    
    Assumes ingest is already complete.
    
    Args:
        task_type: Task type for recommendations
        deployment: Deployment target
        model_id: Optional model override
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied."
        )
    
    session_data = session.get("data", {})
    
    if not session_data.get("ingest_done"):
        raise HTTPException(
            status_code=400,
            detail="Ingest not complete. Upload a dataset first."
        )
    
    # Update parameters
    await session_store.update_session(session_id, {
        "task_type": task_type,
        "deployment_target": deployment,
    })
    
    # Enqueue all tasks
    tasks = []
    
    if not session_data.get("analyze_done"):
        tasks.append(("analyze_task", {"session_id": session_id}))
    
    tasks.append(("recommend_task", {"session_id": session_id}))
    
    if not session_data.get("notebook_path") or model_id:
        tasks.append(("generate_notebook_task", {
            "session_id": session_id,
            "model_id": model_id,
        }))
    
    if not job_queue.is_connected:
        # Run synchronously
        from app.jobs.tasks import analyze_task, recommend_task, generate_notebook_task
        task_map = {
            "analyze_task": analyze_task,
            "recommend_task": recommend_task,
            "generate_notebook_task": generate_notebook_task,
        }
        for task_name, kwargs in tasks:
            try:
                task_map[task_name](**kwargs)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    else:
        # Enqueue tasks
        for task_name, kwargs in tasks:
            job = job_queue.enqueue(task_name, **kwargs)
            if not job:
                raise HTTPException(status_code=503, detail=f"Failed to enqueue {task_name}")
    
    return {
        "message": f"Pipeline started with {len(tasks)} tasks.",
        "tasks": len(tasks),
        "status": "queued",
    }


@router.delete("/{session_id}")
async def cancel_job(
    session_id: str,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Cancel a running job or clear session.
    
    Note: This doesn't kill running jobs, just marks them as cancelled.
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied."
        )
    
    await session_store.update_session(session_id, {
        "job_status": "cancelled",
        "current_step": None,
    })
    
    return {
        "message": "Job cancelled.",
        "session_id": session_id,
    }
