#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload Router.

Handles file uploads and initial dataset processing.
Now uses object storage (Supabase) instead of local filesystem.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import io
import json
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.session_store import session_store
from app.storage import storage_service
from app.models import UploadResponse
from app.middleware.auth import get_optional_user, AuthenticatedUser, AnonymousUser
from core import validate_quality

logger = logging.getLogger(__name__)
router = APIRouter()


def ingest_from_bytes(file_bytes: bytes) -> tuple[list[dict], dict, Optional[str]]:
    """
    Parse and validate JSONL from bytes.
    
    This replaces ingest_data(file_path) for in-memory processing.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        - raw_data: List of valid conversation dicts
        - stats: DatasetStats-like dict
        - error: Error message if failed, None on success
    """
    import re
    from app.models import DatasetStats
    
    MIN_EXAMPLES = 50
    
    def estimate_tokens(text: str) -> int:
        """Rough token estimation."""
        return max(1, len(text) // 4)
    
    def validate_message(msg: dict) -> tuple[bool, str]:
        if not isinstance(msg, dict):
            return False, "message must be a dict"
        role = msg.get("role")
        content = msg.get("content")
        if role not in ("user", "assistant", "system"):
            return False, f"invalid role: {role}"
        if not isinstance(content, str):
            return False, "content must be a string"
        return True, ""
    
    def validate_conversation(entry: dict, idx: int) -> tuple[bool, str]:
        if not isinstance(entry, dict):
            return False, f"Line {idx}: must be a JSON object"
        messages = entry.get("messages")
        if not isinstance(messages, list):
            return False, f"Line {idx}: missing or invalid 'messages' array"
        if len(messages) < 2:
            return False, f"Line {idx}: need at least 2 messages"
        has_user = False
        has_assistant = False
        for i, msg in enumerate(messages):
            valid, err = validate_message(msg)
            if not valid:
                return False, f"Line {idx}, message {i}: {err}"
            if msg.get("role") == "user":
                has_user = True
            elif msg.get("role") == "assistant":
                has_assistant = True
        if not has_user:
            return False, f"Line {idx}: must have at least one user message"
        if not has_assistant:
            return False, f"Line {idx}: must have at least one assistant message"
        return True, ""
    
    data: list[dict] = []
    errors: list[str] = []
    total_tokens = 0
    single_turn = 0
    multi_turn = 0
    has_system = False
    
    # Parse JSONL from bytes
    content = file_bytes.decode("utf-8")
    lines = content.strip().split("\n")
    
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Line {line_num}: Invalid JSON - {e}")
            continue
        
        valid, err = validate_conversation(entry, line_num)
        if not valid:
            errors.append(err)
            continue
        
        messages = entry["messages"]
        data.append(entry)
        
        for msg in messages:
            total_tokens += estimate_tokens(msg.get("content", ""))
            if msg.get("role") == "system":
                has_system = True
        
        non_system = [m for m in messages if m.get("role") != "system"]
        if len(non_system) == 2:
            single_turn += 1
        else:
            multi_turn += 1
    
    if len(data) < MIN_EXAMPLES:
        return [], None, (
            f"Need at least {MIN_EXAMPLES} examples for fine-tuning. "
            f"You only have {len(data)}. Maybe try adding more data?"
        )
    
    if errors:
        logger.warning(f"Found {len(errors)} validation issues")
        for err in errors[:5]:
            logger.warning(f"  - {err}")
    
    total = len(data)
    single_pct = int((single_turn / total) * 100) if total > 0 else 0
    multi_pct = 100 - single_pct
    avg_tokens = total_tokens // total if total > 0 else 0
    
    stats = DatasetStats(
        total_examples=total,
        total_tokens=total_tokens,
        avg_tokens_per_example=avg_tokens,
        single_turn_pct=single_pct,
        multi_turn_pct=multi_pct,
        has_system_prompts=has_system,
        quality_score=1.0,  # placeholder
        quality_issues=[],
    )
    
    return data, stats, None


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
    
    Files are stored in Supabase Storage (or local filesystem in dev mode).
    """
    # Check file extension
    if not file.filename or not file.filename.lower().endswith(".jsonl"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .jsonl file"
        )
    
    # Get owner ID if authenticated
    owner_id = user.id if user.is_authenticated else None
    
    # Create session in Redis
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
    
    # Upload to object storage
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
    
    # Parse and validate the data
    data, stats, error = ingest_from_bytes(file_bytes)
    
    if error:
        # Cleanup on error
        await storage_service.delete_file(dataset_path)
        await session_store.delete_session(session_id)
        raise HTTPException(status_code=400, detail=error)
    
    # Run quality checks
    quality_score, quality_issues = validate_quality(data)
    stats.quality_score = quality_score
    stats.quality_issues = quality_issues
    
    # Update session with all data
    await session_store.update_session(session_id, {
        "dataset_path": dataset_path,
        "original_filename": file.filename,
        "raw_data": data,  # Keep in session for analysis
        "stats": stats.model_dump(),
    })
    
    logger.info(f"Upload complete: session={session_id}, examples={stats.total_examples}, owner={owner_id}")
    
    return UploadResponse(
        session_id=session_id,
        stats=stats,
        message=f"Dataset uploaded! Found {stats.total_examples} examples.",
    )
