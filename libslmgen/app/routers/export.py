#!/usr/bin/env python3
"""
Export Router.

Provides export instructions for various deployment formats.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.export import (
    generate_ollama_modelfile,
    get_export_instructions,
    list_export_formats,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ExportRequest(BaseModel):
    """Export request."""
    model_id: str
    format: str  # "ollama", "gguf", "vllm", "hf"
    system_prompt: str = ""


class ExportResponse(BaseModel):
    """Export response."""
    format: str
    instructions: str
    model_id: str


class ExportFormatInfo(BaseModel):
    """Export format info."""
    key: str
    name: str
    description: str


class FormatListResponse(BaseModel):
    """List of available formats."""
    formats: list[ExportFormatInfo]


@router.post("/generate", response_model=ExportResponse)
async def generate_export(request: ExportRequest):
    """
    Generate export instructions.

    Supported formats:
    - ollama: Generate Modelfile for Ollama
    - gguf: Generate GGUF conversion instructions
    - vllm: Generate vLLM deployment template
    - hf: Generate HuggingFace push instructions
    """
    try:
        instructions = get_export_instructions(
            format=request.format,
            model_id=request.model_id,
            system_prompt=request.system_prompt,
        )

        return ExportResponse(
            format=request.format,
            instructions=instructions,
            model_id=request.model_id,
        )

    except Exception as e:
        logger.error(f"Export generation error: {e}")
        raise HTTPException(status_code=500, detail="Export generation failed")


@router.post("/ollama-modelfile", response_model=ExportResponse)
async def generate_modelfile(request: ExportRequest):
    """Generate Ollama Modelfile specifically."""
    try:
        modelfile = generate_ollama_modelfile(
            model_id=request.model_id,
            system_prompt=request.system_prompt or "You are a helpful AI assistant.",
        )

        return ExportResponse(
            format="ollama",
            instructions=modelfile,
            model_id=request.model_id,
        )

    except Exception as e:
        logger.error(f"Modelfile generation error: {e}")
        raise HTTPException(status_code=500, detail="Modelfile generation failed")


@router.get("/formats", response_model=FormatListResponse)
async def list_formats():
    """List all available export formats."""
    formats = list_export_formats()

    return FormatListResponse(
        formats=[
            ExportFormatInfo(key=key, name=info["name"], description=info["description"])
            for key, info in formats.items()
        ]
    )
