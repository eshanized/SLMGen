#!/usr/bin/env python3
"""
Tests for model recommendation engine.

Covers:
- Score bounds (0-100)
- Hard override precedence
- Multi-turn bonus correctness
"""

# Import with path adjustment for test environment
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.models import (
    DatasetCharacteristics,
    DatasetStats,
    DeploymentTarget,
    TaskType,
)
from core.recommender import (
    MODELS,
    _apply_bonuses,
    _score_data_fit,
    _score_deployment_fit,
    _score_task_fit,
    get_recommendations,
)


def _make_stats(total_examples: int = 200, avg_tokens: int = 100) -> DatasetStats:
    """Create sample dataset stats."""
    return DatasetStats(
        total_examples=total_examples,
        total_tokens=total_examples * avg_tokens,
        avg_tokens_per_example=avg_tokens,
        single_turn_pct=50,
        multi_turn_pct=50,
        has_system_prompts=False,
        quality_score=0.85,
        quality_issues=[],
    )


def _make_chars(
    is_multilingual: bool = False,
    looks_like_json: bool = False,
    is_multi_turn: bool = False,
) -> DatasetCharacteristics:
    """Create sample dataset characteristics."""
    return DatasetCharacteristics(
        is_multilingual=is_multilingual,
        avg_response_length=150,
        looks_like_json=looks_like_json,
        is_multi_turn=is_multi_turn,
        has_system_prompts=False,
        dominant_language="en",
    )


class TestScoreBounds:
    """Test that scores stay within valid bounds."""

    def test_recommendation_scores_within_bounds(self):
        """All recommendation scores should be 0-100."""
        stats = _make_stats()
        chars = _make_chars()

        result = get_recommendations(
            task=TaskType.QA,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        assert 0 <= result.primary.score <= 100
        for alt in result.alternatives:
            assert 0 <= alt.score <= 100

    def test_task_fit_score_bounds(self):
        """Task fit score should be within expected range."""
        for model_key, model in MODELS.items():
            for task in TaskType:
                score = _score_task_fit(model, task)
                assert 0 <= score <= 50, f"Task fit score out of range for {model_key}"

    def test_deployment_fit_score_bounds(self):
        """Deployment fit score should be within expected range."""
        for model_key, model in MODELS.items():
            for deploy in DeploymentTarget:
                score = _score_deployment_fit(model, deploy)
                assert 0 <= score <= 30, f"Deployment fit score out of range for {model_key}"

    def test_data_fit_score_bounds(self):
        """Data fit score should be within expected range."""
        stats = _make_stats()
        chars = _make_chars()

        for model_key, model in MODELS.items():
            score = _score_data_fit(model, stats, chars)
            assert 0 <= score <= 20, f"Data fit score out of range for {model_key}"

    def test_score_never_exceeds_100(self):
        """Total score should be capped at 100 even with bonuses."""
        stats = _make_stats(total_examples=5000, avg_tokens=5000)  # Large dataset
        chars = _make_chars(is_multilingual=True, is_multi_turn=True)

        result = get_recommendations(
            task=TaskType.CONVERSATION,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        assert result.primary.score <= 100


class TestHardOverrides:
    """Test hard override precedence for special cases."""

    def test_multilingual_override_favors_qwen(self):
        """Multilingual data should strongly favor Qwen."""
        stats = _make_stats()
        chars = _make_chars(is_multilingual=True)

        result = get_recommendations(
            task=TaskType.QA,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        # Find Qwen in results
        qwen_found = False
        for rec in [result.primary] + result.alternatives:
            if "qwen" in rec.model_id.lower():
                qwen_found = True
                # Qwen should have high score due to override
                assert rec.score >= 70

        assert qwen_found, "Qwen should be in recommendations for multilingual data"

    def test_edge_deployment_override_favors_gemma(self):
        """Edge deployment should favor Gemma due to compact size."""
        stats = _make_stats()
        chars = _make_chars()

        result = get_recommendations(
            task=TaskType.CLASSIFY,
            deployment=DeploymentTarget.EDGE,
            stats=stats,
            characteristics=chars,
        )

        # Gemma should be in top recommendations for edge
        gemma_found = False
        for rec in [result.primary] + result.alternatives:
            if "gemma" in rec.model_id.lower():
                gemma_found = True

        assert gemma_found, "Gemma should appear for edge deployment"

    def test_mobile_deployment_favors_small_models(self):
        """Mobile deployment should favor smaller models."""
        stats = _make_stats()
        chars = _make_chars()

        result = get_recommendations(
            task=TaskType.QA,
            deployment=DeploymentTarget.MOBILE,
            stats=stats,
            characteristics=chars,
        )

        # Primary recommendation should be a small model
        small_sizes = {"1B", "1.1B", "1.3B", "1.7B", "2B"}
        assert result.primary.size in small_sizes or "gemma" in result.primary.model_id.lower()


class TestMultiTurnBonus:
    """Test multi-turn conversation bonus."""

    def test_multi_turn_adds_bonus(self):
        """Multi-turn data should get bonus points."""
        stats = _make_stats()
        single_turn_chars = _make_chars(is_multi_turn=False)
        multi_turn_chars = _make_chars(is_multi_turn=True)

        for model in MODELS.values():
            single_bonus = _apply_bonuses(model, stats, single_turn_chars)
            multi_bonus = _apply_bonuses(model, stats, multi_turn_chars)

            # Multi-turn should get MORE bonus
            assert multi_bonus >= single_bonus

    def test_multi_turn_bonus_value(self):
        """Multi-turn bonus should be 10 points."""
        stats = _make_stats()
        multi_turn_chars = _make_chars(is_multi_turn=True)

        # Pick any model
        model = MODELS["llama32"]
        bonus = _apply_bonuses(model, stats, multi_turn_chars)

        # Multi-turn contributes at least 10 to bonus
        assert bonus >= 10


class TestReasonTruthfulness:
    """Test that reasons match actual conditions."""

    def test_reasons_not_empty(self):
        """Recommendations should have at least one reason."""
        stats = _make_stats()
        chars = _make_chars()

        result = get_recommendations(
            task=TaskType.QA,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        assert len(result.primary.reasons) > 0

    def test_multilingual_reason_appears_when_appropriate(self):
        """Multilingual reason should appear for multilingual data with Qwen."""
        stats = _make_stats()
        chars = _make_chars(is_multilingual=True)

        result = get_recommendations(
            task=TaskType.QA,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        # Find Qwen and check for multilingual reason
        for rec in [result.primary] + result.alternatives:
            if "qwen" in rec.model_id.lower():
                all_reasons = " ".join(rec.reasons).lower()
                assert "multilingual" in all_reasons


class TestModelGatedStatus:
    """Test that gated status is correctly reported."""

    def test_llama_is_gated(self):
        """Llama models should be marked as gated."""
        stats = _make_stats()
        chars = _make_chars()

        result = get_recommendations(
            task=TaskType.CONVERSATION,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        for rec in [result.primary] + result.alternatives:
            if "llama" in rec.model_id.lower():
                assert rec.is_gated is True

    def test_phi_is_not_gated(self):
        """Phi models should not be marked as gated."""
        stats = _make_stats()
        chars = _make_chars()

        result = get_recommendations(
            task=TaskType.QA,
            deployment=DeploymentTarget.CLOUD,
            stats=stats,
            characteristics=chars,
        )

        for rec in [result.primary] + result.alternatives:
            if "phi" in rec.model_id.lower():
                assert rec.is_gated is False
