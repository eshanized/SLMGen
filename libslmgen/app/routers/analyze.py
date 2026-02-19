#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze Router.

Returns detailed dataset characteristics for model selection.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.session_store import session_store
from app.models import AnalyzeRequest, AnalyzeResponse, DatasetStats, DatasetCharacteristics
from app.middleware.auth import get_optional_user, AuthenticatedUser, AnonymousUser
from core import analyze_dataset, ingest_data

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_session(
    request: AnalyzeRequest,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Analyze an uploaded dataset and return characteristics.
    
    This extracts features like: multilingual, JSON output patterns,
    multi-turn conversations, etc. which help with model selection.
    
    Respects session ownership if authenticated.
    """
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(request.session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found, expired, or access denied. Please upload again."
        )
    
    session_data = session.get("data", {})
    stats_dict = session_data.get("stats")
    
    if stats_dict is None:
        raise HTTPException(
            status_code=400,
            detail="Dataset not processed yet."
        )
    
    stats = DatasetStats(**stats_dict)
    
    # If we already have characteristics cached, return Them
    chars_dict = session_data.get("characteristics")
    if chars_dict is not None:
        characteristics = DatasetCharacteristics(**chars_dict)
        return AnalyzeResponse(
            session_id=session["id"],
            stats=stats,
            characteristics=characteristics,
        )
    
    # Need to reload data if it was Cleared
    data = session_data.get("raw_data", [])
    if not data and session_data.get("file_path"):
        # Reload from File
        data, _, error = ingest_data(session_data["file_path"])
        if error:
            raise HTTPException(status_code=500, detail=f"Failed to reload data: {error}")
    
    if not data:
        raise HTTPException(
            status_code=400,
            detail="No data available for analysis."
        )
    
    # Run Analysis
    characteristics = analyze_dataset(data)
    
    # Cache it in Session
    await session_store.update_session(request.session_id, {
        "characteristics": characteristics.model_dump(),
    })
    
    logger.info(f"Analyzed session {session['id']}")
    
    return AnalyzeResponse(
        session_id=session["id"],
        stats=stats,
        characteristics=characteristics,
    )
