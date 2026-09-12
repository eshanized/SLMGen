#!/usr/bin/env python3
"""
Recommend Router.

Returns model recommendations based on task and deployment target.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.middleware.auth import AnonymousUser, AuthenticatedUser, get_optional_user
from app.models import (
    DatasetCharacteristics,
    DatasetStats,
    RecommendationResponse,
    RecommendRequest,
)
from app.session_store import session_store
from app.storage import storage_service
from core import analyze_dataset, get_recommendations

logger = logging.getLogger(__name__)
router = APIRouter()


async def _load_dataset_for_analysis(session_data: dict) -> list[dict]:
    """
    Load dataset for analysis.

    Priority:
    1. raw_data in session
    2. Download from storage
    """
    data = session_data.get("raw_data", [])
    if data:
        return data

    dataset_path = session_data.get("dataset_path")
    if dataset_path:
        try:
            file_bytes = await storage_service.download_file(dataset_path)
            content = file_bytes.decode("utf-8")
            dataset = []
            for line in content.strip().split("\n"):
                line = line.strip()
                if line:
                    dataset.append(json.loads(line))
            return dataset
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load dataset from storage: {e}"
            )

    return []


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

    # Get or compute characteristics
    chars_dict = session_data.get("characteristics")
    if chars_dict is not None:
        characteristics = DatasetCharacteristics(**chars_dict)
    else:
        # Need to analyze first
        data = await _load_dataset_for_analysis(session_data)

        if not data:
            raise HTTPException(status_code=400, detail="No data available.")

        characteristics = analyze_dataset(data)

    # Save user selections + characteristics
    await session_store.update_session(request.session_id, {
        "characteristics": characteristics.model_dump(),
        "task_type": request.task.value,
        "deployment_target": request.deployment.value,
    })

    # Get recommendations
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
