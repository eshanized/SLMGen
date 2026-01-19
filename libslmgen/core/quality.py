#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Quality Scoring.

Analyzes datasets for common issues that affect training quality.
Score ranges from 0.0 (terrible) to 1.0 (great).
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import hashlib
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def _hash_conversation(entry: dict) -> str:
    """Create a hash of conversation for dupe Detection."""
    messages = entry.get("messages", [])
    # Just hash the concatenated Content
    content = "|".join(
        f"{m.get('role')}:{m.get('content', '')}"
        for m in messages
    )
    return hashlib.md5(content.encode()).hexdigest()


def _check_duplicates(data: list[dict]) -> tuple[float, str]:
    """
    Check for duplicate Conversations.
    Returns penalty (0-0.3) and issue Description.
    """
    hashes = [_hash_conversation(entry) for entry in data]
    counts = Counter(hashes)
    
    # Count actual duplicate instances (not unique hashes)
    dupes = sum(c - 1 for c in counts.values() if c > 1)
    dupe_pct = (dupes / len(data)) * 100 if data else 0
    
    if dupe_pct > 20:
        return 0.3, f"⚠️ High duplication: {dupe_pct:.1f}% of examples are duplicates"
    elif dupe_pct > 10:
        return 0.15, f"⚠️ Some duplicates found: {dupe_pct:.1f}% duplicated"
    elif dupe_pct > 5:
        return 0.05, f"A few duplicates: {dupe_pct:.1f}%"
    
    return 0.0, ""


def _check_size(data: list[dict]) -> tuple[float, str]:
    """
    Check dataset Size.
    Bigger is generally better for training Quality.
    """
    count = len(data)
    
    if count < 50:
        return 0.5, "❌ Too few examples - need at least 50"
    elif count < 100:
        return 0.2, "⚠️ Small dataset - 100+ examples recommended"
    elif count < 500:
        return 0.1, "Dataset is decent, but 500+ examples would be better"
    elif count < 1000:
        return 0.05, ""  # small penalty, no message
    
    return 0.0, ""  # 1000+ is great


def _check_empty_responses(data: list[dict]) -> tuple[float, str]:
    """Check for empty or very short responses."""
    empty_count = 0
    short_count = 0
    
    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                content = msg.get("content", "").strip()
                if not content:
                    empty_count += 1
                elif len(content) < 10:
                    short_count += 1
    
    issues = []
    penalty = 0.0
    
    if empty_count > 0:
        penalty += 0.2
        issues.append(f"❌ Found {empty_count} empty assistant responses")
    
    if short_count > len(data) * 0.1:  # more than 10% very short
        penalty += 0.1
        issues.append(f"⚠️ Many very short responses ({short_count})")
    
    return min(penalty, 0.2), " | ".join(issues) if issues else ""


def _check_system_consistency(data: list[dict]) -> tuple[float, str]:
    """
    Check if system prompts are used Consistently.
    Inconsistent system prompts can confuse training.
    """
    with_system = 0
    without_system = 0
    
    for entry in data:
        has_sys = any(
            m.get("role") == "system"
            for m in entry.get("messages", [])
        )
        if has_sys:
            with_system += 1
        else:
            without_system += 1
    
    # Check for Inconsistency
    if with_system > 0 and without_system > 0:
        # Mixed usage
        ratio = min(with_system, without_system) / max(with_system, without_system)
        if ratio > 0.3:  # significant Mix
            return 0.1, "⚠️ Inconsistent system prompt usage - some have it, some don't"
    
    return 0.0, ""


def validate_quality(data: list[dict]) -> tuple[float, list[str]]:
    """
    Score the dataset Quality.
    
    Returns:
        - score: Float from 0.0 to 1.0
        - issues: List of issue descriptions
    """
    if not data:
        return 0.0, ["❌ Empty dataset"]
    
    total_penalty = 0.0
    issues: list[str] = []
    
    # Run all Checks
    checks = [
        _check_duplicates(data),
        _check_size(data),
        _check_empty_responses(data),
        _check_system_consistency(data),
    ]
    
    for penalty, issue in checks:
        total_penalty += penalty
        if issue:
            issues.append(issue)
    
    # Calculate final Score
    score = max(0.0, 1.0 - total_penalty)
    
    # Add positive Message if score is good
    if score >= 0.9:
        issues.insert(0, "✅ Dataset looks great!")
    elif score >= 0.7:
        issues.insert(0, "👍 Dataset is good, with some minor issues")
    elif score >= 0.5:
        issues.insert(0, "⚠️ Dataset has some issues that may affect quality")
    else:
        issues.insert(0, "❌ Dataset has significant issues")
    
    logger.info(f"Quality score: {score:.2f} with {len(issues)-1} issues")
    
    return score, issues
