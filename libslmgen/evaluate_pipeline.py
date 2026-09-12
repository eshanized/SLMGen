#!/usr/bin/env python3
"""
SLMGEN Pipeline Evaluation Script.

This script runs a complete evaluation of the SLMGEN pipeline:
1. Data Ingestion
2. Quality Scoring
3. Dataset Analysis
4. Model Recommendation
5. Notebook Generation

All claims are verified against actual behavior.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.models import DeploymentTarget, TaskType
from core.analyzer import analyze_dataset
from core.ingest import MIN_EXAMPLES, ingest_data
from core.notebook import generate_notebook
from core.quality import validate_quality
from core.recommender import get_recommendations


class EvaluationResult:
    """Holds results for a single evaluation step."""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.details: dict = {}
        self.errors: list[str] = []

    def success(self, **details):
        self.passed = True
        self.details = details

    def fail(self, error: str):
        self.passed = False
        self.errors.append(error)

    def as_dict(self):
        return {
            "step": self.name,
            "status": "PASS" if self.passed else "FAIL",
            "details": self.details,
            "errors": self.errors
        }


def evaluate_ingestion(dataset_path: str) -> tuple[EvaluationResult, list[dict], any]:
    """Evaluate the data ingestion step."""
    result = EvaluationResult("Data Ingestion")

    data, stats, error = ingest_data(dataset_path)

    if error:
        result.fail(f"Ingestion failed: {error}")
        return result, [], None

    if len(data) < MIN_EXAMPLES:
        result.fail(f"Only {len(data)} examples, need {MIN_EXAMPLES}")
        return result, [], None

    result.success(
        total_examples=stats.total_examples,
        total_tokens=stats.total_tokens,
        avg_tokens_per_example=stats.avg_tokens_per_example,
        single_turn_pct=stats.single_turn_pct,
        multi_turn_pct=stats.multi_turn_pct,
        has_system_prompts=stats.has_system_prompts
    )

    return result, data, stats


def evaluate_quality(data: list[dict]) -> tuple[EvaluationResult, float]:
    """Evaluate the quality scoring step."""
    result = EvaluationResult("Quality Scoring")

    if not data:
        result.fail("No data to evaluate quality")
        return result, 0.0

    score, issues = validate_quality(data)

    result.success(
        quality_score=score,
        score_percentage=f"{score * 100:.1f}%",
        issues=issues
    )

    return result, score


def evaluate_analysis(data: list[dict]) -> tuple[EvaluationResult, any]:
    """Evaluate the dataset analysis step."""
    result = EvaluationResult("Dataset Analysis")

    if not data:
        result.fail("No data to analyze")
        return result, None

    chars = analyze_dataset(data)

    result.success(
        is_multilingual=chars.is_multilingual,
        avg_response_length=chars.avg_response_length,
        looks_like_json=chars.looks_like_json,
        is_multi_turn=chars.is_multi_turn,
        has_system_prompts=chars.has_system_prompts,
        dominant_language=chars.dominant_language
    )

    return result, chars


def evaluate_recommendation(stats: any, chars: any) -> tuple[EvaluationResult, any]:
    """Evaluate the model recommendation step."""
    result = EvaluationResult("Model Recommendation")

    if not stats or not chars:
        result.fail("Missing stats or characteristics")
        return result, None

    # Test with QA task and cloud deployment
    recommendations = get_recommendations(
        task=TaskType.QA,
        deployment=DeploymentTarget.CLOUD,
        stats=stats,
        characteristics=chars
    )

    primary = recommendations.primary

    result.success(
        primary_model=primary.model_name,
        primary_model_id=primary.model_id,
        primary_score=primary.score,
        primary_reasons=primary.reasons,
        num_alternatives=len(recommendations.alternatives),
        is_gated=primary.is_gated,
        context_window=primary.context_window
    )

    return result, recommendations


def evaluate_notebook(data: list[dict], recommendation: any) -> EvaluationResult:
    """Evaluate the notebook generation step."""
    result = EvaluationResult("Notebook Generation")

    if not data or not recommendation:
        result.fail("Missing data or recommendation")
        return result

    # Convert data to JSONL string
    jsonl_str = "\n".join(json.dumps(entry) for entry in data)

    primary = recommendation.primary

    notebook_json = generate_notebook(
        dataset_jsonl=jsonl_str,
        model_id=primary.model_id,
        model_name=primary.model_name,
        model_size=primary.size,
        task_type="qa",
        num_examples=len(data),
        is_gated=primary.is_gated
    )

    # Validate notebook structure
    try:
        notebook = json.loads(notebook_json)

        # Check essential notebook properties
        has_cells = "cells" in notebook
        has_metadata = "metadata" in notebook
        has_nbformat = "nbformat" in notebook

        cell_count = len(notebook.get("cells", []))

        # Check for markdown and code cells
        markdown_cells = sum(1 for c in notebook.get("cells", []) if c.get("cell_type") == "markdown")
        code_cells = sum(1 for c in notebook.get("cells", []) if c.get("cell_type") == "code")

        if not all([has_cells, has_metadata, has_nbformat]):
            result.fail("Invalid notebook structure")
            return result

        if cell_count < 5:
            result.fail(f"Too few cells: {cell_count}")
            return result

        result.success(
            valid_json=True,
            has_cells=has_cells,
            has_metadata=has_metadata,
            total_cells=cell_count,
            markdown_cells=markdown_cells,
            code_cells=code_cells,
            notebook_size_bytes=len(notebook_json)
        )

    except json.JSONDecodeError as e:
        result.fail(f"Generated invalid JSON: {e}")

    return result


def run_evaluation(dataset_path: str) -> dict:
    """Run the complete evaluation pipeline."""
    print("=" * 60)
    print("SLMGEN Pipeline Evaluation")
    print("=" * 60)
    print(f"\nDataset: {dataset_path}\n")

    results = []

    # Step 1: Data Ingestion
    print("1. Testing Data Ingestion...")
    ing_result, data, stats = evaluate_ingestion(dataset_path)
    results.append(ing_result)
    print(f"   {'✓ PASS' if ing_result.passed else '✗ FAIL'}: {ing_result.details.get('total_examples', 0)} examples ingested")

    if not ing_result.passed:
        print("\n   Errors:", ing_result.errors)
        return {"results": [r.as_dict() for r in results], "overall": "FAIL"}

    # Step 2: Quality Scoring
    print("2. Testing Quality Scoring...")
    qual_result, quality_score = evaluate_quality(data)
    results.append(qual_result)
    print(f"   {'✓ PASS' if qual_result.passed else '✗ FAIL'}: Score = {quality_score * 100:.1f}%")

    # Step 3: Dataset Analysis
    print("3. Testing Dataset Analysis...")
    anal_result, chars = evaluate_analysis(data)
    results.append(anal_result)
    print(f"   {'✓ PASS' if anal_result.passed else '✗ FAIL'}: Analyzed {len(data)} examples")
    if anal_result.passed:
        print(f"      - Multilingual: {chars.is_multilingual}")
        print(f"      - JSON output: {chars.looks_like_json}")
        print(f"      - Multi-turn: {chars.is_multi_turn}")

    # Step 4: Model Recommendation
    print("4. Testing Model Recommendation...")
    rec_result, recommendations = evaluate_recommendation(stats, chars)
    results.append(rec_result)
    print(f"   {'✓ PASS' if rec_result.passed else '✗ FAIL'}: Recommended {rec_result.details.get('primary_model', 'N/A')}")
    if rec_result.passed:
        print(f"      - Score: {rec_result.details.get('primary_score', 0)}/100")
        print(f"      - Alternatives: {rec_result.details.get('num_alternatives', 0)}")

    # Step 5: Notebook Generation
    print("5. Testing Notebook Generation...")
    nb_result = evaluate_notebook(data, recommendations)
    results.append(nb_result)
    print(f"   {'✓ PASS' if nb_result.passed else '✗ FAIL'}: Generated notebook")
    if nb_result.passed:
        print(f"      - Cells: {nb_result.details.get('total_cells', 0)}")
        print(f"      - Size: {nb_result.details.get('notebook_size_bytes', 0):,} bytes")

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    overall = "PASS" if passed == total else "FAIL"

    print("\n" + "=" * 60)
    print(f"EVALUATION SUMMARY: {passed}/{total} steps passed")
    print(f"OVERALL RESULT: {overall}")
    print("=" * 60)

    return {
        "dataset_path": dataset_path,
        "results": [r.as_dict() for r in results],
        "passed": passed,
        "total": total,
        "overall": overall
    }


def main():
    """Main entry point."""
    # Default to the test dataset
    dataset_path = Path(__file__).parent / "data" / "test_dataset.jsonl"

    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])

    if not dataset_path.exists():
        print(f"Error: Dataset not found: {dataset_path}")
        sys.exit(1)

    result = run_evaluation(str(dataset_path))

    # Save detailed results
    output_path = Path(__file__).parent / "evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")

    sys.exit(0 if result["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
