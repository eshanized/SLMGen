#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Training Progress Router.

API endpoints for training progress tracking:
- Webhook receiver for Colab notebook callbacks
- Event streaming via SSE
- Status and history queries
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..models import (
    TrainingEventRequest,
    TrainingStartRequest,
    TrainingCompleteRequest,
    TrainingStatusResponse,
    TrainingEventResponse,
)
from ...core.training_tracker import training_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


@router.post("/start")
async def start_training_session(request: TrainingStartRequest) -> dict:
    """
    Start a new training session.
    
    Called before training begins to initialize progress tracking.
    """
    session = training_tracker.start_session(
        session_id=request.session_id,
        job_id=request.job_id,
        model_id=request.model_id,
        total_steps=request.total_steps,
        total_epochs=request.total_epochs,
    )
    
    return {
        "message": "Training session started",
        "session_id": session.session_id,
        "status": session.status.value,
    }


@router.post("/webhook")
async def training_webhook(event: TrainingEventRequest) -> dict:
    """
    Receive training events from Colab notebook.
    
    This endpoint is called periodically during training to report
    progress (step, loss, epoch, etc.).
    """
    success = training_tracker.add_event(
        session_id=event.session_id,
        step=event.step,
        loss=event.loss,
        epoch=event.epoch,
        learning_rate=event.learning_rate,
        grad_norm=event.grad_norm,
        tokens_per_second=event.tokens_per_second,
        gpu_memory_used=event.gpu_memory_used,
    )
    
    if not success:
        # Don't raise error - notebook should continue training
        # Just log and return success to avoid blocking training
        logger.warning(f"Session not found for webhook: {event.session_id}")
        return {"message": "Session not found, event ignored", "received": False}
    
    return {"message": "Event received", "received": True}


@router.post("/complete")
async def complete_training(request: TrainingCompleteRequest) -> dict:
    """
    Mark training as completed or failed.
    
    Called at the end of training from Colab notebook.
    """
    if request.error:
        success = training_tracker.fail_session(request.session_id, request.error)
        status = "failed"
    else:
        success = training_tracker.complete_session(request.session_id)
        status = "completed"
    
    if not success:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    return {"message": f"Training marked as {status}", "session_id": request.session_id}


@router.get("/{session_id}/status")
async def get_training_status(session_id: str) -> TrainingStatusResponse:
    """
    Get the current status of a training session.
    
    Returns progress, ETA, and latest metrics.
    """
    status = training_tracker.get_status(session_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    return TrainingStatusResponse(**status)


@router.get("/{session_id}/events")
async def get_training_events(
    session_id: str,
    since_step: Optional[int] = Query(None, description="Only return events after this step"),
) -> list[TrainingEventResponse]:
    """
    Get all training events for a session.
    
    Optionally filter by step number for incremental updates.
    """
    events = training_tracker.get_events(session_id, since_step)
    
    if not events and training_tracker.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    return [TrainingEventResponse(**e) for e in events]


@router.get("/{session_id}/latest")
async def get_latest_event(session_id: str) -> TrainingEventResponse:
    """
    Get the latest training event for a session.
    """
    event = training_tracker.get_latest(session_id)
    
    if event is None:
        raise HTTPException(status_code=404, detail="No events found for session")
    
    return TrainingEventResponse(**event)


@router.get("/{session_id}/stream")
async def stream_training_events(
    session_id: str,
    interval: float = Query(2.0, ge=0.5, le=10.0, description="Polling interval in seconds"),
) -> StreamingResponse:
    """
    Stream training events via Server-Sent Events (SSE).
    
    The client should connect to this endpoint and receive real-time
    updates as training progresses.
    
    Example client code (JavaScript):
    ```js
    const eventSource = new EventSource('/training/SESSION_ID/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Training update:', data);
    };
    ```
    """
    session = training_tracker.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    async def event_generator():
        """Generate SSE events."""
        last_step = 0
        
        while True:
            # Get latest status
            status = training_tracker.get_status(session_id)
            
            if status is None:
                # Session was cleaned up
                yield "event: error\ndata: Session expired\n\n"
                break
            
            # Get new events since last step
            new_events = training_tracker.get_events(session_id, last_step)
            
            if new_events:
                last_step = new_events[-1]["step"]
                
                # Send status update
                import json
                yield f"data: {json.dumps(status)}\n\n"
            
            # Check if training is complete
            if status["status"] in ("completed", "failed"):
                yield f"event: complete\ndata: {json.dumps(status)}\n\n"
                break
            
            await asyncio.sleep(interval)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/")
async def list_training_sessions() -> list[dict]:
    """
    List all active training sessions.
    
    For debugging and monitoring purposes.
    """
    return training_tracker.list_sessions()
