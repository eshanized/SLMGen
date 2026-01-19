#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Diff Tool.

Semantic comparison between two prompts.
Highlights what changed and how it might affect behavior.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import logging
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class PromptChange:
    """A single change between prompts."""
    type: str  # "added", "removed", "modified"
    description: str
    impact: str  # How this might affect behavior


@dataclass
class PromptDiff:
    """Result of comparing two prompts."""
    similarity: float  # 0.0 - 1.0
    changes: list[PromptChange]
    summary: str


def _extract_instructions(text: str) -> set[str]:
    """Extract instruction-like phrases from prompt."""
    # Look for directive patterns
    patterns = [
        r"(you (?:are|should|must|will|can)[^.!?]+)",
        r"((?:always|never|don't|do not)[^.!?]+)",
        r"((?:be|keep|make sure|ensure)[^.!?]+)",
    ]
    
    instructions = set()
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        instructions.update(matches)
    
    return instructions


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from prompt."""
    # Skip common stop words
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "to", "of",
        "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "and", "or", "but", "if", "then", "so", "than", "that", "this", "it"
    }
    
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    return set(w for w in words if w not in stop_words)


def compare_prompts(prompt_a: str, prompt_b: str) -> PromptDiff:
    """
    Compare two prompts and identify meaningful differences.
    
    Goes beyond simple text diff to understand semantic changes.
    """
    logger.info("Comparing two prompts")
    
    if not prompt_a.strip() and not prompt_b.strip():
        return PromptDiff(
            similarity=1.0,
            changes=[],
            summary="Both prompts are empty."
        )
    
    if not prompt_a.strip():
        return PromptDiff(
            similarity=0.0,
            changes=[PromptChange(
                type="added",
                description="Entirely new prompt created",
                impact="Complete behavior change"
            )],
            summary="Prompt B is entirely new."
        )
    
    if not prompt_b.strip():
        return PromptDiff(
            similarity=0.0,
            changes=[PromptChange(
                type="removed",
                description="Entire prompt removed",
                impact="Model will use default behavior"
            )],
            summary="Prompt was removed entirely."
        )
    
    # Calculate text similarity
    similarity = SequenceMatcher(None, prompt_a.lower(), prompt_b.lower()).ratio()
    
    changes = []
    
    # Compare instructions
    instructions_a = _extract_instructions(prompt_a)
    instructions_b = _extract_instructions(prompt_b)
    
    removed_instructions = instructions_a - instructions_b
    added_instructions = instructions_b - instructions_a
    
    for instr in removed_instructions:
        changes.append(PromptChange(
            type="removed",
            description=f"Removed: '{instr[:50]}...'",
            impact="Model may no longer follow this guideline"
        ))
    
    for instr in added_instructions:
        changes.append(PromptChange(
            type="added",
            description=f"Added: '{instr[:50]}...'",
            impact="New behavioral constraint added"
        ))
    
    # Compare keywords for topic shifts
    keywords_a = _extract_keywords(prompt_a)
    keywords_b = _extract_keywords(prompt_b)
    
    removed_kw = keywords_a - keywords_b
    added_kw = keywords_b - keywords_a
    
    if len(removed_kw) > 5:
        changes.append(PromptChange(
            type="modified",
            description=f"Removed focus on: {', '.join(list(removed_kw)[:5])}...",
            impact="Topic focus has shifted"
        ))
    
    if len(added_kw) > 5:
        changes.append(PromptChange(
            type="modified",
            description=f"New focus on: {', '.join(list(added_kw)[:5])}...",
            impact="New topics or capabilities introduced"
        ))
    
    # Check length changes
    len_diff = len(prompt_b) - len(prompt_a)
    if abs(len_diff) > len(prompt_a) * 0.5:  # more than 50% change
        if len_diff > 0:
            changes.append(PromptChange(
                type="modified",
                description="Prompt is significantly longer",
                impact="More detailed instructions, potentially more constrained"
            ))
        else:
            changes.append(PromptChange(
                type="modified",
                description="Prompt is significantly shorter",
                impact="Simpler instructions, potentially more flexible"
            ))
    
    # Generate summary
    if similarity > 0.9:
        summary = "Prompts are nearly identical with minor wording changes."
    elif similarity > 0.7:
        summary = "Prompts are similar but have some meaningful differences."
    elif similarity > 0.5:
        summary = "Prompts share some common elements but differ significantly."
    else:
        summary = "Prompts are substantially different in content and intent."
    
    logger.info(f"Prompt comparison: {similarity:.2f} similarity, {len(changes)} changes")
    
    return PromptDiff(
        similarity=round(similarity, 2),
        changes=changes[:10],  # limit to 10 changes
        summary=summary,
    )
