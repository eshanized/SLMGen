#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparison Engine.

Provides side-by-side model comparison with metrics.
Reuses risk.py and confidence.py for output analysis.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from dataclasses import dataclass, field
from typing import Optional

from .engine import InferenceEngine, GenerationResult, InferenceConfig

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetrics:
    """Metrics comparing two model outputs."""
    base_latency_ms: float
    tuned_latency_ms: float
    latency_delta_ms: float
    base_tokens: int
    tuned_tokens: int
    token_delta: int
    similarity_score: float  # 0-1, higher is more similar
    base_risk_score: float  # From risk.py
    tuned_risk_score: float
    base_risk_level: str
    tuned_risk_level: str
    quality_score: float  # From confidence.py


@dataclass
class ComparisonResult:
    """Result from comparing two model outputs."""
    base_model_id: str
    tuned_model_id: Optional[str]
    base_output: str
    tuned_output: str
    base_result: GenerationResult
    tuned_result: GenerationResult
    metrics: ComparisonMetrics
    error: Optional[str] = None


def _compute_text_similarity(text1: str, text2: str) -> float:
    """
    Compute simple similarity score between two texts.
    
    Uses Jaccard similarity on n-grams (bigrams).
    Returns 0-1 where 1 is identical.
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    
    # Normalize
    t1 = text1.lower().split()
    t2 = text2.lower().split()
    
    if not t1 or not t2:
        return 0.0
    
    # Bigrams
    def bigrams(words):
        return set(tuple(words[i:i+2]) for i in range(len(words)-1))
    
    bg1 = bigrams(t1)
    bg2 = bigrams(t2)
    
    if not bg1 and not bg2:
        return 1.0
    
    intersection = len(bg1 & bg2)
    union = len(bg1 | bg2)
    
    return intersection / union if union > 0 else 0.0


def _compute_risk_score(text: str) -> tuple[float, str]:
    """
    Compute risk score for a single text.
    
    Simplified from risk.py for single-output analysis.
    """
    import re
    
    ABSTRACT_MARKERS = {
        "probably", "possibly", "might", "could", "perhaps",
        "seemingly", "apparently", "presumably", "supposedly",
        "essentially", "basically", "generally", "typically", "usually"
    }
    
    GROUNDING_MARKERS = {
        "according to", "based on", "research shows", "data suggests",
        "evidence shows", "verified", "confirmed", "established"
    }
    
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)
    total_words = len(words)
    
    if total_words == 0:
        return 0.5, "medium"
    
    # Abstract density
    abstract_count = sum(1 for m in ABSTRACT_MARKERS if m in text_lower)
    abstract_density = (abstract_count / total_words) * 100
    
    # Grounding markers
    grounding_count = sum(1 for m in GROUNDING_MARKERS if m in text_lower)
    
    # Numbers (concrete)
    numbers = len(re.findall(r"\b\d+\b", text_lower))
    
    # Score components
    abstract_score = min(1.0, abstract_density / 5) * 0.4
    grounding_score = min(1.0, (grounding_count + numbers / 10) / 3) * 0.3
    
    overall = min(1.0, abstract_score + grounding_score + 0.3)
    
    if overall < 0.35:
        level = "low"
    elif overall < 0.6:
        level = "medium"
    else:
        level = "high"
    
    return round(overall, 2), level


def _compute_quality_score(text: str) -> float:
    """
    Compute quality score for text.
    
    Factors:
    - Length (not too short, not too long)
    - Coherence (sentence count)
    - Content (not empty)
    """
    if not text or len(text.strip()) < 10:
        return 0.0
    
    words = len(text.split())
    sentences = len(text.replace("!", ".").replace("?", ".").split("."))
    
    # Length score (optimal 50-500 words)
    length_score = 1.0 if 50 <= words <= 500 else max(0, 1 - abs(words - 275) / 275)
    
    # Coherence score
    coherence_score = min(1.0, sentences / 5) if sentences > 0 else 0.5
    
    # Content score (not too repetitive)
    word_set = set(text.lower().split())
    vocabulary_score = len(word_set) / max(len(text.split()), 1)
    
    return round((length_score * 0.4 + coherence_score * 0.3 + vocabulary_score * 0.3), 2)


class ComparisonEngine:
    """
    Engine for comparing model outputs.
    
    Provides:
    - Side-by-side comparison
    - Latency metrics
    - Similarity scoring
    - Risk and quality analysis
    
    Usage:
        engine = ComparisonEngine(inference_engine)
        
        result = await engine.compare(
            base_model="model1",
            tuned_model="model2",
            prompt="Hello!",
            system_prompt="You are helpful.",
        )
    """
    
    def __init__(self, inference_engine: InferenceEngine):
        """
        Initialize comparison engine.
        
        Args:
            inference_engine: InferenceEngine instance for making calls
        """
        self._inference = inference_engine
    
    async def compare(
        self,
        base_model: str,
        tuned_model: Optional[str],
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None,
    ) -> ComparisonResult:
        """
        Compare outputs from base and tuned models.
        
        Args:
            base_model: Base model ID
            tuned_model: Tuned/fine-tuned model ID (optional)
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration
            
        Returns:
            ComparisonResult with outputs and metrics
        """
        import asyncio
        
        # Generate from both models in parallel
        if tuned_model:
            results = await self._inference.generate_parallel(
                model_ids=[base_model, tuned_model],
                prompt=prompt,
                system_prompt=system_prompt,
                config=config,
            )
            
            if len(results) >= 2:
                base_result = results[0]
                tuned_result = results[1]
            else:
                base_result = results[0]
                tuned_result = GenerationResult(
                    model_id=tuned_model,
                    output="",
                    latency_ms=0,
                    tokens=0,
                    finish_reason="error",
                    error="Failed to get result",
                )
        else:
            # Only base model
            base_result = await self._inference.generate(
                model_id=base_model,
                prompt=prompt,
                system_prompt=system_prompt,
                config=config,
            )
            tuned_result = GenerationResult(
                model_id="",
                output="",
                latency_ms=0,
                tokens=0,
                finish_reason="skipped",
            )
        
        # Compute metrics
        metrics = self._compute_metrics(base_result, tuned_result)
        
        return ComparisonResult(
            base_model_id=base_model,
            tuned_model_id=tuned_model,
            base_output=base_result.output,
            tuned_output=tuned_result.output,
            base_result=base_result,
            tuned_result=tuned_result,
            metrics=metrics,
        )
    
    def _compute_metrics(
        self,
        base_result: GenerationResult,
        tuned_result: GenerationResult,
    ) -> ComparisonMetrics:
        """Compute comparison metrics."""
        import asyncio
        
        # Latency comparison
        latency_delta = tuned_result.latency_ms - base_result.latency_ms
        
        # Token comparison
        token_delta = tuned_result.tokens - base_result.tokens
        
        # Similarity
        similarity = _compute_text_similarity(
            base_result.output,
            tuned_result.output,
        )
        
        # Risk scores
        base_risk, base_level = _compute_risk_score(base_result.output)
        tuned_risk, tuned_level = _compute_risk_score(tuned_result.output)
        
        # Quality scores
        base_quality = _compute_quality_score(base_result.output)
        tuned_quality = _compute_quality_score(tuned_result.output)
        
        # Combined quality (average if both exist)
        quality_score = (base_quality + tuned_quality) / 2
        
        return ComparisonMetrics(
            base_latency_ms=base_result.latency_ms,
            tuned_latency_ms=tuned_result.latency_ms,
            latency_delta_ms=round(latency_delta, 1),
            base_tokens=base_result.tokens,
            tuned_tokens=tuned_result.tokens,
            token_delta=token_delta,
            similarity_score=round(similarity, 3),
            base_risk_score=base_risk,
            tuned_risk_score=tuned_risk,
            base_risk_level=base_level,
            tuned_risk_level=tuned_level,
            quality_score=quality_score,
        )
    
    async def quick_compare(
        self,
        model1: str,
        model2: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        Quick comparison returning minimal data.
        
        Useful for rapid iteration.
        """
        result = await self.compare(
            base_model=model1,
            tuned_model=model2,
            prompt=prompt,
            system_prompt=system_prompt,
        )
        
        return {
            "model1_output": result.base_output,
            "model2_output": result.tuned_output,
            "latency_diff_ms": result.metrics.latency_delta_ms,
            "similarity": result.metrics.similarity_score,
        }


# Global comparison engine
_comparison_engine: Optional[ComparisonEngine] = None


def get_comparison_engine() -> ComparisonEngine:
    """Get or create the global comparison engine."""
    global _comparison_engine
    if _comparison_engine is None:
        from .engine import get_inference_engine
        _comparison_engine = ComparisonEngine(get_inference_engine())
    return _comparison_engine
