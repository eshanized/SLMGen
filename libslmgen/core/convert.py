#!/usr/bin/env python3
"""
Dataset Converter.

Converts various formats to ChatML JSONL for fine-tuning.
Supported formats:
- CSV
- TSV
- JSON (array of objects)
- JSON Lines (JSONL)
- Alpaca format
- ShareGPT format

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import csv
import json
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Error during dataset conversion."""


def detect_delimiter(content: str) -> str:
    """Auto-detect CSV delimiter."""
    first_line = content.split('\n')[0]
    if first_line.count('\t') > first_line.count(','):
        return '\t'
    return ','


def convert_csv(
    content: str,
    text_column: str = "text",
    instruction_column: str | None = None,
) -> list[dict]:
    """
    Convert CSV to ChatML format.

    Args:
        content: CSV file content
        text_column: Column name for the full text
        instruction_column: Optional column for instruction (used for input/output)

    Returns:
        List of ChatML-formatted entries
    """
    delimiter = detect_delimiter(content)
    lines = content.strip().split('\n')

    if not lines:
        raise ConversionError("Empty CSV content")

    # Parse header
    reader = csv.DictReader(lines, delimiter=delimiter)
    fieldnames = reader.fieldnames or []

    if text_column not in fieldnames:
        raise ConversionError(
            f"Column '{text_column}' not found. Available: {fieldnames}"
        )

    results = []
    for row in reader:
        if instruction_column and instruction_column in fieldnames:
            # Two-column format: instruction + output
            messages = [
                {"role": "user", "content": row.get(instruction_column, "")},
                {"role": "assistant", "content": row.get(text_column, "")},
            ]
        else:
            # Single column: just text
            messages = [
                {"role": "user", "content": "Convert this text: " + row.get(text_column, "")},
                {"role": "assistant", "content": row.get(text_column, "")},
            ]

        results.append({"messages": messages})

    logger.info(f"Converted {len(results)} CSV entries to ChatML")
    return results


def convert_tsv(content: str, text_column: str = "text") -> list[dict]:
    """Convert TSV to ChatML format (same as CSV with tab delimiter)."""
    return convert_csv(content, text_column=text_column)


def convert_json(
    content: str,
    text_field: str = "text",
    input_field: str | None = "input",
    output_field: str | None = "output",
) -> list[dict]:
    """
    Convert JSON array to ChatML format.

    Expected JSON structure:
    [
        {"text": "..."},
        {"input": "...", "output": "..."}
    ]
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ConversionError(f"Invalid JSON: {e}")

    if not isinstance(data, list):
        raise ConversionError("JSON must be an array of objects")

    results = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item at index {idx}")
            continue

        if input_field and input_field in item and output_field in item:
            # Instruction + output format
            messages = [
                {"role": "user", "content": item.get(input_field, "")},
                {"role": "assistant", "content": item.get(output_field, "")},
            ]
        elif text_field and text_field in item:
            # Simple text format
            messages = [
                {"role": "user", "content": item.get(text_field, "")},
                {"role": "assistant", "content": item.get(text_field, "")},
            ]
        else:
            # Try to find any string fields
            str_fields = {k: v for k, v in item.items() if isinstance(v, str)}
            if str_fields:
                content_value = list(str_fields.values())[0]
                messages = [
                    {"role": "user", "content": content_value},
                    {"role": "assistant", "content": content_value},
                ]
            else:
                logger.warning(f"Skipping item at index {idx} - no string fields")
                continue

        results.append({"messages": messages})

    logger.info(f"Converted {len(results)} JSON entries to ChatML")
    return results


def convert_jsonl(content: str) -> list[dict]:
    """
    Convert JSON Lines (JSONL) to ChatML format.

    Each line is a valid JSON object with messages array.
    """
    lines = content.strip().split('\n')
    results = []

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        try:
            item = json.loads(line)
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping invalid JSON at line {idx + 1}: {e}")
            continue

        # Validate has messages
        if "messages" in item and isinstance(item["messages"], list):
            results.append(item)
        else:
            # Try to wrap in messages format
            messages = [
                {"role": "user", "content": str(item)},
                {"role": "assistant", "content": str(item)},
            ]
            results.append({"messages": messages})

    logger.info(f"Converted {len(results)} JSONL entries to ChatML")
    return results


def convert_alpaca(content: str) -> list[dict]:
    """
    Convert Alpaca format to ChatML.

    Expected JSON structure:
    [
        {
            "instruction": "...",
            "input": "...",  // optional
            "output": "..."
        }
    ]
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ConversionError(f"Invalid JSON: {e}")

    if not isinstance(data, list):
        raise ConversionError("JSON must be an array of objects")

    results = []
    for item in data:
        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output = item.get("output", "")

        if not output:
            logger.warning("Skipping item without output field")
            continue

        # Build conversation
        if input_text:
            user_content = f"Instruction: {instruction}\nInput: {input_text}"
        else:
            user_content = instruction

        messages = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output},
        ]

        results.append({"messages": messages})

    logger.info(f"Converted {len(results)} Alpaca entries to ChatML")
    return results


def convert_sharegpt(content: str) -> list[dict]:
    """
    Convert ShareGPT format to ChatML.

    Expected structure:
    [
        {
            "conversations": [
                {"from": "human", "value": "..."},
                {"from": "gpt", "value": "..."}
            ]
        }
    ]
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ConversionError(f"Invalid JSON: {e}")

    if not isinstance(data, list):
        raise ConversionError("JSON must be an array of objects")

    results = []
    for item in data:
        conversations = item.get("conversations", [])
        if not conversations:
            continue

        messages = []
        for msg in conversations:
            role = msg.get("from", "")
            value = msg.get("value", "")

            # Map ShareGPT roles to ChatML
            if role == "human":
                mapped_role = "user"
            elif role == "gpt":
                mapped_role = "assistant"
            else:
                mapped_role = "user"  # Default

            messages.append({"role": mapped_role, "content": value})

        if messages:
            results.append({"messages": messages})

    logger.info(f"Converted {len(results)} ShareGPT entries to ChatML")
    return results


# Format detection
def detect_format(content: str) -> str:
    """
    Auto-detect the format of the content.

    Returns:
        'csv', 'tsv', 'json', 'jsonl', 'alpaca', 'sharegpt', or 'unknown'
    """
    content = content.strip()

    # Check for JSON array
    if content.startswith('['):
        try:
            data = json.loads(content)
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    first = data[0]
                    if "conversations" in first:
                        return "sharegpt"
                    elif "instruction" in first:
                        return "alpaca"
                    elif "messages" in first:
                        return "jsonl"  # Already ChatML
                    else:
                        return "json"
        except json.JSONDecodeError:
            pass

    # Check for JSONL (one JSON per line)
    if '\n' in content:
        first_line = content.split('\n')[0].strip()
        if first_line.startswith('{') and first_line.endswith('}'):
            try:
                json.loads(first_line)
                return "jsonl"
            except json.JSONDecodeError:
                pass

    # Check for CSV/TSV
    if ',' in content or '\t' in content:
        try:
            reader = csv.DictReader([content.split('\n')[0]])
            if reader.fieldnames:
                if '\t' in content.split('\n')[0]:
                    return "tsv"
                return "csv"
        except Exception:
            pass

    return "unknown"


def convert_dataset(
    content: str,
    format: str | None = None,
    **kwargs
) -> list[dict]:
    """
    Auto-convert dataset to ChatML format.

    Args:
        content: Raw dataset content
        format: Optional format hint ('csv', 'tsv', 'json', 'jsonl', 'alpaca', 'sharegpt')
        **kwargs: Format-specific options

    Returns:
        List of ChatML-formatted entries

    Raises:
        ConversionError: If conversion fails
    """
    # Auto-detect format if not specified
    if format is None:
        format = detect_format(content)
        logger.info(f"Detected format: {format}")

    # Convert based on format
    converters: dict[str, Callable] = {
        "csv": convert_csv,
        "tsv": convert_tsv,
        "json": convert_json,
        "jsonl": convert_jsonl,
        "alpaca": convert_alpaca,
        "sharegpt": convert_sharegpt,
    }

    converter = converters.get(format)
    if converter is None:
        raise ConversionError(f"Unknown format: {format}")

    return converter(content, **kwargs)


# Export functions
def export_to_csv(entries: list[dict], text_column: str = "text") -> str:
    """Export ChatML to CSV format."""
    rows = []

    for entry in entries:
        messages = entry.get("messages", [])
        user_msg = ""
        assistant_msg = ""

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                user_msg = content
            elif role == "assistant":
                assistant_msg = content

        if user_msg and assistant_msg:
            # Include as instruction + output
            rows.append({
                "instruction": user_msg[:500],  # Truncate for CSV
                "input": "",
                "output": assistant_msg[:2000],
            })
        elif assistant_msg:
            rows.append({text_column: assistant_msg})

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return output.getvalue()


def export_to_alpaca(entries: list[dict]) -> str:
    """Export ChatML to Alpaca format."""
    rows = []

    for entry in entries:
        messages = entry.get("messages", [])
        instruction = ""
        input_text = ""
        output = ""

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                if not instruction:
                    instruction = content
                else:
                    input_text = content
            elif role == "assistant":
                output = content

        if output:
            rows.append({
                "instruction": instruction[:500],
                "input": input_text[:500],
                "output": output[:2000],
            })

    return json.dumps(rows, indent=2, ensure_ascii=False)


def export_to_sharegpt(entries: list[dict]) -> str:
    """Export ChatML to ShareGPT format."""
    rows = []

    for entry in entries:
        messages = entry.get("messages", [])
        conversations = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Map ChatML roles to ShareGPT
            from_role = "human" if role == "user" else "gpt"
            conversations.append({"from": from_role, "value": content})

        if conversations:
            rows.append({"conversations": conversations})

    return json.dumps(rows, indent=2, ensure_ascii=False)


# Import io for StringIO
import io
