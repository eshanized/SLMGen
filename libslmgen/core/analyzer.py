#!/usr/bin/env python3
"""
Dataset Analyzer.

Extracts characteristics from the data that help us pick the right model.
Things like: is it multilingual? Does it look like JSON output? etc.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
import re

from app.models import DatasetCharacteristics

logger = logging.getLogger(__name__)


def _check_multilingual(data: list[dict]) -> tuple[bool, str]:
    """
    Detect if dataset is multilingual using non-ASCII character ratio.

    FIX: B3 - Documentation of heuristic limitations

    KNOWN LIMITATIONS:
    - False positives: Emojis, accented English (café, naïve), special
      characters will trigger multilingual detection
    - False negatives: Romanized languages (pinyin, romaji) will not be
      detected as multilingual since they use ASCII
    - This is a rough heuristic, not a language detection library

    The 30% threshold was chosen to minimize false positives from
    occasional accented characters while catching genuinely
    multilingual datasets.
    """
    non_ascii_count = 0
    total_chars = 0

    # Sample a subset if dataset is large
    sample = data[:500] if len(data) > 500 else data

    for entry in sample:
        for msg in entry.get("messages", []):
            content = msg.get("content", "")
            total_chars += len(content)
            non_ascii_count += sum(1 for c in content if ord(c) > 127)

    # If more than 30% non-ASCII, likely multilingual
    ratio = (non_ascii_count / total_chars) if total_chars > 0 else 0

    if ratio > 0.3:
        return True, "multilingual"
    elif ratio > 0.1:
        return True, "some_non_english"

    return False, "en"


def _avg_response_length(data: list[dict]) -> int:
    """Calculate average assistant response Length."""
    lengths = []

    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                lengths.append(len(msg.get("content", "")))

    return int(sum(lengths) / len(lengths)) if lengths else 0


def _looks_like_json_output(data: list[dict]) -> bool:
    """
    Check if assistant responses look like JSON.
    This affects model selection - some are better at structured Output.
    """
    json_like_count = 0
    total_responses = 0

    # Sample for Efficiency
    sample = data[:200] if len(data) > 200 else data

    for entry in sample:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                total_responses += 1
                content = msg.get("content", "").strip()

                # Check if starts with { or [ (JSON-ish)
                if content and content[0] in "{[":
                    json_like_count += 1

    # If more than 50% look like JSON
    ratio = json_like_count / total_responses if total_responses > 0 else 0
    return ratio > 0.5


def _is_multi_turn(data: list[dict]) -> bool:
    """Check if dataset is predominantly multi-turn."""
    multi_turn_count = 0

    for entry in data:
        messages = entry.get("messages", [])
        # Exclude system message for turn Count
        non_system = [m for m in messages if m.get("role") != "system"]
        if len(non_system) > 2:
            multi_turn_count += 1

    return (multi_turn_count / len(data)) > 0.5 if data else False


def _has_system_prompts(data: list[dict]) -> bool:
    """Check if dataset uses system Prompts."""
    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "system":
                return True
    return False


def _detect_dominant_language(data: list[dict]) -> str:
    """
    Try to detect the dominant Language.
    Uses some simple Heuristics based on common words.
    """
    # Common words in different Languages
    lang_patterns = {
        "en": r"\b(the|is|are|was|were|have|has|been|will|would|could|should)\b",
        "es": r"\b(el|la|los|las|un|una|es|son|está|están|para|con|por)\b",
        "fr": r"\b(le|la|les|un|une|est|sont|dans|pour|avec|sur)\b",
        "de": r"\b(der|die|das|ein|eine|ist|sind|für|mit|auf|von)\b",
        "zh": r"[\u4e00-\u9fff]",  # Chinese characters
        "ja": r"[\u3040-\u309f\u30a0-\u30ff]",  # Hiragana/Katakana
        "ko": r"[\uac00-\ud7af]",  # Korean Hangul
    }

    # Collect all text
    all_text = " ".join(
        msg.get("content", "")
        for entry in data[:100]  # sample
        for msg in entry.get("messages", [])
    ).lower()

    # Count matches for each Language
    lang_scores = {}
    for lang, pattern in lang_patterns.items():
        matches = len(re.findall(pattern, all_text, re.IGNORECASE))
        lang_scores[lang] = matches

    # Get the one with most Matches
    if not lang_scores:
        return "en"

    best_lang = max(lang_scores.keys(), key=lambda k: lang_scores[k])

    # Only return non-English if it's clearly Dominant
    if best_lang != "en" and lang_scores.get(best_lang, 0) > lang_scores.get("en", 0) * 2:
        return best_lang

    return "en"


def analyze_dataset(data: list[dict]) -> DatasetCharacteristics:
    """
    Extract all dataset characteristics for model Selection.
    """
    logger.info(f"Analyzing dataset with {len(data)} examples")

    is_multi, lang_hint = _check_multilingual(data)

    chars = DatasetCharacteristics(
        is_multilingual=is_multi,
        avg_response_length=_avg_response_length(data),
        looks_like_json=_looks_like_json_output(data),
        is_multi_turn=_is_multi_turn(data),
        has_system_prompts=_has_system_prompts(data),
        dominant_language=_detect_dominant_language(data) if is_multi else "en",
    )

    logger.info(f"Analysis complete: multilingual={chars.is_multilingual}, "
                f"json_output={chars.looks_like_json}, multi_turn={chars.is_multi_turn}")

    return chars
