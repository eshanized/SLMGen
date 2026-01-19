#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Linter.

Analyzes prompts for common issues:
- Contradictions
- Redundancy
- Ambiguity
- Overload

Returns warnings, not errors - we're helping, not blocking.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Contradiction patterns
CONTRADICTION_PAIRS = [
    ("always", "never"),
    ("all", "none"),
    ("must", "should not"),
    ("required", "optional"),
    ("brief", "detailed"),
    ("concise", "comprehensive"),
    ("simple", "complex"),
    ("formal", "casual"),
]

# Redundancy indicators
REDUNDANCY_PATTERNS = [
    r"\b(very|really|extremely|highly)\b.*\b(very|really|extremely|highly)\b",
    r"\b(important|essential|crucial)\b.*\b(important|essential|crucial)\b",
]


@dataclass
class PromptWarning:
    """A single warning about a prompt issue."""
    type: str  # "contradiction", "redundancy", "ambiguity", "overload"
    severity: str  # "low", "medium", "high"
    message: str
    suggestion: str


@dataclass
class LintResult:
    """Result of prompt linting."""
    score: int  # 0-100, higher is better
    warnings: list[PromptWarning]
    is_good: bool


def _check_contradictions(text: str) -> list[PromptWarning]:
    """Find contradictory statements in the prompt."""
    warnings = []
    text_lower = text.lower()
    
    for word1, word2 in CONTRADICTION_PAIRS:
        if word1 in text_lower and word2 in text_lower:
            warnings.append(PromptWarning(
                type="contradiction",
                severity="high",
                message=f"Potential contradiction: '{word1}' and '{word2}' both appear",
                suggestion=f"Consider clarifying whether you mean '{word1}' or '{word2}'"
            ))
    
    return warnings


def _check_redundancy(text: str) -> list[PromptWarning]:
    """Find redundant or repetitive language."""
    warnings = []
    
    # Check for repeated emphasis words
    for pattern in REDUNDANCY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(PromptWarning(
                type="redundancy",
                severity="low",
                message="Multiple emphasis words detected",
                suggestion="Consider reducing emphasis words for clarity"
            ))
            break
    
    # Check for repeated sentences
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip().lower() for s in sentences if s.strip()]
    if len(sentences) != len(set(sentences)):
        warnings.append(PromptWarning(
            type="redundancy",
            severity="medium",
            message="Repeated sentence or phrase detected",
            suggestion="Remove duplicate instructions"
        ))
    
    return warnings


def _check_ambiguity(text: str) -> list[PromptWarning]:
    """Find vague or ambiguous language."""
    warnings = []
    
    ambiguous_phrases = [
        (r"\b(sometimes|occasionally|maybe)\b", "Vague frequency"),
        (r"\b(kind of|sort of|somewhat)\b", "Imprecise qualifier"),
        (r"\b(things?|stuff|etc\.?)\b", "Vague reference"),
        (r"\b(appropriate|suitable|proper)\b", "Subjective term without definition"),
    ]
    
    for pattern, issue in ambiguous_phrases:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            warnings.append(PromptWarning(
                type="ambiguity",
                severity="low",
                message=f"{issue}: '{matches[0]}'",
                suggestion="Consider being more specific"
            ))
    
    return warnings[:3]  # limit to 3


def _check_overload(text: str) -> list[PromptWarning]:
    """Check if prompt is too complex or long."""
    warnings = []
    
    # Word count check
    words = text.split()
    if len(words) > 500:
        warnings.append(PromptWarning(
            type="overload",
            severity="high",
            message=f"Prompt is very long ({len(words)} words)",
            suggestion="Consider breaking into smaller, focused instructions"
        ))
    elif len(words) > 200:
        warnings.append(PromptWarning(
            type="overload",
            severity="medium",
            message=f"Prompt is quite long ({len(words)} words)",
            suggestion="Shorter prompts often work better"
        ))
    
    # Instruction count check
    instruction_patterns = r"\b(must|should|always|never|do not|don't|make sure)\b"
    instructions = len(re.findall(instruction_patterns, text, re.IGNORECASE))
    
    if instructions > 10:
        warnings.append(PromptWarning(
            type="overload",
            severity="high",
            message=f"Too many instructions ({instructions} directive words)",
            suggestion="Focus on the most important 3-5 instructions"
        ))
    elif instructions > 5:
        warnings.append(PromptWarning(
            type="overload",
            severity="low",
            message=f"Many instructions detected ({instructions})",
            suggestion="Consider prioritizing key instructions"
        ))
    
    return warnings


def lint_prompt(text: str) -> LintResult:
    """
    Analyze a prompt for common issues.
    
    Returns warnings to help improve the prompt,
    but doesn't block usage - we're assistants, not gatekeepers.
    """
    logger.info(f"Linting prompt ({len(text)} chars)")
    
    if not text or not text.strip():
        return LintResult(
            score=0,
            warnings=[PromptWarning(
                type="empty",
                severity="high",
                message="Prompt is empty",
                suggestion="Add some instructions for the model"
            )],
            is_good=False
        )
    
    # Run all checks
    warnings = []
    warnings.extend(_check_contradictions(text))
    warnings.extend(_check_redundancy(text))
    warnings.extend(_check_ambiguity(text))
    warnings.extend(_check_overload(text))
    
    # Calculate score
    penalty = 0
    for w in warnings:
        if w.severity == "high":
            penalty += 20
        elif w.severity == "medium":
            penalty += 10
        else:
            penalty += 5
    
    score = max(0, 100 - penalty)
    is_good = score >= 70
    
    logger.info(f"Lint complete: score={score}, warnings={len(warnings)}")
    
    return LintResult(
        score=score,
        warnings=warnings,
        is_good=is_good,
    )
