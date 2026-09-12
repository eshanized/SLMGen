#!/usr/bin/env python3
"""
Core Processing Package.

Contains data processing, analysis, and notebook generation logic.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

from .analyzer import analyze_dataset
from .behavior import BehaviorConfig, compose_behavior
from .confidence import calculate_confidence
from .failure_preview import generate_failure_previews
from .ingest import ingest_data, ingest_from_bytes, ingest_from_str
from .model_card import generate_model_card
from .notebook import generate_notebook

# Advanced features
from .personality import detect_personality
from .prompt_diff import compare_prompts
from .prompt_linter import lint_prompt
from .quality import validate_quality
from .recommender import get_recommendations

# Model Registry
from .registry import (
    SUPPORTED_ARCHITECTURES,
    check_compatibility,
    get_registry,
    validate_hf_model,
)
from .reverse_prompt import infer_reverse_prompt  # FIX: C1 - Added missing module
from .risk import estimate_hallucination_risk

__all__ = [
    # Core
    "ingest_data",
    "ingest_from_bytes",
    "ingest_from_str",
    "validate_quality",
    "analyze_dataset",
    "get_recommendations",
    "generate_notebook",
    # Advanced
    "detect_personality",
    "estimate_hallucination_risk",
    "calculate_confidence",
    "compose_behavior",
    "BehaviorConfig",
    "lint_prompt",
    "generate_failure_previews",
    "generate_model_card",
    "compare_prompts",
    "infer_reverse_prompt",  # FIX: C1 - Added missing module
    # Model Registry
    "validate_hf_model",
    "check_compatibility",
    "get_registry",
    "SUPPORTED_ARCHITECTURES",
]
