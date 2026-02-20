#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recommend Router.

Returns model recommendations based on task and deployment target.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.session_store import session_store
from app.models import RecommendRequest, RecommendationResponse, DatasetStats, DatasetCharacteristics
from app.middleware.auth import get_optional_user, AuthenticatedUser, AnonymousUser
from core import analyze_dataset, get_recommendations, ingest_data

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/recommend", response_model=RecommendationResponse)
async def get_model_recommendation(
    request: RecommendRequest,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Get model recommendations based on task, deployment, and dataset.
    
    Returns a primary recommendation and alternatives with scores.
    
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
    
    # Get or compute Characteristics
    chars_dict = session_data.get("characteristics")
    if chars_dict is not None:
        characteristics = DatasetCharacteristics(**chars_dict)
    else:
        # Need to Analyze first
        data = session_data.get("raw_data", [])
        if not data and session_data.get("file_path"):
            data, _, error = ingest_data(session_data["file_path"])
            if error:
                raise HTTPException(status_code=500, detail=f"Failed to reload data: {error}")
        
        if not data:
            raise HTTPException(status_code=400, detail="No data available.")
        
        characteristics = analyze_dataset(data)
    
    # Save user selections + characteristics
    await session_store.update_session(request.session_id, {
        "characteristics": characteristics.model_dump(),
        "task_type": request.task.value,
        "deployment_target": request.deployment.value,
    })
    
    # Get Recommendations
    recommendations = get_recommendations(
        task=request.task,
        deployment=request.deployment,
        stats=stats,
        characteristics=characteristics,
    )
    
    # Store the primary recommendation
    await session_store.update_session(request.session_id, {
        "selected_model_id": recommendations.primary.model_id,
    })
    
    logger.info(f"Recommended {recommendations.primary.model_name} for session {session['id']}")
    
    return recommendations
