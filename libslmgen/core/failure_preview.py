#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic Failure Preview.

Generates 2-3 failure cases from dataset patterns to show users
what might go wrong *before* they spend time training.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import random
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FailureCase:
    """A synthetic failure scenario."""
    category: str  # "hallucination", "refusal", "off-topic", "inconsistency"
    user_prompt: str
    bad_response: str
    why_it_fails: str
    likelihood: str  # "low", "medium", "high"


def _collect_patterns(data: list[dict]) -> dict:
    """Extract patterns from dataset for failure synthesis."""
    patterns = {
        "topics": [],
        "user_lengths": [],
        "response_lengths": [],
        "has_refusals": False,
        "has_code": False,
        "avg_response_len": 0,
    }
    
    all_responses = []
    
    for entry in data[:200]:  # sample for efficiency
        for msg in entry.get("messages", []):
            content = msg.get("content", "")
            role = msg.get("role")
            
            if role == "user":
                patterns["user_lengths"].append(len(content))
                # Extract first few words as topic hint
                words = content.split()[:5]
                patterns["topics"].append(" ".join(words))
                
            elif role == "assistant":
                all_responses.append(content)
                patterns["response_lengths"].append(len(content))
                
                # Check for refusal patterns
                refusal_words = ["i can't", "i cannot", "i'm unable", "i won't"]
                if any(r in content.lower() for r in refusal_words):
                    patterns["has_refusals"] = True
                
                # Check for code
                if "```" in content or "def " in content or "function" in content:
                    patterns["has_code"] = True
    
    if all_responses:
        patterns["avg_response_len"] = sum(len(r) for r in all_responses) // len(all_responses)
    
    return patterns


def _generate_hallucination_case(patterns: dict) -> FailureCase:
    """Generate a hallucination failure scenario."""
    # Pick a random topic-ish prompt
    topics = patterns.get("topics", ["the topic"])
    sample_topic = random.choice(topics) if topics else "this subject"
    
    return FailureCase(
        category="hallucination",
        user_prompt=f"Tell me the exact statistics about {sample_topic}",
        bad_response=(
            f"According to the 2023 Global Report, {sample_topic} accounts for "
            "precisely 47.3% of all instances, with a 12% increase year-over-year. "
            "The International Committee confirmed these numbers in their March publication."
        ),
        why_it_fails=(
            "The model invents specific statistics and fake sources. "
            "This happens when training data lacks factual grounding."
        ),
        likelihood="medium" if patterns.get("avg_response_len", 0) < 200 else "high"
    )


def _generate_refusal_case(patterns: dict) -> FailureCase:
    """Generate an over-refusal failure scenario."""
    return FailureCase(
        category="refusal",
        user_prompt="Can you help me write a story about a difficult situation?",
        bad_response=(
            "I'm sorry, but I can't help with that request. "
            "Writing about difficult situations could be harmful. "
            "Is there something else I can assist you with?"
        ),
        why_it_fails=(
            "The model becomes overly cautious and refuses benign requests. "
            "This can happen if training data has many refusal examples."
        ),
        likelihood="high" if patterns.get("has_refusals") else "low"
    )


def _generate_inconsistency_case(patterns: dict) -> FailureCase:
    """Generate an inconsistency failure scenario."""
    return FailureCase(
        category="inconsistency",
        user_prompt="What's the best approach for this problem?",
        bad_response=(
            "The best approach is to use method A because it's faster. "
            "However, you should always use method B as it's more reliable. "
            "Actually, method C is what most experts recommend."
        ),
        why_it_fails=(
            "The model contradicts itself within a single response. "
            "This indicates conflicting examples in the training data."
        ),
        likelihood="medium"
    )


def _generate_offtopic_case(patterns: dict) -> FailureCase:
    """Generate an off-topic failure scenario."""
    topics = patterns.get("topics", ["the topic"])
    sample_topic = random.choice(topics) if topics else "this"
    
    return FailureCase(
        category="off-topic",
        user_prompt=f"How does {sample_topic} work in practice?",
        bad_response=(
            "That's a great question! Speaking of great things, "
            "have you heard about the latest developments in AI? "
            "There's so much happening in the field right now..."
        ),
        why_it_fails=(
            "The model drifts off-topic instead of addressing the question. "
            "This can happen with datasets that have tangential responses."
        ),
        likelihood="low"
    )


def generate_failure_previews(data: list[dict], max_cases: int = 3) -> list[FailureCase]:
    """
    Generate synthetic failure cases based on dataset patterns.
    
    Shows users what might go wrong before they train,
    so they can improve their dataset or set expectations.
    """
    logger.info(f"Generating failure previews for {len(data)} examples")
    
    if len(data) < 20:
        return [FailureCase(
            category="insufficient_data",
            user_prompt="Any question",
            bad_response="[Model may produce random or incoherent output]",
            why_it_fails="With fewer than 20 examples, the model has too little to learn from.",
            likelihood="high"
        )]
    
    patterns = _collect_patterns(data)
    
    # Generate potential failures
    all_cases = [
        _generate_hallucination_case(patterns),
        _generate_inconsistency_case(patterns),
    ]
    
    if patterns.get("has_refusals"):
        all_cases.append(_generate_refusal_case(patterns))
    else:
        all_cases.append(_generate_offtopic_case(patterns))
    
    # Sort by likelihood and return top N
    likelihood_order = {"high": 0, "medium": 1, "low": 2}
    all_cases.sort(key=lambda c: likelihood_order.get(c.likelihood, 1))
    
    result = all_cases[:max_cases]
    
    logger.info(f"Generated {len(result)} failure preview cases")
    
    return result
