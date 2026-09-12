#!/usr/bin/env python3
"""
Preview Router.

Provides dataset preview and analysis endpoints.
Uses storage to load datasets when not in session memory.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import json
from collections import Counter

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.session_store import session_store
from app.storage import storage_service

router = APIRouter(prefix="/preview", tags=["preview"])


# ============================================
# MODELS
# ============================================

class ExamplePreview(BaseModel):
    index: int
    messages: list[dict[str, str]]
    token_count: int


class FieldDistribution(BaseModel):
    roles: dict[str, int]
    avg_message_length: float
    token_distribution: dict[str, int]  # buckets: 0-100, 100-500, 500-1000, 1000+
    has_system_prompts: bool
    multi_turn_percentage: float


class DuplicateInfo(BaseModel):
    count: int
    examples: list[int]  # indices of duplicate examples


class PreviewResponse(BaseModel):
    examples: list[ExamplePreview]
    total_count: int
    page: int
    page_size: int


# ============================================
# HELPERS
# ============================================

async def _load_dataset(session_data: dict) -> list[dict]:
    """
    Load dataset from session or storage.

    Priority:
    1. raw_data in session (preferred - already in memory)
    2. Download from storage using dataset_path
    """
    raw_data = session_data.get("raw_data")
    if raw_data and isinstance(raw_data, list):
        return raw_data

    dataset_path = session_data.get("dataset_path")
    if dataset_path:
        try:
            file_bytes = await storage_service.download_file(dataset_path)
            content = file_bytes.decode("utf-8")
            # Parse JSONL
            dataset = []
            for line in content.strip().split("\n"):
                line = line.strip()
                if line:
                    dataset.append(json.loads(line))
            return dataset
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load dataset from storage: {e}"
            )

    raise HTTPException(
        status_code=404,
        detail="Dataset not found in session or storage"
    )


# ============================================
# ENDPOINTS
# ============================================

@router.get("/{session_id}", response_model=PreviewResponse)
async def get_preview(
    session_id: str,
    page: int = 1,
    page_size: int = 5
):
    """
    Get a paginated preview of dataset examples.

    Datasets are loaded from session memory (if cached) or from
    object storage (if needed).
    """
    page = max(page, 1)
    if page_size < 1:
        page_size = 1
    elif page_size > 100:
        page_size = 100

    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        dataset = await _load_dataset(session.get("data", {}))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load dataset: {e}"
        )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset is empty"
        )

    total = len(dataset)
    start = (page - 1) * page_size
    end = start + page_size

    examples = []
    for i, example in enumerate(dataset[start:end], start=start):
        messages = example.get("messages", [])
        text = " ".join(m.get("content", "") for m in messages)
        token_count = int(len(text.split()) * 1.3)

        examples.append(ExamplePreview(
            index=i,
            messages=messages,
            token_count=token_count
        ))

    return PreviewResponse(
        examples=examples,
        total_count=total,
        page=page,
        page_size=page_size
    )


@router.get("/{session_id}/distribution", response_model=FieldDistribution)
async def get_distribution(session_id: str):
    """
    Get field distribution statistics for the dataset.

    Analyzes role distribution, message lengths, and multi-turn patterns.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        dataset = await _load_dataset(session.get("data", {}))
    except HTTPException:
        raise

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset is empty"
        )

    role_counts: Counter = Counter()
    message_lengths: list[int] = []
    token_buckets = {"0-100": 0, "100-500": 0, "500-1000": 0, "1000+": 0}
    has_system = False
    multi_turn_count = 0

    for example in dataset:
        messages = example.get("messages", [])

        for msg in messages:
            role = msg.get("role", "unknown")
            role_counts[role] += 1

            content = msg.get("content", "")
            message_lengths.append(len(content))

            if role == "system":
                has_system = True

        total_text = " ".join(m.get("content", "") for m in messages)
        tokens = int(len(total_text.split()) * 1.3)

        if tokens < 100:
            token_buckets["0-100"] += 1
        elif tokens < 500:
            token_buckets["100-500"] += 1
        elif tokens < 1000:
            token_buckets["500-1000"] += 1
        else:
            token_buckets["1000+"] += 1

        user_msgs = sum(1 for m in messages if m.get("role") == "user")
        if user_msgs > 1:
            multi_turn_count += 1

    avg_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
    multi_turn_pct = (multi_turn_count / len(dataset) * 100) if dataset else 0

    return FieldDistribution(
        roles=dict(role_counts),
        avg_message_length=round(avg_length, 1),
        token_distribution=token_buckets,
        has_system_prompts=has_system,
        multi_turn_percentage=round(multi_turn_pct, 1)
    )


@router.get("/{session_id}/duplicates", response_model=DuplicateInfo)
async def check_duplicates(session_id: str):
    """
    Check for duplicate examples in the dataset.

    Uses a simple hash-based approach to detect near-duplicates.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        dataset = await _load_dataset(session.get("data", {}))
    except HTTPException:
        raise

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset is empty"
        )

    seen: dict[str, list[int]] = {}

    for i, example in enumerate(dataset):
        messages = example.get("messages", [])
        hash_key = str([(m.get("role"), m.get("content", "")[:100]) for m in messages])

        if hash_key in seen:
            seen[hash_key].append(i)
        else:
            seen[hash_key] = [i]

    duplicate_indices = []
    for indices in seen.values():
        if len(indices) > 1:
            duplicate_indices.extend(indices[1:])

    return DuplicateInfo(
        count=len(duplicate_indices),
        examples=duplicate_indices[:20]
    )
