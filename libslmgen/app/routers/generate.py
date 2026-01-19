#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Router.

Creates the Colab notebook and handles downloads.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.session import session_manager
from app.models import GenerateRequest, NotebookResponse
from app.gist import create_gist
from core import generate_notebook
from core.recommender import MODELS

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_model_info(model_id: str) -> tuple[str, str, bool]:
    """
    Get model name, size, and gated status for notebook generation.
    
    FIX: A2 - Now returns is_gated from MODELS instead of re-detecting.
    """
    for key, spec in MODELS.items():
        if spec.model_id == model_id:
            return spec.name, spec.size, spec.is_gated
    # Fallback for unknown models
    return model_id.split("/")[-1], "3B", False


@router.post("/generate-notebook", response_model=NotebookResponse)
async def generate_training_notebook(request: GenerateRequest):
    """
    Generate a Colab notebook for the session's dataset.
    
    If model_id is not provided, uses the primary recommendation.
    """
    session = session_manager.get(request.session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please upload again."
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
    
    # Get Model info
    model_name, model_size, is_gated = _get_model_info(model_id)
    
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
    
    # Generate the Notebook
    try:
        notebook_json = generate_notebook(
            dataset_jsonl=dataset_content,
            model_id=model_id,
            model_name=model_name,
            model_size=model_size,
            task_type=task_type,
            num_examples=session.stats.total_examples,
            is_gated=is_gated,
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
    
    logger.info(f"Generated notebook: {notebook_filename}")
    
    # Build download URL
    download_url = f"/download/{request.session_id}"
    
    # Create GitHub Gist for Colab URL (if configured)
    colab_url = None
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
            # Don't fail the whole request if Gist creation fails
    
    return NotebookResponse(
        session_id=request.session_id,
        notebook_filename=notebook_filename,
        download_url=download_url,
        colab_url=colab_url,
        message=f"Notebook generated for {model_name}!",
    )


@router.get("/download/{session_id}")
async def download_notebook(session_id: str):
    """Download the generated notebook File."""
    session = session_manager.get(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
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
