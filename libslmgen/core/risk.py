#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hallucination Risk Estimator.

Heuristic-based scoring to estimate how likely a fine-tuned model
might produce fabricated or ungrounded responses.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import logging
from dataclasses import dataclass
from statistics import stdev, mean

logger = logging.getLogger(__name__)

# Words that often precede factual claims
GROUNDING_MARKERS = {
    "according to", "based on", "research shows", "studies indicate",
    "data suggests", "evidence shows", "it is proven", "documented",
    "verified", "confirmed", "established", "measured", "recorded"
}

# Abstract/vague language that correlates with hallucination
ABSTRACT_MARKERS = {
    "probably", "possibly", "might", "could", "perhaps", "seemingly",
    "apparently", "presumably", "supposedly", "allegedly", "virtually",
    "essentially", "basically", "generally", "typically", "usually"
}


@dataclass
class HallucinationRisk:
    """Risk assessment for model hallucination."""
    score: float  # 0.0 (low risk) to 1.0 (high risk)
    level: str  # "low", "medium", "high"
    factors: list[str]  # Contributing risk factors
    recommendation: str  # What user can do about it


def _collect_responses(data: list[dict]) -> list[str]:
    """Extract all assistant responses."""
    responses = []
    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                content = msg.get("content", "").strip()
                if content:
                    responses.append(content)
    return responses


def _measure_abstraction_density(responses: list[str]) -> tuple[float, str]:
    """
    Check for vague/abstract language.
    High abstraction = higher hallucination risk.
    Returns (score 0-1, explanation).
    """
    all_text = " ".join(responses).lower()
    total_words = len(re.findall(r"\b\w+\b", all_text))
    
    if total_words == 0:
        return 0.5, ""
    
    # Count abstract markers
    abstract_count = 0
    for marker in ABSTRACT_MARKERS:
        abstract_count += all_text.count(marker)
    
    # Density per 100 words
    density = (abstract_count / total_words) * 100
    
    if density > 5:
        return 0.8, "High use of uncertain language (might, probably, etc.)"
    elif density > 2:
        return 0.5, "Moderate use of qualifying language"
    
    return 0.2, ""


def _measure_grounding(responses: list[str]) -> tuple[float, str]:
    """
    Check for references to verifiable facts.
    More grounding = lower hallucination risk.
    Returns (score 0-1 where lower is better, explanation).
    """
    all_text = " ".join(responses).lower()
    
    # Count grounding phrases
    grounding_count = 0
    for marker in GROUNDING_MARKERS:
        grounding_count += all_text.count(marker)
    
    # Check for numbers/dates (concrete claims)
    numbers = len(re.findall(r"\b\d+\b", all_text))
    
    # Normalize by response count
    total_responses = len(responses)
    grounding_per_response = (grounding_count + numbers / 10) / max(total_responses, 1)
    
    if grounding_per_response < 0.1:
        return 0.7, "Responses lack factual grounding or citations"
    elif grounding_per_response < 0.5:
        return 0.4, ""
    
    return 0.2, "Good use of factual references"


def _measure_length_variance(responses: list[str]) -> tuple[float, str]:
    """
    High variance in response lengths indicates inconsistent behavior,
    which can correlate with hallucination.
    """
    if len(responses) < 10:
        return 0.5, ""
    
    lengths = [len(r) for r in responses]
    avg_len = mean(lengths)
    
    if avg_len == 0:
        return 0.5, ""
    
    try:
        std = stdev(lengths)
        coef_of_var = std / avg_len
    except:
        return 0.5, ""
    
    if coef_of_var > 1.0:
        return 0.7, "High variance in response lengths (inconsistent behavior)"
    elif coef_of_var > 0.5:
        return 0.4, ""
    
    return 0.2, ""


def _measure_overconfidence(responses: list[str]) -> tuple[float, str]:
    """
    Detect overconfident language without backing.
    Overconfidence without grounding = higher hallucination risk.
    """
    overconfident_patterns = [
        r"\b(definitely|certainly|absolutely|without doubt|100%)\b",
        r"\b(always|never|everyone|no one|impossible)\b",
        r"\b(the best|the worst|the only|the first|the last)\b",
    ]
    
    all_text = " ".join(responses).lower()
    total_words = len(re.findall(r"\b\w+\b", all_text))
    
    if total_words == 0:
        return 0.5, ""
    
    overconf_count = 0
    for pattern in overconfident_patterns:
        overconf_count += len(re.findall(pattern, all_text))
    
    density = (overconf_count / total_words) * 100
    
    if density > 1:
        return 0.6, "Frequent use of absolute claims"
    
    return 0.2, ""


def estimate_hallucination_risk(data: list[dict]) -> HallucinationRisk:
    """
    Estimate the hallucination risk for a model trained on this dataset.
    
    Uses heuristics based on:
    - Abstraction density (vague language)
    - Grounding frequency (factual references)
    - Response length variance (behavioral consistency)
    - Overconfidence markers
    
    This is a heuristic estimate, not a guarantee.
    """
    logger.info(f"Estimating hallucination risk for {len(data)} examples")
    
    responses = _collect_responses(data)
    
    if len(responses) < 20:
        return HallucinationRisk(
            score=0.5,
            level="medium",
            factors=["Insufficient data for reliable risk assessment"],
            recommendation="Add more training examples for a more accurate estimate."
        )
    
    # Run all measurements
    factors = []
    scores = []
    
    abs_score, abs_note = _measure_abstraction_density(responses)
    scores.append(abs_score)
    if abs_note:
        factors.append(abs_note)
    
    ground_score, ground_note = _measure_grounding(responses)
    scores.append(ground_score)
    if ground_note and ground_score > 0.5:
        factors.append(ground_note)
    
    var_score, var_note = _measure_length_variance(responses)
    scores.append(var_score)
    if var_note:
        factors.append(var_note)
    
    overconf_score, overconf_note = _measure_overconfidence(responses)
    scores.append(overconf_score)
    if overconf_note:
        factors.append(overconf_note)
    
    # Calculate overall score (weighted average)
    overall = (abs_score * 0.3 + ground_score * 0.3 + var_score * 0.2 + overconf_score * 0.2)
    
    # Determine level
    if overall < 0.35:
        level = "low"
        recommendation = "Your dataset has good grounding. The model should be relatively reliable."
    elif overall < 0.6:
        level = "medium"
        recommendation = "Consider adding more factual references and reducing vague language."
    else:
        level = "high"
        recommendation = "This dataset may produce unreliable outputs. Consider adding grounded examples with citations."
    
    if not factors:
        factors = ["No significant risk factors detected"]
    
    logger.info(f"Hallucination risk: {level} ({overall:.2f})")
    
    return HallucinationRisk(
        score=round(overall, 2),
        level=level,
        factors=factors,
        recommendation=recommendation,
    )
