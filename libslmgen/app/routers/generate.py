#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Router.

Creates the Colab notebook and handles downloads.
Now uses object storage (Supabase) instead of local filesystem.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import asyncio
import json
import logging
import urllib.parse
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import Response

from app.config import settings
from app.session_store import session_store
from app.storage import storage_service
from app.models import GenerateRequest, NotebookResponse, TaskType
from app.gist import create_gist
from app.middleware.auth import get_optional_user, AuthenticatedUser, AnonymousUser
from core import generate_notebook
from core.recommender import MODELS

logger = logging.getLogger(__name__)
router = APIRouter()

# Notebook generation timeout (60 seconds)
GENERATION_TIMEOUT_SECONDS = 60


def _get_model_info(model_id: str) -> tuple[str, str, bool]:
    """
    Get model name, size, and gated status for notebook generation.
    
    Returns None if model_id is invalid.
    """
    for key, spec in MODELS.items():
        if spec.model_id == model_id:
            return spec.name, spec.size, spec.is_gated
    return None


def _validate_model_id(model_id: str) -> None:
    """Validate that model_id exists in MODELS dict."""
    valid_ids = [spec.model_id for spec in MODELS.values()]
    if model_id not in valid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_id. Valid options: {valid_ids}"
        )


def _build_colab_url(notebook_public_url: str) -> str:
    """
    Build a Google Colab URL that opens a notebook from a public URL.
    
    Colab supports opening notebooks via URL parameter.
    """
    encoded_url = urllib.parse.quote(notebook_public_url, safe='')
    return f"https://colab.research.google.com/notebooks/empty.ipynb#fileId={encoded_url}"


async def _load_dataset_content(session_data: dict) -> str:
    """
    Load dataset content from storage or session.
    
    Priority:
    1. raw_data in session (preferred - already in memory)
    2. Download from storage
    
    Returns:
        Dataset content as JSONL string
    """
    # Try raw_data first (already parsed in session)
    raw_data = session_data.get("raw_data")
    if raw_data and isinstance(raw_data, list):
        # Convert back to JSONL format
        lines = []
        for entry in raw_data:
            lines.append(json.dumps(entry))
        return "\n".join(lines)
    
    # Fall back to storage
    dataset_path = session_data.get("dataset_path")
    if dataset_path:
        file_bytes = await storage_service.download_file(dataset_path)
        return file_bytes.decode("utf-8")
    
    raise HTTPException(
        status_code=400,
        detail="Dataset not available."
    )


@router.post("/generate-notebook", response_model=NotebookResponse)
async def generate_training_notebook(
    request: GenerateRequest,
    http_request: Request,
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Generate a Colab notebook for the session's dataset.
    
    If model_id is not provided, uses the primary recommendation.
    
    Respects session ownership if authenticated.
    
    The notebook is uploaded to object storage (Supabase) and
    a signed download URL is returned.
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
    
    # Determine which model to use
    model_id = request.model_id or session_data.get("selected_model_id")
    if not model_id:
        raise HTTPException(
            status_code=400,
            detail="No model selected. Please get a recommendation first."
        )
    
    # Validate model_id exists
    _validate_model_id(model_id)
    
    # Get model info
    model_info = _get_model_info(model_id)
    if model_info is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid model_id."
        )
    model_name, model_size, is_gated = model_info
    
    # Load the dataset content
    try:
        dataset_content = await _load_dataset_content(session_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load dataset."
        )
    
    # Get task type string
    task_type_val = session_data.get("task_type", "general")
    
    # Generate the notebook with timeout
    try:
        notebook_json = await asyncio.wait_for(
            asyncio.to_thread(
                generate_notebook,
                dataset_jsonl=dataset_content,
                model_id=model_id,
                model_name=model_name,
                model_size=model_size,
                task_type=task_type_val,
                num_examples=stats_dict["total_examples"],
                is_gated=is_gated,
            ),
            timeout=GENERATION_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        logger.error(f"Notebook generation timed out for session {request.session_id}")
        raise HTTPException(
            status_code=504,
            detail="Notebook generation timed out. Try again with a smaller dataset."
        )
    except Exception as e:
        logger.error(f"Failed to generate notebook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate notebook: {e}")
    
    # Upload notebook to object storage
    notebook_filename = f"finetune_{model_name.lower().replace(' ', '_')}_{request.session_id[:8]}.ipynb"
    notebook_bytes = notebook_json.encode("utf-8")
    
    try:
        notebook_path = await storage_service.upload_notebook(
            file_bytes=notebook_bytes,
            session_id=request.session_id,
            user_id=user_id,
            original_filename=notebook_filename,
        )
        logger.info(f"Uploaded notebook to storage: {notebook_path}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload notebook to storage: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to upload notebook to storage."
        )
    
    # Update session with notebook path
    await session_store.update_session(request.session_id, {
        "notebook_path": notebook_path,
    })
    
    # Generate secure download token
    download_token = await session_store.generate_download_token(request.session_id)
    
    logger.info(f"Generated notebook: {notebook_filename}")
    
    # Build download URL with token
    download_url = f"/download/{request.session_id}?token={download_token}"
    
    # Generate Colab URL
    colab_url = None
    
    # Option 1: Try GitHub Gist first (if configured)
    if settings.github_token:
        try:
            colab_url = await create_gist(
                notebook_content=notebook_json,
                filename=notebook_filename,
                description=f"SLMGEN Fine-tuning Notebook - {model_name}",
            )
            if colab_url:
                logger.info(f"Created Gist with Colab URL: {colab_url}")
        except Exception as e:
            logger.warning(f"Failed to create Gist: {e}")
    
    # Option 2: Use signed URL for storage (fallback)
    if not colab_url:
        try:
            # Generate a long-lived signed URL for Colab
            colab_url = await storage_service.get_signed_url(
                notebook_path,
                expires_in=86400,  # 24 hours
            )
            # Wrap in Colab format
            encoded_url = urllib.parse.quote(colab_url, safe='')
            colab_url = f"https://colab.research.google.com/notebooks/empty.ipynb#fileId={encoded_url}"
            logger.info(f"Generated Colab URL with signed storage URL")
        except Exception as e:
            logger.warning(f"Failed to generate signed URL: {e}")
    
    return NotebookResponse(
        session_id=request.session_id,
        notebook_filename=notebook_filename,
        download_url=download_url,
        colab_url=colab_url,
        message=f"Notebook generated for {model_name}!",
    )


@router.get("/download/{session_id}")
async def download_notebook(
    session_id: str,
    token: str = Query(..., description="Download token from generate-notebook response"),
    user: AuthenticatedUser | AnonymousUser = Depends(get_optional_user)
):
    """
    Download the generated notebook file.
    
    Requires valid download token from generate-notebook response.
    Returns a signed URL for downloading the notebook.
    """
    # Validate download token first
    if not await session_store.validate_download_token(session_id, token):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired download token. Please regenerate the notebook."
        )
    
    user_id = user.id if user.is_authenticated else None
    session = await session_store.get_session_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found, expired, or access denied."
        )
    
    session_data = session.get("data", {})
    notebook_path = session_data.get("notebook_path")
    
    if not notebook_path:
        raise HTTPException(
            status_code=404,
            detail="Notebook not generated yet."
        )
    
    # Get signed URL for download
    try:
        signed_url = await storage_service.get_signed_url(
            notebook_path,
            expires_in=3600,  # 1 hour
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to generate download URL."
        )
    
    # Return redirect to signed URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=signed_url, status_code=302)


@router.get("/notebooks/{session_id}.ipynb")
async def get_public_notebook(session_id: str):
    """
    Public endpoint to serve notebooks for Google Colab integration.
    
    This endpoint serves notebooks WITHOUT authentication so that
    Google Colab can fetch them directly via URL.
    
    Note: Notebooks are stored in Supabase Storage and remain
    accessible until explicitly deleted.
    
    For permanent storage, use the GitHub Gist integration by setting
    GITHUB_TOKEN environment variable.
    """
    # Get session without owner check (public access)
    session = await session_store.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Notebook not found. Please generate a new notebook."
        )
    
    session_data = session.get("data", {})
    notebook_path = session_data.get("notebook_path")
    
    if not notebook_path:
        raise HTTPException(
            status_code=404,
            detail="Notebook not generated yet."
        )
    
    # Download notebook content from storage
    try:
        notebook_bytes = await storage_service.download_file(notebook_path)
        notebook_content = notebook_bytes.decode("utf-8")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download notebook from storage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve notebook."
        )
    
    # Extract filename from path
    filename = notebook_path.split("/")[-1] if "/" in notebook_path else f"{session_id}.ipynb"
    
    # Return as JSON with proper headers for Colab
    return Response(
        content=notebook_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Access-Control-Allow-Origin": "*",  # Allow Colab to fetch
            "Cache-Control": "no-cache",
        }
    )
