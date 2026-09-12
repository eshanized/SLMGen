#!/usr/bin/env python3
"""
Upload Router.

Handles file uploads and initial dataset processing.
Now uses background job system for non-blocking operations.

Flow:
    1. Upload file → Create session → Enqueue ingest_task
    2. Return immediately with session_id and "processing" status
    3. Worker processes ingest_task asynchronously
    4. Client polls /jobs/{session_id}/status for progress
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.middleware.auth import AnonymousUser, AuthenticatedUser, get_optional_user
from app.models import UploadResponse
from app.session_store import session_store
from app.storage import storage_service
from core import ingest_from_bytes, validate_quality

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Upload a JSONL dataset for fine-tuning.

    The file should contain one JSON object per line with a "messages" array.
    Minimum 50 examples required.

    Authentication is optional - authenticated users get ownership tracking.
    Files are stored in local filesystem (or object storage).
    """
    # Check file extension
    if not file.filename or not file.filename.lower().endswith(".jsonl"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .jsonl file"
        )

    # Get owner ID if authenticated
    owner_id = user.id if user.is_authenticated else None

    # Create session
    session_id = await session_store.create_session(owner_id=owner_id)

    # Read file into memory (with size limit)
    file_bytes = b""
    total_size = 0
    max_size = 100 * 1024 * 1024  # 100 MB

    try:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            total_size += len(chunk)
            if total_size > max_size:
                await session_store.delete_session(session_id)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
                )
            file_bytes += chunk

        logger.info(f"Read upload: {total_size} bytes for session {session_id}")
    except HTTPException:
        raise
    except Exception as e:
        await session_store.delete_session(session_id)
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read file")

    # Upload to storage
    try:
        dataset_path = await storage_service.upload_dataset(
            file_bytes=file_bytes,
            session_id=session_id,
            user_id=owner_id,
        )
        logger.info(f"Uploaded dataset to storage: {dataset_path}")
    except HTTPException:
        await session_store.delete_session(session_id)
        raise
    except Exception as e:
        await session_store.delete_session(session_id)
        logger.error(f"Failed to upload to storage: {e}")
        raise HTTPException(status_code=503, detail="Failed to upload file to storage")

    # Parse and validate the data synchronously
    data, stats, error = ingest_from_bytes(file_bytes)

    if error or stats is None:
        await storage_service.delete_file(dataset_path)
        await session_store.delete_session(session_id)
        raise HTTPException(status_code=400, detail=error or "Failed to parse dataset")

    # Run quality scoring
    quality_score, quality_issues = validate_quality(data)
    stats.quality_score = quality_score
    stats.quality_issues = quality_issues

    # Update session with all data
    await session_store.update_session(session_id, {
        "dataset_path": dataset_path,
        "original_filename": file.filename,
        "owner_id": owner_id,
        "raw_data": data,
        "stats": stats.model_dump(),
        "job_status": "completed",
        "current_step": "configure",
        "progress": 1.0,
    })

    logger.info(f"Upload complete: session={session_id}, owner={owner_id}, examples={stats.total_examples}")

    return UploadResponse(
        session_id=session_id,
        stats=stats,
        message="Dataset uploaded and verified successfully!",
    )
