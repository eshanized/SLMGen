#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Processing Package.

Contains data processing, analysis, and notebook generation logic.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

from .ingest import ingest_data
from .quality import validate_quality
from .analyzer import analyze_dataset
from .recommender import get_recommendations
from .notebook import generate_notebook

# Advanced features
from .personality import detect_personality
from .risk import estimate_hallucination_risk
from .confidence import calculate_confidence
from .behavior import compose_behavior, BehaviorConfig
from .prompt_linter import lint_prompt
from .failure_preview import generate_failure_previews
from .model_card import generate_model_card
from .prompt_diff import compare_prompts
from .reverse_prompt import infer_reverse_prompt  # FIX: C1 - Added missing module

# Model Registry
from .registry import validate_hf_model, check_compatibility, get_registry, SUPPORTED_ARCHITECTURES

__all__ = [
    # Core
    "ingest_data",
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
