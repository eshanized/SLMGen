#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Confidence Score.

Measures how much we can trust this dataset for training.
Higher confidence = more reliable fine-tuning results.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import hashlib
import logging
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class DatasetConfidence:
    """Confidence assessment for training reliability."""
    score: float  # 0.0 - 1.0
    level: str  # "low", "medium", "high"
    coverage: float  # Topic breadth
    redundancy: float  # Repetition penalty (0 = no dupes, 1 = all dupes)
    diversity: float  # Response variation
    explanation: str


def _hash_content(text: str) -> str:
    """Create hash for deduplication."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()[:16]


def _measure_coverage(data: list[dict]) -> tuple[float, str]:
    """
    Estimate topic coverage based on vocabulary breadth.
    Returns (score 0-1, note).
    """
    all_text = []
    for entry in data:
        for msg in entry.get("messages", []):
            all_text.append(msg.get("content", ""))
    
    combined = " ".join(all_text).lower()
    words = re.findall(r"\b[a-z]{4,}\b", combined)  # words with 4+ chars
    
    unique_words = len(set(words))
    total_words = len(words)
    
    if total_words == 0:
        return 0.3, "No text content found"
    
    # Vocabulary richness
    richness = unique_words / (total_words ** 0.5)  # Heap's law approximation
    
    # Normalize to 0-1
    coverage = min(1.0, richness / 50)  # 50 is a good threshold
    
    if coverage > 0.7:
        return coverage, "Excellent vocabulary coverage"
    elif coverage > 0.4:
        return coverage, "Good topic coverage"
    else:
        return coverage, "Limited vocabulary breadth"


def _measure_redundancy(data: list[dict]) -> tuple[float, str]:
    """
    Check for duplicate or near-duplicate examples.
    Returns (penalty 0-1 where 0 is best, note).
    """
    # Hash conversations for comparison
    conv_hashes = []
    for entry in data:
        msgs = entry.get("messages", [])
        content = "|".join(m.get("content", "")[:100] for m in msgs)
        conv_hashes.append(_hash_content(content))
    
    # Count duplicates
    counts = Counter(conv_hashes)
    dup_count = sum(c - 1 for c in counts.values() if c > 1)
    
    redundancy = dup_count / max(len(data), 1)
    
    if redundancy > 0.2:
        return redundancy, f"High redundancy: ~{int(redundancy * 100)}% duplicates"
    elif redundancy > 0.05:
        return redundancy, "Some duplicate examples found"
    
    return redundancy, ""


def _measure_diversity(data: list[dict]) -> tuple[float, str]:
    """
    Measure response diversity - how varied are the assistant outputs?
    Returns (score 0-1, note).
    """
    responses = []
    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                responses.append(msg.get("content", ""))
    
    if len(responses) < 10:
        return 0.5, "Too few responses for diversity analysis"
    
    # Check length distribution
    lengths = [len(r) for r in responses]
    unique_lengths = len(set(lengths))
    
    # Check opening diversity (first 30 chars)
    openings = [r[:30].lower().strip() for r in responses if len(r) > 30]
    unique_openings = len(set(openings)) / max(len(openings), 1)
    
    # Check ending diversity
    endings = [r[-30:].lower().strip() for r in responses if len(r) > 30]
    unique_endings = len(set(endings)) / max(len(endings), 1)
    
    # Combined diversity score
    diversity = (unique_openings + unique_endings + min(1.0, unique_lengths / 20)) / 3
    
    if diversity > 0.7:
        return diversity, "High response diversity"
    elif diversity > 0.4:
        return diversity, "Moderate response diversity"
    else:
        return diversity, "Low response diversity - responses are very similar"


def _measure_balance(data: list[dict]) -> tuple[float, str]:
    """
    Check if dataset is balanced (user/assistant ratio).
    """
    user_count = 0
    assistant_count = 0
    
    for entry in data:
        for msg in entry.get("messages", []):
            role = msg.get("role")
            if role == "user":
                user_count += 1
            elif role == "assistant":
                assistant_count += 1
    
    if user_count == 0 or assistant_count == 0:
        return 0.2, "Missing user or assistant messages"
    
    ratio = min(user_count, assistant_count) / max(user_count, assistant_count)
    
    if ratio > 0.8:
        return 1.0, ""
    elif ratio > 0.5:
        return 0.7, "Slightly imbalanced message distribution"
    else:
        return 0.4, "Imbalanced dataset - check message distribution"


def calculate_confidence(data: list[dict]) -> DatasetConfidence:
    """
    Calculate overall confidence score for the dataset.
    
    This helps users understand how reliable their fine-tuning
    results are likely to be.
    """
    logger.info(f"Calculating confidence for {len(data)} examples")
    
    if len(data) < 50:
        return DatasetConfidence(
            score=0.3,
            level="low",
            coverage=0.3,
            redundancy=0.0,
            diversity=0.5,
            explanation="Too few examples for confident training. Add at least 50 examples."
        )
    
    # Run measurements
    coverage, cov_note = _measure_coverage(data)
    redundancy, red_note = _measure_redundancy(data)
    diversity, div_note = _measure_diversity(data)
    balance, bal_note = _measure_balance(data)
    
    # Calculate overall score
    # Coverage and diversity are positive, redundancy is negative
    score = (
        coverage * 0.3 +
        (1 - redundancy) * 0.25 +
        diversity * 0.25 +
        balance * 0.2
    )
    
    # Determine level
    if score > 0.75:
        level = "high"
    elif score > 0.5:
        level = "medium"
    else:
        level = "low"
    
    # Build explanation
    notes = [n for n in [cov_note, red_note, div_note, bal_note] if n]
    if notes:
        explanation = ". ".join(notes) + "."
    else:
        explanation = "Dataset looks well-structured for training."
    
    logger.info(f"Dataset confidence: {level} ({score:.2f})")
    
    return DatasetConfidence(
        score=round(score, 2),
        level=level,
        coverage=round(coverage, 2),
        redundancy=round(redundancy, 2),
        diversity=round(diversity, 2),
        explanation=explanation,
    )
