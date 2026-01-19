#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Features Router.

Exposes all advanced intelligence features via new API endpoints.
These are additive to the core upload → analyze → recommend → generate flow.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.session import session_manager
from core import (
    detect_personality,
    estimate_hallucination_risk,
    calculate_confidence,
    compose_behavior,
    BehaviorConfig,
    lint_prompt,
    generate_failure_previews,
    generate_model_card,
    compare_prompts,
)
from core.recommender import MODELS

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class PersonalityResponse(BaseModel):
    tone: str
    verbosity: str
    technicality: str
    strictness: str
    confidence: float
    summary: str


class RiskResponse(BaseModel):
    score: float
    level: str
    factors: list[str]
    recommendation: str


class ConfidenceResponse(BaseModel):
    score: float
    level: str
    coverage: float
    redundancy: float
    diversity: float
    explanation: str


class BehaviorRequest(BaseModel):
    tone: int = 50
    depth: int = 50
    risk_tolerance: int = 30
    creativity: int = 50


class BehaviorResponse(BaseModel):
    system_prompt: str
    explanation: str
    traits_summary: str


class LintRequest(BaseModel):
    prompt: str


class LintWarning(BaseModel):
    type: str
    severity: str
    message: str
    suggestion: str


class LintResponse(BaseModel):
    score: int
    warnings: list[LintWarning]
    is_good: bool


class FailureCase(BaseModel):
    category: str
    user_prompt: str
    bad_response: str
    why_it_fails: str
    likelihood: str


class PromptDiffRequest(BaseModel):
    prompt_a: str
    prompt_b: str


class PromptChange(BaseModel):
    type: str
    description: str
    impact: str


class PromptDiffResponse(BaseModel):
    similarity: float
    changes: list[PromptChange]
    summary: str


class ModelCardResponse(BaseModel):
    title: str
    description: str
    markdown: str


class ModelDeepDiveResponse(BaseModel):
    model_id: str
    model_name: str
    size: str
    context_window: int
    is_gated: bool
    strengths: list[str]
    good_for_tasks: list[str]
    good_for_deploy: list[str]
    min_examples: int


# ============================================
# ENDPOINTS
# ============================================

@router.get("/personality/{session_id}", response_model=PersonalityResponse)
async def get_personality(session_id: str):
    """Get dataset personality analysis."""
    session = session_manager.get(session_id)
    if not session or not session.raw_data:
        raise HTTPException(status_code=404, detail="Session not found or no data")
    
    personality = detect_personality(session.raw_data)
    
    return PersonalityResponse(
        tone=personality.tone,
        verbosity=personality.verbosity,
        technicality=personality.technicality,
        strictness=personality.strictness,
        confidence=personality.confidence,
        summary=personality.summary,
    )


@router.get("/risk/{session_id}", response_model=RiskResponse)
async def get_risk(session_id: str):
    """Get hallucination risk estimate."""
    session = session_manager.get(session_id)
    if not session or not session.raw_data:
        raise HTTPException(status_code=404, detail="Session not found or no data")
    
    risk = estimate_hallucination_risk(session.raw_data)
    
    return RiskResponse(
        score=risk.score,
        level=risk.level,
        factors=risk.factors,
        recommendation=risk.recommendation,
    )


@router.get("/confidence/{session_id}", response_model=ConfidenceResponse)
async def get_confidence(session_id: str):
    """Get dataset confidence score."""
    session = session_manager.get(session_id)
    if not session or not session.raw_data:
        raise HTTPException(status_code=404, detail="Session not found or no data")
    
    conf = calculate_confidence(session.raw_data)
    
    return ConfidenceResponse(
        score=conf.score,
        level=conf.level,
        coverage=conf.coverage,
        redundancy=conf.redundancy,
        diversity=conf.diversity,
        explanation=conf.explanation,
    )


@router.post("/behavior/compose", response_model=BehaviorResponse)
async def compose_behavior_prompt(request: BehaviorRequest):
    """Generate a system prompt from trait sliders."""
    config = BehaviorConfig(
        tone=request.tone,
        depth=request.depth,
        risk_tolerance=request.risk_tolerance,
        creativity=request.creativity,
    )
    
    result = compose_behavior(config)
    
    return BehaviorResponse(
        system_prompt=result.system_prompt,
        explanation=result.explanation,
        traits_summary=result.traits_summary,
    )


@router.post("/lint-prompt", response_model=LintResponse)
async def lint_prompt_endpoint(request: LintRequest):
    """Lint a prompt for issues."""
    result = lint_prompt(request.prompt)
    
    return LintResponse(
        score=result.score,
        warnings=[
            LintWarning(
                type=w.type,
                severity=w.severity,
                message=w.message,
                suggestion=w.suggestion,
            )
            for w in result.warnings
        ],
        is_good=result.is_good,
    )


@router.get("/failure-preview/{session_id}", response_model=list[FailureCase])
async def get_failure_preview(session_id: str):
    """Get synthetic failure cases for the dataset."""
    session = session_manager.get(session_id)
    if not session or not session.raw_data:
        raise HTTPException(status_code=404, detail="Session not found or no data")
    
    cases = generate_failure_previews(session.raw_data)
    
    return [
        FailureCase(
            category=c.category,
            user_prompt=c.user_prompt,
            bad_response=c.bad_response,
            why_it_fails=c.why_it_fails,
            likelihood=c.likelihood,
        )
        for c in cases
    ]


@router.post("/prompt-diff", response_model=PromptDiffResponse)
async def diff_prompts(request: PromptDiffRequest):
    """Compare two prompts semantically."""
    result = compare_prompts(request.prompt_a, request.prompt_b)
    
    return PromptDiffResponse(
        similarity=result.similarity,
        changes=[
            PromptChange(
                type=c.type,
                description=c.description,
                impact=c.impact,
            )
            for c in result.changes
        ],
        summary=result.summary,
    )


@router.get("/model-deep-dive/{model_key}", response_model=ModelDeepDiveResponse)
async def model_deep_dive(model_key: str):
    """Get detailed model information."""
    model = MODELS.get(model_key)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_key}' not found")
    
    return ModelDeepDiveResponse(
        model_id=model.model_id,
        model_name=model.name,
        size=model.size,
        context_window=model.context_window,
        is_gated=model.is_gated,
        strengths=model.strengths,
        good_for_tasks=[t.value for t in model.good_for_tasks],
        good_for_deploy=[d.value for d in model.good_for_deploy],
        min_examples=model.min_examples,
    )


@router.get("/model-card/{session_id}", response_model=ModelCardResponse)
async def get_model_card(session_id: str):
    """Generate a model README/card."""
    session = session_manager.get(session_id)
    if not session or not session.stats:
        raise HTTPException(status_code=404, detail="Session not found or incomplete")
    
    model_id = session.selected_model_id or "unknown"
    model_name = "Custom Model"
    
    # Find model name
    for key, spec in MODELS.items():
        if spec.model_id == model_id:
            model_name = spec.name
            break
    
    task = session.task_type.value if session.task_type else "general"
    
    # Get personality if available
    personality_summary = None
    if session.raw_data:
        try:
            personality = detect_personality(session.raw_data)
            personality_summary = personality.summary
        except:
            pass
    
    card = generate_model_card(
        model_name=model_name,
        model_id=model_id,
        task_type=task,
        num_examples=session.stats.total_examples,
        quality_score=session.stats.quality_score,
        personality_summary=personality_summary,
    )
    
    return ModelCardResponse(
        title=card.title,
        description=card.description,
        markdown=card.markdown,
    )
