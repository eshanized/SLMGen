#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Recommendation Engine.

Picks the best SLM for your dataset based on task, deployment, and data characteristics.
Uses a scoring system with hard overrides for special cases.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from dataclasses import dataclass

from app.models import (
    TaskType,
    DeploymentTarget,
    DatasetStats,
    DatasetCharacteristics,
    ModelRecommendation,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelSpec:
    """Internal model Specification."""
    key: str
    model_id: str
    name: str
    size: str
    context_window: int
    is_gated: bool
    strengths: list[str]
    good_for_tasks: list[TaskType]
    good_for_deploy: list[DeploymentTarget]
    min_examples: int  # recommended minimum


# Supported Models for fine-tuning (V3.0.0)
MODELS: dict[str, ModelSpec] = {
    # === NEW 2026 Models ===
    "qwen35": ModelSpec(
        key="qwen35",
        model_id="Qwen/Qwen3.5-32B-Instruct",
        name="Qwen 3.5 32B",
        size="32B",
        context_window=64000,
        is_gated=False,
        strengths=["Hybrid thinking", "Code generation", "Math reasoning", "64K context"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION, TaskType.EXTRACTION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER],
        min_examples=300,
    ),
    "llama33": ModelSpec(
        key="llama33",
        model_id="meta-llama/Llama-3.3-8B-Instruct",
        name="Llama 3.3 8B",
        size="8B",
        context_window=128000,
        is_gated=True,
        strengths=["128K context", "General purpose", "Top-tier quality"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=200,
    ),
    "llama33_70b": ModelSpec(
        key="llama33_70b",
        model_id="meta-llama/Llama-3.3-70B-Instruct",
        name="Llama 3.3 70B",
        size="70B",
        context_window=128000,
        is_gated=True,
        strengths=["SOTA quality", "128K context", "Complex reasoning"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER],
        min_examples=500,
    ),
    "deepseek_v3": ModelSpec(
        key="deepseek_v3",
        model_id="deepseek-ai/DeepSeek-V3",
        name="DeepSeek V3",
        size="84B",
        context_window=64000,
        is_gated=False,
        strengths=["MoE architecture", "Open weights", "64K context"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER],
        min_examples=500,
    ),
    "smollm3": ModelSpec(
        key="smollm3",
        model_id="HuggingFaceTB/SmolLM3-3B-Instruct",
        name="SmolLM3 3B",
        size="3B",
        context_window=128000,
        is_gated=False,
        strengths=["128K context", "Multilingual (6 languages)", "Advanced reasoning"],
        good_for_tasks=[TaskType.QA, TaskType.EXTRACTION, TaskType.GENERATION, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP, DeploymentTarget.EDGE],
        min_examples=100,
    ),
    "mistral_small": ModelSpec(
        key="mistral_small",
        model_id="mistralai/Mistral-Small-24B-Instruct-2501",
        name="Mistral Small 3",
        size="24B",
        context_window=131072,
        is_gated=False,
        strengths=["SOTA small model", "Code & reasoning", "128K context"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION, TaskType.EXTRACTION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER],
        min_examples=200,
    ),
    "qwen3": ModelSpec(
        key="qwen3",
        model_id="Qwen/Qwen3-4B-Instruct",
        name="Qwen 3 4B",
        size="4B",
        context_window=32768,
        is_gated=False,
        strengths=["Thinking mode", "Code generation", "Math reasoning"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION, TaskType.EXTRACTION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=100,
    ),
    "qwen25_14b": ModelSpec(
        key="qwen25_14b",
        model_id="Qwen/Qwen2.5-14B-Instruct",
        name="Qwen 2.5 14B",
        size="14B",
        context_window=32768,
        is_gated=False,
        strengths=["High quality", "Complex reasoning", "Code generation"],
        good_for_tasks=[TaskType.QA, TaskType.GENERATION, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER],
        min_examples=200,
    ),
    "gemma4": ModelSpec(
        key="gemma4",
        model_id="google/gemma-3-4b-it",
        name="Gemma 3 4B",
        size="4B",
        context_window=131072,
        is_gated=True,
        strengths=["Gemma 3", "Vision support", "128K context"],
        good_for_tasks=[TaskType.QA, TaskType.CONVERSATION, TaskType.GENERATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=100,
    ),
    "phi4": ModelSpec(
        key="phi4",
        model_id="microsoft/Phi-4-mini-instruct",
        name="Phi-4 Mini",
        size="3.8B",
        context_window=16384,
        is_gated=False,
        strengths=["Classification", "Extraction", "Reasoning"],
        good_for_tasks=[TaskType.CLASSIFY, TaskType.EXTRACTION, TaskType.QA],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=100,
    ),
    "llama32": ModelSpec(
        key="llama32",
        model_id="meta-llama/Llama-3.2-3B-Instruct",
        name="Llama 3.2 3B",
        size="3B",
        context_window=8192,
        is_gated=True,
        strengths=["Q&A", "Conversations", "General purpose"],
        good_for_tasks=[TaskType.QA, TaskType.CONVERSATION, TaskType.GENERATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=100,
    ),
    "gemma2": ModelSpec(
        key="gemma2",
        model_id="google/gemma-2-2b-it",
        name="Gemma 2 2B",
        size="2B",
        context_window=8192,
        is_gated=True,
        strengths=["Edge deployment", "Small footprint", "Fast inference"],
        good_for_tasks=[TaskType.CLASSIFY, TaskType.QA, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.EDGE, DeploymentTarget.MOBILE, DeploymentTarget.BROWSER],
        min_examples=50,
    ),
    "qwen25": ModelSpec(
        key="qwen25",
        model_id="Qwen/Qwen2.5-3B-Instruct",
        name="Qwen 2.5 3B",
        size="3B",
        context_window=32768,
        is_gated=False,
        strengths=["Multilingual", "JSON/structured output", "Long context"],
        good_for_tasks=[TaskType.EXTRACTION, TaskType.GENERATION, TaskType.QA],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=100,
    ),
    "mistral7b": ModelSpec(
        key="mistral7b",
        model_id="mistralai/Mistral-7B-Instruct-v0.3",
        name="Mistral 7B",
        size="7B",
        context_window=32768,
        is_gated=False,
        strengths=["Generation", "Creative writing", "Complex reasoning"],
        good_for_tasks=[TaskType.GENERATION, TaskType.CONVERSATION, TaskType.QA],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER],
        min_examples=200,
    ),
    "smollm2": ModelSpec(
        key="smollm2",
        model_id="HuggingFaceTB/SmolLM2-1.7B-Instruct",
        name="SmolLM2 1.7B",
        size="1.7B",
        context_window=8192,
        is_gated=False,
        strengths=["Ultra compact", "Edge inference", "Low memory"],
        good_for_tasks=[TaskType.CLASSIFY, TaskType.QA, TaskType.EXTRACTION],
        good_for_deploy=[DeploymentTarget.EDGE, DeploymentTarget.MOBILE, DeploymentTarget.BROWSER],
        min_examples=50,
    ),
    "llama32_1b": ModelSpec(
        key="llama32_1b",
        model_id="meta-llama/Llama-3.2-1B-Instruct",
        name="Llama 3.2 1B",
        size="1B",
        context_window=8192,
        is_gated=True,
        strengths=["Smallest Llama", "Mobile-first", "Fast inference"],
        good_for_tasks=[TaskType.CLASSIFY, TaskType.QA, TaskType.CONVERSATION],
        good_for_deploy=[DeploymentTarget.MOBILE, DeploymentTarget.EDGE, DeploymentTarget.BROWSER],
        min_examples=50,
    ),
    "deepseek_coder": ModelSpec(
        key="deepseek_coder",
        model_id="deepseek-ai/deepseek-coder-1.3b-instruct",
        name="DeepSeek Coder 1.3B",
        size="1.3B",
        context_window=16384,
        is_gated=False,
        strengths=["Code generation", "Technical docs", "Structured output"],
        good_for_tasks=[TaskType.EXTRACTION, TaskType.GENERATION, TaskType.QA],
        good_for_deploy=[DeploymentTarget.DESKTOP, DeploymentTarget.SERVER, DeploymentTarget.EDGE],
        min_examples=100,
    ),
    "phi35": ModelSpec(
        key="phi35",
        model_id="microsoft/Phi-3.5-mini-instruct",
        name="Phi-3.5 Mini",
        size="3.8B",
        context_window=128000,
        is_gated=False,
        strengths=["128K context", "Reasoning", "Long documents"],
        good_for_tasks=[TaskType.QA, TaskType.EXTRACTION, TaskType.GENERATION],
        good_for_deploy=[DeploymentTarget.CLOUD, DeploymentTarget.SERVER, DeploymentTarget.DESKTOP],
        min_examples=100,
    ),
}


def _score_task_fit(model: ModelSpec, task: TaskType) -> int:
    """Score model's fit for the Task (0-50 points)."""
    if task in model.good_for_tasks:
        idx = model.good_for_tasks.index(task)
        # First match = 50pts, second = 40pts, etc.
        return max(30, 50 - (idx * 10))
    return 15  # baseline if not explicitly Listed


def _score_deployment_fit(model: ModelSpec, deploy: DeploymentTarget) -> int:
    """Score model's fit for deployment Target (0-30 points)."""
    if deploy in model.good_for_deploy:
        return 30
    
    # Smaller models get partial credit for edge/mobile
    if deploy in [DeploymentTarget.EDGE, DeploymentTarget.MOBILE, DeploymentTarget.BROWSER]:
        if model.size in ["2B", "3B", "3.8B"]:
            return 20
        return 5  # big models not great for Edge
    
    return 15  # neutral


def _score_data_fit(model: ModelSpec, stats: DatasetStats, chars: DatasetCharacteristics) -> int:
    """Score based on dataset characteristics (0-20 points)."""
    score = 10  # baseline
    
    # Multilingual data → Qwen preferred (including Qwen 3)
    if chars.is_multilingual and model.key in ["qwen25", "qwen3"]:
        score += 10
    
    # JSON output → Qwen or Phi
    if chars.looks_like_json and model.key in ["qwen25", "qwen3", "phi4"]:
        score += 5
    
    # Multi-turn → Llama or conversation-focused
    if chars.is_multi_turn and TaskType.CONVERSATION in model.good_for_tasks:
        score += 5
    
    # Dataset size vs model minimum
    if stats.total_examples >= model.min_examples * 2:
        score += 5
    elif stats.total_examples < model.min_examples:
        score -= 5
    
    return max(0, min(20, score))


def _apply_bonuses(model: ModelSpec, stats: DatasetStats, chars: DatasetCharacteristics) -> int:
    """Apply bonus points for special Cases."""
    bonus = 0
    
    # Multi-turn Bonus
    if chars.is_multi_turn:
        bonus += 10
    
    # Long context utilization
    if stats.avg_tokens_per_example > 2000 and model.context_window >= 16384:
        bonus += 5
    
    return bonus


def _get_reasons(
    model: ModelSpec,
    task: TaskType,
    deploy: DeploymentTarget,
    chars: DatasetCharacteristics
) -> list[str]:
    """Generate human-readable reasons for Recommendation."""
    reasons = []
    
    # Task fit Reason
    if task in model.good_for_tasks:
        reasons.append(f"✅ Excellent for {task.value} tasks")
    
    # Deployment reason
    if deploy in model.good_for_deploy:
        reasons.append(f"✅ Great for {deploy.value} deployment")
    
    # Special Strengths (V2.0.0)
    if chars.is_multilingual and model.key in ["qwen25", "qwen3"]:
        reasons.append("✅ Best choice for multilingual data")
    
    if chars.looks_like_json and model.key in ["qwen25", "qwen3", "phi4"]:
        reasons.append("✅ Excels at structured JSON output")
    
    if deploy in [DeploymentTarget.EDGE, DeploymentTarget.MOBILE]:
        if model.size == "2B":
            reasons.append("✅ Compact size perfect for edge devices")
    
    # Add general Strengths
    for strength in model.strengths[:2]:
        if strength not in str(reasons):
            reasons.append(f"💪 {strength}")
    
    return reasons[:4]  # max 4 Reasons


def get_recommendations(
    task: TaskType,
    deployment: DeploymentTarget,
    stats: DatasetStats,
    characteristics: DatasetCharacteristics,
) -> RecommendationResponse:
    """
    Get model recommendations based on task, deployment, and data.
    
    Scoring breakdown (100 points Max):
    - Task fit: 50 pts
    - Deployment fit: 30 pts
    - Data characteristics: 20 pts
    - Bonuses: +10 pts possible
    """
    logger.info(f"Getting recommendations for task={task.value}, deploy={deployment.value}")
    
    scores: list[tuple[str, int, ModelSpec]] = []
    
    for key, model in MODELS.items():
        # Calculate Scores
        task_score = _score_task_fit(model, task)
        deploy_score = _score_deployment_fit(model, deployment)
        data_score = _score_data_fit(model, stats, characteristics)
        bonus = _apply_bonuses(model, stats, characteristics)
        
        total = task_score + deploy_score + data_score + bonus
        total = min(100, total)  # cap at 100
        
        scores.append((key, total, model))
        logger.debug(f"  {key}: task={task_score}, deploy={deploy_score}, "
                     f"data={data_score}, bonus={bonus}, total={total}")
    
    # Hard overrides for special Cases
    # Multilingual data → Qwen always wins
    if characteristics.is_multilingual:
        for i, (key, score, model) in enumerate(scores):
            if key == "qwen25":
                scores[i] = (key, min(100, score + 20), model)
                logger.info("Applied multilingual override for Qwen")
    
    # Edge deployment → Gemma preferred
    if deployment in [DeploymentTarget.EDGE, DeploymentTarget.MOBILE, DeploymentTarget.BROWSER]:
        for i, (key, score, model) in enumerate(scores):
            if key == "gemma2":
                scores[i] = (key, min(100, score + 15), model)
                logger.info("Applied edge override for Gemma")
    
    # Sort by Score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Build Response
    recommendations = []
    for key, score, model in scores:
        rec = ModelRecommendation(
            model_id=model.model_id,
            model_name=model.name,
            size=model.size,
            score=float(score),
            reasons=_get_reasons(model, task, deployment, characteristics),
            context_window=model.context_window,
            is_gated=model.is_gated,
        )
        recommendations.append(rec)
    
    primary = recommendations[0]
    alternatives = recommendations[1:4]  # top 3 alternatives
    
    logger.info(f"Recommending {primary.model_name} with score {primary.score}")
    
    return RecommendationResponse(
        primary=primary,
        alternatives=alternatives,
    )
