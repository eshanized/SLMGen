#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Inference Module.

Covers:
- Inference engine
- Comparison engine
- Router endpoints
- Risk scoring
- Similarity computation

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.inference.engine import (
    InferenceEngine,
    InferenceConfig,
    GenerationResult,
)
from app.inference.comparison import (
    ComparisonEngine,
    _compute_text_similarity,
    _compute_risk_score,
    _compute_quality_score,
)


# ============================================
# Inference Engine Tests
# ============================================

class TestInferenceConfig:
    """Test inference configuration."""

    def test_default_config(self):
        """Default config has sensible values."""
        config = InferenceConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 512
        assert config.timeout == 30.0

    def test_custom_config(self):
        """Custom config values work."""
        config = InferenceConfig(
            temperature=1.0,
            max_tokens=256,
            do_sample=False,
        )
        assert config.temperature == 1.0
        assert config.max_tokens == 256
        assert config.do_sample is False


class TestGenerationResult:
    """Test generation result dataclass."""

    def test_successful_result(self):
        """Successful result has expected fields."""
        result = GenerationResult(
            model_id="test/model",
            output="Hello, world!",
            latency_ms=1500.5,
            tokens=10,
            finish_reason="stop",
        )
        assert result.model_id == "test/model"
        assert result.output == "Hello, world!"
        assert result.latency_ms == 1500.5
        assert result.tokens == 10
        assert result.finish_reason == "stop"
        assert result.error is None

    def test_error_result(self):
        """Error result has error field."""
        result = GenerationResult(
            model_id="test/model",
            output="",
            latency_ms=100.0,
            tokens=0,
            finish_reason="error",
            error="Model not found",
        )
        assert result.error == "Model not found"


# ============================================
# Comparison Engine Tests
# ============================================

class TestTextSimilarity:
    """Test text similarity computation."""

    def test_identical_texts(self):
        """Identical texts return high similarity."""
        text = "Hello, how are you today?"
        score = _compute_text_similarity(text, text)
        assert score == 1.0

    def test_similar_texts(self):
        """Similar texts return moderate-high similarity."""
        text1 = "Hello, how are you today?"
        text2 = "Hello, how are you tomorrow?"
        score = _compute_text_similarity(text1, text2)
        assert 0.3 < score < 1.0

    def test_different_texts(self):
        """Different texts return low similarity."""
        text1 = "The cat sat on the mat"
        text2 = "A dog ran through the park"
        score = _compute_text_similarity(text1, text2)
        assert score < 0.5

    def test_empty_texts(self):
        """Empty texts handled gracefully."""
        score = _compute_text_similarity("", "")
        assert score == 1.0

        score = _compute_text_similarity("Hello", "")
        assert score == 0.0


class TestRiskScoring:
    """Test risk score computation."""

    def test_low_risk_text(self):
        """Grounded text has low risk."""
        text = "According to research, the data shows that 73% of users prefer option A."
        score, level = _compute_risk_score(text)
        assert score < 0.5
        assert level in ["low", "medium"]

    def test_high_risk_text(self):
        """Vague text has higher risk."""
        text = "This might probably be essentially a good approach that could work possibly."
        score, level = _compute_risk_score(text)
        # High abstraction should increase score
        assert score >= 0.3

    def test_empty_text(self):
        """Empty text has medium risk."""
        score, level = _compute_risk_score("")
        assert score == 0.5
        assert level == "medium"


class TestQualityScoring:
    """Test quality score computation."""

    def test_good_quality_text(self):
        """Good text has high quality."""
        text = """
        Machine learning is a subset of artificial intelligence that enables
        systems to learn and improve from experience. It uses algorithms to
        identify patterns in data and make decisions with minimal human intervention.
        
        There are three main types of machine learning: supervised learning,
        unsupervised learning, and reinforcement learning. Each has its own
        use cases and applications in various industries.
        """
        score = _compute_quality_score(text)
        assert score > 0.5

    def test_poor_quality_text(self):
        """Short text has lower quality."""
        text = "Hello"
        score = _compute_quality_score(text)
        assert score < 0.5

    def test_empty_text(self):
        """Empty text has zero quality."""
        score = _compute_quality_score("")
        assert score == 0.0


class TestComparisonEngine:
    """Test comparison engine."""

    @pytest.mark.asyncio
    async def test_compare_single_model(self):
        """Compare with single model works."""
        mock_inference = AsyncMock()
        mock_inference.generate.return_value = GenerationResult(
            model_id="test/model",
            output="Hello!",
            latency_ms=1000.0,
            tokens=5,
            finish_reason="stop",
        )

        engine = ComparisonEngine(mock_inference)
        result = await engine.compare(
            base_model="test/model",
            tuned_model=None,
            prompt="Hi!",
        )

        assert result.base_model_id == "test/model"
        assert result.tuned_model_id is None
        assert result.base_output == "Hello!"
        assert result.metrics.base_latency_ms == 1000.0

    @pytest.mark.asyncio
    async def test_compare_two_models_parallel(self):
        """Compare with two models runs in parallel."""
        mock_inference = AsyncMock()
        mock_inference.generate_parallel.return_value = [
            GenerationResult(
                model_id="base/model",
                output="Hello from base!",
                latency_ms=1000.0,
                tokens=5,
                finish_reason="stop",
            ),
            GenerationResult(
                model_id="tuned/model",
                output="Hello from tuned!",
                latency_ms=1200.0,
                tokens=6,
                finish_reason="stop",
            ),
        ]

        engine = ComparisonEngine(mock_inference)
        result = await engine.compare(
            base_model="base/model",
            tuned_model="tuned/model",
            prompt="Hi!",
        )

        assert result.base_model_id == "base/model"
        assert result.tuned_model_id == "tuned/model"
        assert result.base_output == "Hello from base!"
        assert result.tuned_output == "Hello from tuned!"
        assert result.metrics.base_latency_ms == 1000.0
        assert result.metrics.tuned_latency_ms == 1200.0
        assert result.metrics.latency_delta_ms == 200.0


# ============================================
# Router Endpoint Tests
# ============================================

class TestInferenceRouter:
    """Test inference router endpoints."""

    def test_list_models_endpoint(self):
        """List models endpoint returns model list."""
        from app.routers.inference import _get_available_models
        
        models = _get_available_models()
        assert len(models) > 0
        assert all(hasattr(m, 'model_id') for m in models)
        assert all(hasattr(m, 'name') for m in models)

    def test_model_includes_required_fields(self):
        """Each model has required fields."""
        from app.routers.inference import _get_available_models
        
        models = _get_available_models()
        for model in models:
            assert hasattr(model, 'model_id')
            assert hasattr(model, 'name')
            assert hasattr(model, 'size')
            assert hasattr(model, 'is_gated')
            assert hasattr(model, 'context_window')


# ============================================
# Integration Tests
# ============================================

class TestInferenceIntegration:
    """Integration-style tests."""

    @pytest.mark.asyncio
    async def test_engine_lifecycle(self):
        """Engine can be created, used, and closed."""
        engine = InferenceEngine(timeout=5.0)
        
        # Client should be created lazily
        client = await engine._get_client()
        assert client is not None
        
        # Close should work
        await engine.close()
        assert engine._client is None or engine._client.is_closed
