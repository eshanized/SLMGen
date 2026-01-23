#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Router.

Creates the Colab notebook and handles downloads.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import asyncio
import logging
import urllib.parse
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.session import session_manager
from app.models import GenerateRequest, NotebookResponse
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
    """
    user_id = user.id if user.is_authenticated else None
    session = session_manager.get_with_owner(request.session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found, expired, or access denied. Please upload again."
        )
    
    if session.stats is None:
        raise HTTPException(
            status_code=400,
            detail="Dataset not processed yet."
        )
    
    # Determine which model to Use
    model_id = request.model_id or session.selected_model_id
    if not model_id:
        raise HTTPException(
            status_code=400,
            detail="No model selected. Please get a recommendation first."
        )
    
    # Validate model_id exists
    _validate_model_id(model_id)
    
    # Get Model info
    model_info = _get_model_info(model_id)
    if model_info is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid model_id."
        )
    model_name, model_size, is_gated = model_info
    
    # Load the dataset Content
    if not session.file_path or not Path(session.file_path).exists():
        raise HTTPException(
            status_code=400,
            detail="Dataset file not found."
        )
    
    with open(session.file_path, "r", encoding="utf-8") as f:
        dataset_content = f.read()
    
    # Get task type String
    task_type = session.task_type.value if session.task_type else "general"
    
    # Generate the Notebook with timeout
    try:
        notebook_json = await asyncio.wait_for(
            asyncio.to_thread(
                generate_notebook,
                dataset_jsonl=dataset_content,
                model_id=model_id,
                model_name=model_name,
                model_size=model_size,
                task_type=task_type,
                num_examples=session.stats.total_examples,
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
    
    # Save notebook to File
    notebook_filename = f"finetune_{model_name.lower().replace(' ', '_')}_{request.session_id[:8]}.ipynb"
    notebook_path = Path(settings.upload_dir) / notebook_filename
    
    with open(notebook_path, "w", encoding="utf-8") as f:
        f.write(notebook_json)
    
    session.notebook_path = str(notebook_path)
    session_manager.update(session)
    
    # Generate secure download token
    download_token = session_manager.generate_download_token(request.session_id)
    
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
            # Fall through to public URL method
    
    # Option 2: Use public notebook endpoint (fallback)
    if not colab_url:
        # Build the public notebook URL using the request's base URL
        base_url = str(http_request.base_url).rstrip('/')
        public_notebook_url = f"{base_url}/notebooks/{request.session_id}.ipynb"
        colab_url = _build_colab_url(public_notebook_url)
        logger.info(f"Generated public Colab URL: {colab_url}")
    
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
    Download the generated notebook File.
    
    Requires valid download token from generate-notebook response.
    """
    # Validate download token first
    if not session_manager.validate_download_token(session_id, token):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired download token. Please regenerate the notebook."
        )
    
    user_id = user.id if user.is_authenticated else None
    session = session_manager.get_with_owner(session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found, expired, or access denied."
        )
    
    if not session.notebook_path or not Path(session.notebook_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Notebook not generated yet."
        )
    
    filename = Path(session.notebook_path).name
    
    return FileResponse(
        path=session.notebook_path,
        filename=filename,
        media_type="application/x-ipynb+json",
    )


@router.get("/notebooks/{session_id}.ipynb")
async def get_public_notebook(session_id: str):
    """
    Public endpoint to serve notebooks for Google Colab integration.
    
    This endpoint serves notebooks WITHOUT authentication so that
    Google Colab can fetch them directly via URL.
    
    Note: Notebooks are only available while the session is active.
    After session expiry (default 30 minutes), the notebook won't be accessible.
    
    For permanent storage, use the GitHub Gist integration by setting
    GITHUB_TOKEN environment variable.
    """
    # Get session without owner check (public access)
    session = session_manager.get(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Notebook not found or session expired. Please generate a new notebook."
        )
    
    if not session.notebook_path or not Path(session.notebook_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Notebook not generated yet."
        )
    
    # Read notebook content
    with open(session.notebook_path, "r", encoding="utf-8") as f:
        notebook_content = f.read()
    
    # Return as JSON with proper headers for Colab
    return Response(
        content=notebook_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"inline; filename={Path(session.notebook_path).name}",
            "Access-Control-Allow-Origin": "*",  # Allow Colab to fetch
            "Cache-Control": "no-cache",  # Don't cache as session may expire
        }
    )
