#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Personality Detection.

Infers behavioral traits from dataset patterns to help users understand
what kind of assistant their data will produce.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import logging
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

# Vocabulary markers for tone detection
FORMAL_MARKERS = {
    "therefore", "consequently", "furthermore", "moreover", "however",
    "nevertheless", "whereas", "accordingly", "subsequently", "thus",
    "hereby", "henceforth", "notwithstanding", "pursuant", "regarding"
}

CASUAL_MARKERS = {
    "hey", "cool", "awesome", "gonna", "wanna", "kinda", "sorta", "yeah",
    "nope", "ok", "okay", "sure", "yep", "btw", "lol", "haha", "omg"
}

# Technical jargon patterns
TECHNICAL_PATTERNS = [
    r"\b(api|sdk|cli|gui|http|tcp|udp|sql|nosql|orm|mvc|crud)\b",
    r"\b(algorithm|function|variable|parameter|argument|instance)\b",
    r"\b(deploy|compile|debug|refactor|optimize|integrate|implement)\b",
    r"\b(tensor|gradient|epoch|batch|layer|neural|vector|matrix)\b",
    r"\b(kubernetes|docker|aws|gcp|azure|terraform|ansible)\b",
]


@dataclass
class DatasetPersonality:
    """Behavioral profile inferred from dataset patterns."""
    tone: str  # "formal", "casual", "neutral"
    verbosity: str  # "concise", "moderate", "verbose"
    technicality: str  # "layman", "intermediate", "expert"
    strictness: str  # "flexible", "moderate", "strict"
    confidence: float  # 0.0 - 1.0 (how confident we are in this assessment)
    summary: str  # Human-readable description


def _collect_responses(data: list[dict]) -> list[str]:
    """Extract all assistant responses from dataset."""
    responses = []
    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                content = msg.get("content", "").strip()
                if content:
                    responses.append(content)
    return responses


def _analyze_tone(responses: list[str]) -> tuple[str, float]:
    """
    Detect formal vs casual tone.
    Returns (tone, confidence).
    """
    all_text = " ".join(responses).lower()
    words = set(re.findall(r"\b\w+\b", all_text))
    
    formal_count = len(words & FORMAL_MARKERS)
    casual_count = len(words & CASUAL_MARKERS)
    
    # Also check sentence structure
    # Formal text tends to have longer sentences
    sentences = re.split(r"[.!?]+", all_text)
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    
    # Scoring
    formal_score = formal_count * 2 + (1 if avg_sentence_len > 15 else 0)
    casual_score = casual_count * 2 + (1 if avg_sentence_len < 10 else 0)
    
    if formal_score > casual_score + 2:
        return "formal", min(0.9, 0.5 + formal_score * 0.1)
    elif casual_score > formal_score + 2:
        return "casual", min(0.9, 0.5 + casual_score * 0.1)
    
    return "neutral", 0.6


def _analyze_verbosity(responses: list[str]) -> tuple[str, float]:
    """
    Measure response length distribution.
    Returns (verbosity, confidence).
    """
    if not responses:
        return "moderate", 0.3
    
    lengths = [len(r) for r in responses]
    avg_len = sum(lengths) / len(lengths)
    
    # Thresholds based on character count
    if avg_len < 150:
        return "concise", 0.8
    elif avg_len < 500:
        return "moderate", 0.7
    else:
        return "verbose", 0.8


def _analyze_technicality(responses: list[str]) -> tuple[str, float]:
    """
    Detect technical jargon density.
    Returns (technicality, confidence).
    """
    all_text = " ".join(responses).lower()
    total_words = len(re.findall(r"\b\w+\b", all_text))
    
    if total_words == 0:
        return "layman", 0.3
    
    # Count technical terms
    tech_count = 0
    for pattern in TECHNICAL_PATTERNS:
        tech_count += len(re.findall(pattern, all_text, re.IGNORECASE))
    
    # Calculate density
    tech_density = tech_count / (total_words / 100)  # per 100 words
    
    if tech_density > 3:
        return "expert", 0.85
    elif tech_density > 1:
        return "intermediate", 0.75
    else:
        return "layman", 0.7


def _analyze_strictness(responses: list[str]) -> tuple[str, float]:
    """
    Measure response consistency/strictness.
    High variance = flexible, low variance = strict.
    """
    if len(responses) < 10:
        return "moderate", 0.4  # not enough data
    
    lengths = [len(r) for r in responses]
    avg_len = sum(lengths) / len(lengths)
    
    # Calculate variance
    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
    coef_of_var = std_dev / avg_len if avg_len > 0 else 0
    
    # Also check for templated responses (indicates strictness)
    # Look for common prefixes
    if len(responses) > 20:
        prefixes = [r[:50] for r in responses if len(r) > 50]
        prefix_counts = Counter(prefixes)
        most_common = prefix_counts.most_common(1)
        if most_common and most_common[0][1] > len(responses) * 0.1:
            return "strict", 0.8  # many similar openings
    
    if coef_of_var < 0.3:
        return "strict", 0.75
    elif coef_of_var < 0.6:
        return "moderate", 0.7
    else:
        return "flexible", 0.75


def _generate_summary(
    tone: str,
    verbosity: str,
    technicality: str,
    strictness: str
) -> str:
    """Generate a human-readable personality summary."""
    templates = {
        ("formal", "expert"): "a professional technical specialist who communicates precisely",
        ("formal", "intermediate"): "a knowledgeable professional who explains things clearly",
        ("formal", "layman"): "a polite assistant who keeps things simple",
        ("casual", "expert"): "a friendly tech expert who makes complex topics approachable",
        ("casual", "intermediate"): "a helpful buddy who knows their stuff",
        ("casual", "layman"): "a casual conversationalist who keeps it simple",
        ("neutral", "expert"): "a balanced technical assistant",
        ("neutral", "intermediate"): "a helpful all-rounder",
        ("neutral", "layman"): "a straightforward helper",
    }
    
    base = templates.get((tone, technicality), "a capable assistant")
    
    # Add verbosity note
    if verbosity == "concise":
        base += " who gets straight to the point"
    elif verbosity == "verbose":
        base += " who provides thorough explanations"
    
    # Add strictness note
    if strictness == "strict":
        base += " with consistent, predictable responses"
    elif strictness == "flexible":
        base += " who adapts to different questions"
    
    return f"Your dataset behaves like {base}."


def detect_personality(data: list[dict]) -> DatasetPersonality:
    """
    Analyze dataset and infer behavioral personality.
    
    This helps users understand what kind of assistant they're training,
    before they even start the training process.
    """
    logger.info(f"Detecting personality from {len(data)} examples")
    
    responses = _collect_responses(data)
    
    if len(responses) < 20:
        # Not enough data for reliable analysis
        logger.warning("Too few responses for reliable personality detection")
        return DatasetPersonality(
            tone="neutral",
            verbosity="moderate",
            technicality="intermediate",
            strictness="moderate",
            confidence=0.3,
            summary="Not enough data for reliable personality analysis. "
                    "Consider adding more examples for a better assessment."
        )
    
    # Run all analyses
    tone, tone_conf = _analyze_tone(responses)
    verbosity, verb_conf = _analyze_verbosity(responses)
    technicality, tech_conf = _analyze_technicality(responses)
    strictness, strict_conf = _analyze_strictness(responses)
    
    # Overall confidence is the average
    overall_conf = (tone_conf + verb_conf + tech_conf + strict_conf) / 4
    
    # Generate summary
    summary = _generate_summary(tone, verbosity, technicality, strictness)
    
    logger.info(f"Personality detected: {tone}/{verbosity}/{technicality}/{strictness} "
                f"(confidence: {overall_conf:.2f})")
    
    return DatasetPersonality(
        tone=tone,
        verbosity=verbosity,
        technicality=technicality,
        strictness=strictness,
        confidence=overall_conf,
        summary=summary,
    )
