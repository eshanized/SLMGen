"""
Preview Router.

Provides dataset preview and analysis endpoints.

@author Eshan Roy <eshanized@proton.me>
@license MIT
@copyright 2026 Eshan Roy
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from collections import Counter

from app.session import session_manager

router = APIRouter(prefix="/preview", tags=["preview"])


# ============================================
# MODELS
# ============================================

class ExamplePreview(BaseModel):
    index: int
    messages: List[Dict[str, str]]
    token_count: int


class FieldDistribution(BaseModel):
    roles: Dict[str, int]
    avg_message_length: float
    token_distribution: Dict[str, int]  # buckets: 0-100, 100-500, 500-1000, 1000+
    has_system_prompts: bool
    multi_turn_percentage: float


class DuplicateInfo(BaseModel):
    count: int
    examples: List[int]  # indices of duplicate examples


class PreviewResponse(BaseModel):
    examples: List[ExamplePreview]
    total_count: int
    page: int
    page_size: int


# ============================================
# ENDPOINTS
# ============================================

@router.get("/{session_id}", response_model=PreviewResponse)
async def get_preview(
    session_id: str,
    page: int = 1,
    page_size: int = 5
):
    """Get a paginated preview of dataset examples."""
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    elif page_size > 100:
        page_size = 100
    
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    dataset = session.raw_data
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found in session"
        )
    
    total = len(dataset)
    start = (page - 1) * page_size
    end = start + page_size
    
    examples = []
    for i, example in enumerate(dataset[start:end], start=start):
        messages = example.get("messages", [])
        # Estimate token count (rough approximation)
        text = " ".join(m.get("content", "") for m in messages)
        token_count = len(text.split()) * 1.3  # rough estimate
        
        examples.append(ExamplePreview(
            index=i,
            messages=messages,
            token_count=int(token_count)
        ))
    
    return PreviewResponse(
        examples=examples,
        total_count=total,
        page=page,
        page_size=page_size
    )


@router.get("/{session_id}/distribution", response_model=FieldDistribution)
async def get_distribution(session_id: str):
    """Get field distribution statistics for the dataset."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    dataset = session.raw_data
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found in session"
        )
    
    # Analyze roles
    role_counts: Counter = Counter()
    message_lengths: List[int] = []
    token_buckets = {"0-100": 0, "100-500": 0, "500-1000": 0, "1000+": 0}
    has_system = False
    multi_turn_count = 0
    
    for example in dataset:
        messages = example.get("messages", [])
        
        # Count roles
        for msg in messages:
            role = msg.get("role", "unknown")
            role_counts[role] += 1
            
            content = msg.get("content", "")
            message_lengths.append(len(content))
            
            if role == "system":
                has_system = True
        
        # Token bucket (per example)
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
        
        # Multi-turn detection
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
    """Check for duplicate examples in the dataset."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    dataset = session.raw_data
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found in session"
        )
    
    # Create hashes of examples
    seen: Dict[str, List[int]] = {}
    
    for i, example in enumerate(dataset):
        messages = example.get("messages", [])
        # Create a simple hash
        hash_key = str([(m.get("role"), m.get("content", "")[:100]) for m in messages])
        
        if hash_key in seen:
            seen[hash_key].append(i)
        else:
            seen[hash_key] = [i]
    
    # Find duplicates
    duplicate_indices = []
    for indices in seen.values():
        if len(indices) > 1:
            duplicate_indices.extend(indices[1:])  # Keep first, mark rest as duplicates
    
    return DuplicateInfo(
        count=len(duplicate_indices),
        examples=duplicate_indices[:20]  # Return first 20 duplicate indices
    )
