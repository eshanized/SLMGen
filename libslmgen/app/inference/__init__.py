#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inference Module.

Provides real-time inference and model comparison capabilities.

Modules:
    engine: HuggingFace Inference API wrapper
    comparison: Side-by-side model comparison

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

from app.inference.engine import (
    InferenceEngine,
    InferenceConfig,
    GenerationResult,
    get_inference_engine,
    shutdown_inference_engine,
)

from app.inference.comparison import (
    ComparisonEngine,
    ComparisonResult,
    ComparisonMetrics,
    get_comparison_engine,
)

__all__ = [
    "InferenceEngine",
    "InferenceConfig",
    "GenerationResult",
    "get_inference_engine",
    "shutdown_inference_engine",
    "ComparisonEngine",
    "ComparisonResult",
    "ComparisonMetrics",
    "get_comparison_engine",
]
