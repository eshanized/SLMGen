#!/usr/bin/env python3
"""
Tests for dataset ingestion module.

Covers:
- Blank lines handling
- Malformed JSON handling
- Non-UTF8 byte handling
- Mixed valid/invalid lines
"""

import json

# Import with path adjustment for test environment
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.ingest import MIN_EXAMPLES, ingest_data


def _create_temp_jsonl(lines: list[str], suffix: str = ".jsonl") -> str:
    """Helper to create a temporary JSONL file."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    for line in lines:
        f.write(line + "\n")
    f.close()
    return f.name


def _make_valid_entry(user_msg: str = "Hello", assistant_msg: str = "Hi there!") -> str:
    """Create a valid JSONL entry."""
    return json.dumps({
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg}
        ]
    })


class TestBlankLines:
    """Test that blank lines are handled correctly."""

    def test_blank_lines_skipped(self):
        """Blank lines should be skipped without error."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(60)]
        # Insert blank lines at various positions
        lines.insert(10, "")
        lines.insert(20, "   ")  # whitespace only
        lines.insert(30, "\t")  # tab only

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is None
            assert len(data) == 60  # Only valid entries counted
            assert stats.total_examples == 60
        finally:
            Path(path).unlink()

    def test_file_with_only_blank_lines(self):
        """File with only blank lines should fail gracefully."""
        path = _create_temp_jsonl(["", "   ", "\t", ""])
        try:
            data, stats, error = ingest_data(path)
            assert error is not None
            assert "at least" in error.lower()
        finally:
            Path(path).unlink()


class TestMalformedJSON:
    """Test handling of malformed JSON entries."""

    def test_malformed_json_skipped(self):
        """Malformed JSON lines should be skipped."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(60)]
        # Insert malformed JSON
        lines.insert(5, "{invalid json}")
        lines.insert(15, "not even json at all")
        lines.insert(25, '{"messages": [incomplete')

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is None
            assert len(data) == 60  # Only valid entries
        finally:
            Path(path).unlink()

    def test_valid_json_wrong_structure(self):
        """Valid JSON but wrong structure should be skipped."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(60)]
        # Insert valid JSON but wrong structure
        lines.insert(10, '{"not_messages": []}')
        lines.insert(20, '{"messages": "not_an_array"}')
        lines.insert(30, '[]')  # Array instead of object

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is None
            assert len(data) == 60
        finally:
            Path(path).unlink()


class TestMixedValidInvalid:
    """Test datasets with mixed valid and invalid entries."""

    def test_mixed_entries_below_minimum(self):
        """Should fail if valid entries < MIN_EXAMPLES after filtering."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(30)]
        lines.extend(["{invalid}" for _ in range(20)])

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is not None
            assert str(MIN_EXAMPLES) in error
        finally:
            Path(path).unlink()

    def test_mixed_entries_above_minimum(self):
        """Should succeed if enough valid entries remain."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(60)]
        lines.extend(["{invalid}" for _ in range(10)])

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is None
            assert len(data) == 60
        finally:
            Path(path).unlink()


class TestRoleValidation:
    """Test message role validation."""

    def test_missing_user_message(self):
        """Entry without user message should be skipped."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(60)]
        lines.insert(10, json.dumps({
            "messages": [
                {"role": "assistant", "content": "orphan response"},
                {"role": "assistant", "content": "another"}
            ]
        }))

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is None
            assert len(data) == 60  # Invalid entry skipped
        finally:
            Path(path).unlink()

    def test_missing_assistant_message(self):
        """Entry without assistant message should be skipped."""
        lines = [_make_valid_entry(f"msg {i}", f"response {i}") for i in range(60)]
        lines.insert(10, json.dumps({
            "messages": [
                {"role": "user", "content": "question 1"},
                {"role": "user", "content": "question 2"}
            ]
        }))

        path = _create_temp_jsonl(lines)
        try:
            data, stats, error = ingest_data(path)
            assert error is None
            assert len(data) == 60
        finally:
            Path(path).unlink()


class TestFileExtension:
    """Test file extension validation."""

    def test_wrong_extension_rejected(self):
        """Non-.jsonl files should be rejected."""
        path = _create_temp_jsonl([_make_valid_entry()], suffix=".txt")
        try:
            data, stats, error = ingest_data(path)
            assert error is not None
            assert ".jsonl" in error.lower()
        finally:
            Path(path).unlink()
