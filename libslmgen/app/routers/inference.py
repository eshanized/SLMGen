#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inference Router.

Provides endpoints for real-time inference and model comparison.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.inference.engine import InferenceEngine, InferenceConfig, get_inference_engine
from app.inference.comparison import ComparisonEngine, get_comparison_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inference", tags=["Inference"])

# Rate limiter for inference endpoints
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    limiter = Limiter(key_func=get_remote_address)
except ImportError:
    limiter = None


# =============================================================================
# Request/Response Models
# =============================================================================

class InferenceRequest(BaseModel):
    """Request for single model inference."""
    model_id: str = Field(..., description="HuggingFace model ID")
    prompt: str = Field(..., min_length=1, max_length=10000, description="User prompt")
    system_prompt: Optional[str] = Field(None, max_length=2000, description="Optional system prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=1, le=4096)
    do_sample: bool = Field(True)
    top_p: float = Field(0.9, ge=0.0, le=1.0)


class InferenceResponse(BaseModel):
    """Response from inference."""
    model_id: str
    output: str
    latency_ms: float
    tokens: int
    finish_reason: str
    error: Optional[str] = None


class CompareRequest(BaseModel):
    """Request for model comparison."""
    base_model_id: str = Field(..., description="Base model HuggingFace ID")
    tuned_model_id: Optional[str] = Field(None, description="Tuned model ID (optional)")
    prompt: str = Field(..., min_length=1, max_length=10000)
    system_prompt: Optional[str] = Field(None, max_length=2000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=1, le=4096)
    
    @field_validator("tuned_model_id")
    @classmethod
    def validate_models_different(cls, v, info):
        if v and v == info.data.get("base_model_id"):
            raise ValueError("tuned_model_id must be different from base_model_id")
        return v


class MetricsData(BaseModel):
    """Comparison metrics."""
    base_latency_ms: float
    tuned_latency_ms: float
    latency_delta_ms: float
    base_tokens: int
    tuned_tokens: int
    token_delta: int
    similarity_score: float
    base_risk_score: float
    tuned_risk_score: float
    base_risk_level: str
    tuned_risk_level: str
    quality_score: float


class CompareResponse(BaseModel):
    """Response from comparison."""
    base_model_id: str
    tuned_model_id: Optional[str]
    base_output: str
    tuned_output: str
    base_latency_ms: float
    tuned_latency_ms: float
    metrics: MetricsData
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """Model information."""
    model_id: str
    name: str
    size: str
    is_gated: bool
    context_window: int


class ListModelsResponse(BaseModel):
    """Response with available models."""
    models: list[ModelInfo]


# =============================================================================
# Available Models List
# =============================================================================

def _get_available_models() -> list[ModelInfo]:
    """Get list of available models for inference."""
    from core.recommender import MODELS
    
    models = []
    for key, spec in MODELS.items():
        models.append(ModelInfo(
            model_id=spec.model_id,
            name=spec.name,
            size=spec.size,
            is_gated=spec.is_gated,
            context_window=spec.context_window,
        ))
    
    return models


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/run", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    """
    Run inference on a single model.
    
    Use this to test prompts against any HuggingFace model.
    
    Note: Models may need time to load on first request (503 response).
    """
    logger.info(f"Inference request for {request.model_id}")
    
    # Build config
    config = InferenceConfig(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        do_sample=request.do_sample,
        top_p=request.top_p,
    )
    
    # Get engine and run
    engine = get_inference_engine()
    result = await engine.generate(
        model_id=request.model_id,
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        config=config,
    )
    
    return InferenceResponse(
        model_id=result.model_id,
        output=result.output,
        latency_ms=result.latency_ms,
        tokens=result.tokens,
        finish_reason=result.finish_reason,
        error=result.error,
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_models(request: CompareRequest):
    """
    Compare outputs from base and tuned models side-by-side.
    
    Runs both models in parallel for fair comparison.
    Returns outputs and metrics including:
    - Latency comparison
    - Token count difference
    - Similarity score
    - Risk analysis
    - Quality score
    """
    logger.info(f"Comparison request: {request.base_model_id} vs {request.tuned_model_id}")
    
    # Build config
    config = InferenceConfig(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    
    # Get engine and compare
    engine = get_comparison_engine()
    result = await engine.compare(
        base_model=request.base_model_id,
        tuned_model=request.tuned_model_id,
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        config=config,
    )
    
    if result.error:
        logger.warning(f"Comparison error: {result.error}")
    
    return CompareResponse(
        base_model_id=result.base_model_id,
        tuned_model_id=result.tuned_model_id,
        base_output=result.base_output,
        tuned_output=result.tuned_output,
        base_latency_ms=result.base_result.latency_ms,
        tuned_latency_ms=result.tuned_result.latency_ms,
        metrics=MetricsData(
            base_latency_ms=result.metrics.base_latency_ms,
            tuned_latency_ms=result.metrics.tuned_latency_ms,
            latency_delta_ms=result.metrics.latency_delta_ms,
            base_tokens=result.metrics.base_tokens,
            tuned_tokens=result.metrics.tuned_tokens,
            token_delta=result.metrics.token_delta,
            similarity_score=result.metrics.similarity_score,
            base_risk_score=result.metrics.base_risk_score,
            tuned_risk_score=result.metrics.tuned_risk_score,
            base_risk_level=result.metrics.base_risk_level,
            tuned_risk_level=result.metrics.tuned_risk_level,
            quality_score=result.metrics.quality_score,
        ),
        error=result.error,
    )


@router.get("/models", response_model=ListModelsResponse)
async def list_models():
    """
    Get list of models available for inference.
    
    Returns models from the SLMGEN recommendation engine.
    """
    models = _get_available_models()
    return ListModelsResponse(models=models)
