#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Training Progress Router.

API endpoints for training progress tracking using Redis Streams:
- Webhook receiver for Colab notebook callbacks
- Event streaming via SSE (Server-Sent Events)
- Status and history queries

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.training_store import training_store, TrainingStatus
from app.models import (
    TrainingEventRequest,
    TrainingStartRequest,
    TrainingCompleteRequest,
    TrainingStatusResponse,
    TrainingEventResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


def _build_status_response(state: dict) -> TrainingStatusResponse:
    """Convert state dict to TrainingStatusResponse."""
    return TrainingStatusResponse(
        session_id=state.get("session_id", ""),
        job_id=state.get("job_id", ""),
        model_id=state.get("model_id", ""),
        status=state.get("status", TrainingStatus.PENDING.value),
        total_steps=state.get("total_steps", 0),
        total_epochs=state.get("total_epochs", 1),
        current_step=state.get("current_step", 0),
        current_epoch=state.get("current_epoch", 0),
        progress_percent=state.get("progress_percent", 0.0),
        latest_loss=state.get("latest_loss"),
        eta_seconds=state.get("eta_seconds"),
        eta_formatted=state.get("eta_formatted"),
        created_at=state.get("created_at", ""),
        started_at=state.get("started_at"),
        completed_at=state.get("completed_at"),
        error_message=state.get("error_message"),
        event_count=state.get("event_count", 0),
    )


@router.post("/start")
async def start_training_session(request: TrainingStartRequest) -> dict:
    """
    Start a new training session.
    
    Called before training begins to initialize progress tracking in Redis.
    """
    try:
        await training_store.start_session(
            session_id=request.session_id,
            metadata={
                "job_id": request.job_id,
                "model_id": request.model_id,
                "total_steps": request.total_steps,
                "total_epochs": request.total_epochs,
            },
        )
        
        return {
            "message": "Training session started",
            "session_id": request.session_id,
            "status": TrainingStatus.RUNNING.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start training session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start training session")


@router.post("/webhook")
async def training_webhook(event: TrainingEventRequest) -> dict:
    """
    Receive training events from Colab notebook.
    
    This endpoint is called periodically during training to report
    progress (step, loss, epoch, etc.). Events are written to
    Redis Streams and update the state snapshot.
    
    Note: If the session doesn't exist, we return success to avoid
    blocking training. The Colab notebook should continue regardless.
    """
    try:
        # Get current state for total_steps (needed for ETA calculation)
        state = await training_store.get_state(event.session_id)
        total_steps = state.get("total_steps", 0) if state else 0
        
        event_id = await training_store.add_event(
            session_id=event.session_id,
            event={
                "step": event.step,
                "loss": event.loss,
                "epoch": event.epoch,
                "learning_rate": event.learning_rate,
                "grad_norm": event.grad_norm,
                "tokens_per_second": event.tokens_per_second,
                "gpu_memory_used": event.gpu_memory_used,
                "total_steps": total_steps,
            },
        )
        
        return {
            "message": "Event received",
            "received": True,
            "event_id": event_id,
        }
        
    except HTTPException as e:
        if e.status_code == 404:
            # Session not found - don't block training
            logger.warning(f"Session not found for webhook: {event.session_id}")
            return {"message": "Session not found, event ignored", "received": False}
        raise
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        # Return success to avoid blocking training
        return {"message": "Event processing failed", "received": False}


@router.post("/complete")
async def complete_training(request: TrainingCompleteRequest) -> dict:
    """
    Mark training as completed or failed.
    
    Called at the end of training from Colab notebook.
    """
    try:
        await training_store.complete_session(
            session_id=request.session_id,
            error=request.error,
        )
        
        status = "failed" if request.error else "completed"
        
        return {
            "message": f"Training marked as {status}",
            "session_id": request.session_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete training session: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete training session")


@router.get("/{session_id}/status")
async def get_training_status(session_id: str) -> TrainingStatusResponse:
    """
    Get the current status of a training session.
    
    Uses the state snapshot for fast reads.
    """
    state = await training_store.get_state(session_id)
    
    if state is None:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    return _build_status_response(state)


@router.get("/{session_id}/events")
async def get_training_events(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    after_id: Optional[str] = Query(None, description="Return events after this ID"),
) -> list[TrainingEventResponse]:
    """
    Get training events for a session.
    
    Returns events newest-first (most recent first). Use after_id
    for pagination through older events.
    """
    # Check if session exists
    exists = await training_store.session_exists(session_id)
    if not exists:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    events = await training_store.get_events(
        session_id=session_id,
        limit=limit,
        after_id=after_id,
    )
    
    return [
        TrainingEventResponse(
            step=e.get("step", 0),
            loss=e.get("loss", 0.0),
            epoch=e.get("epoch", 0),
            learning_rate=e.get("learning_rate", 0.0),
            timestamp=e.get("timestamp", ""),
            grad_norm=e.get("grad_norm"),
            tokens_per_second=e.get("tokens_per_second"),
            gpu_memory_used=e.get("gpu_memory_used"),
        )
        for e in events
    ]


@router.get("/{session_id}/latest")
async def get_latest_event(session_id: str) -> TrainingEventResponse:
    """
    Get the latest training event for a session.
    """
    event = await training_store.get_latest(session_id)
    
    if event is None:
        raise HTTPException(status_code=404, detail="No events found for session")
    
    return TrainingEventResponse(
        step=event.get("step", 0),
        loss=event.get("loss", 0.0),
        epoch=event.get("epoch", 0),
        learning_rate=event.get("learning_rate", 0.0),
        timestamp=event.get("timestamp", ""),
        grad_norm=event.get("grad_norm"),
        tokens_per_second=event.get("tokens_per_second"),
        gpu_memory_used=event.get("gpu_memory_used"),
    )


@router.get("/{session_id}/stream")
async def stream_training_events(
    session_id: str,
    last_id: Optional[str] = Query(None, description="Last event ID received by client"),
) -> StreamingResponse:
    """
    Stream training events via Server-Sent Events (SSE).
    
    Uses Redis XREAD BLOCK for efficient real-time streaming.
    Events are streamed as JSON with the following structure:
    
    ```json
    {"type": "event", "id": "1234-0", "step": 100, "loss": 0.5, ...}
    {"type": "state", "data": {...}}
    {"type": "complete", "data": {"status": "completed", ...}}
    ```
    
    Client code example (JavaScript):
    ```javascript
    const eventSource = new EventSource(
        '/training/SESSION_ID/stream?last_id=' + lastEventId
    );
    
    eventSource.addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'event') {
            console.log('Progress:', data.step, 'Loss:', data.loss);
        } else if (data.type === 'complete') {
            console.log('Training complete!');
            eventSource.close();
        }
    });
    ```
    
    The stream continues until:
    - Training completes or fails (type: "complete")
    - Client disconnects (stream closes)
    - Redis error occurs (type: "error")
    
    Heartbeat messages (type: "heartbeat") are sent every ~2 seconds
    when no new events are available.
    """
    # Check if session exists first
    exists = await training_store.session_exists(session_id)
    if not exists:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    async def event_generator():
        """
        Async generator for SSE events.
        
        Yields formatted SSE messages. Handles client disconnection
        gracefully via asyncio.CancelledError.
        """
        try:
            # Stream events from Redis
            async for message in training_store.stream_events(session_id, last_id):
                msg_type = message.get("type", "event")
                
                if msg_type == "state":
                    # Initial state - include in status update
                    state = message.get("data", {})
                    yield f"event: status\ndata: {json.dumps(state)}\n\n"
                    
                elif msg_type == "event":
                    # Training progress event
                    yield f"data: {json.dumps(message)}\n\n"
                    
                elif msg_type == "complete":
                    # Training finished
                    state = message.get("data", {})
                    yield f"event: complete\ndata: {json.dumps(state)}\n\n"
                    break
                    
                elif msg_type == "heartbeat":
                    # Keep-alive - sent every ~2 seconds
                    yield f": heartbeat\n\n"
                    
                elif msg_type == "error":
                    # Error occurred
                    yield f"event: error\ndata: {json.dumps({'error': message.get('data')})}\n\n"
                    break
                    
        except asyncio.CancelledError:
            # Client disconnected
            logger.debug(f"SSE client disconnected: {session_id}")
        except Exception as e:
            logger.error(f"SSE stream error for {session_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
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
    sessions = await training_store.list_sessions()
    return sessions


@router.delete("/{session_id}")
async def delete_training_session(session_id: str) -> dict:
    """
    Delete a training session and all its data.
    
    Use with caution - this is irreversible.
    """
    try:
        await training_store.delete_session(session_id)
        return {"message": "Training session deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete training session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete training session")
