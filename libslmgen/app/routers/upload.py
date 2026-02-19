#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload Router.

Handles file uploads and initial dataset processing.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.config import settings
from app.session_store import session_store
from app.models import UploadResponse
from app.middleware.auth import get_optional_user, AuthenticatedUser, AnonymousUser
from core import ingest_data, validate_quality

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
    """
    # Check file Extension
    if not file.filename or not file.filename.lower().endswith(".jsonl"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .jsonl file"
        )
    
    # Get owner ID if authenticated
    owner_id = user.id if user.is_authenticated else None
    
    # Create session in Redis
    session_id = await session_store.create_session(owner_id=owner_id)
    
    # Save file to disk with size limit
    file_path = Path(settings.upload_dir) / f"{session_id}.jsonl"
    total_size = 0
    
    try:
        async with aiofiles.open(file_path, "wb") as f:
            # Stream file with size checking
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > settings.max_upload_bytes:
                    await f.close()
                    file_path.unlink(missing_ok=True)
                    await session_store.delete_session(session_id)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {settings.max_upload_bytes // (1024*1024)}MB"
                    )
                await f.write(chunk)
        
        logger.info(f"Saved upload to {file_path} ({total_size} bytes)")
    except HTTPException:
        raise
    except Exception as e:
        await session_store.delete_session(session_id)
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Parse and validate the Data
    data, stats, error = ingest_data(str(file_path))
    
    if error:
        # Cleanup on Error
        await session_store.delete_session(session_id)
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=error)
    
    # Run quality Checks
    quality_score, quality_issues = validate_quality(data)
    stats.quality_score = quality_score
    stats.quality_issues = quality_issues
    
    # Update session with all data
    await session_store.update_session(session_id, {
        "file_path": str(file_path),
        "original_filename": file.filename,
        "raw_data": data,
        "stats": stats.model_dump(),
    })
    
    logger.info(f"Upload complete: session={session_id}, examples={stats.total_examples}, owner={owner_id}")
    
    return UploadResponse(
        session_id=session_id,
        stats=stats,
        message=f"Dataset uploaded! Found {stats.total_examples} examples.",
    )
