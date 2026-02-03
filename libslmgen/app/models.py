#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic Models and Schemas.

Defines all the data structures used across the API.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """What kind of Task the model should be trained for."""
    CLASSIFY = "classify"
    QA = "qa"
    CONVERSATION = "conversation"
    GENERATION = "generation"
    EXTRACTION = "extraction"


class DeploymentTarget(str, Enum):
    """Where the trained model will Run."""
    CLOUD = "cloud"
    MOBILE = "mobile"
    EDGE = "edge"
    BROWSER = "browser"
    DESKTOP = "desktop"
    SERVER = "server"


class DatasetStats(BaseModel):
    """Statistics about the uploaded Dataset."""
    total_examples: int = Field(..., description="Number of conversation Examples")
    total_tokens: int = Field(..., description="Rough token Count estimate")
    avg_tokens_per_example: int = Field(..., description="Average tokens per Example")
    single_turn_pct: int = Field(..., description="Percentage of single-turn convos")
    multi_turn_pct: int = Field(..., description="Percentage of multi-turn Convos")
    has_system_prompts: bool = Field(..., description="Whether dataset has system Prompts")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score 0-1")
    quality_issues: list[str] = Field(default_factory=list, description="List of Issues found")


class DatasetCharacteristics(BaseModel):
    """Detailed characteristics for model Selection."""
    is_multilingual: bool = False
    avg_response_length: int = 0
    looks_like_json: bool = False
    is_multi_turn: bool = False
    has_system_prompts: bool = False
    dominant_language: str = "en"


class ModelRecommendation(BaseModel):
    """A single model Recommendation."""
    model_id: str = Field(..., description="HuggingFace model ID")
    model_name: str = Field(..., description="Human-readable Name")
    size: str = Field(..., description="Model size like 2B, 3B, 7B")
    score: float = Field(..., ge=0.0, le=100.0, description="Recommendation score 0-100")
    reasons: list[str] = Field(default_factory=list, description="Why we picked this Model")
    context_window: int = Field(..., description="Max context length")
    is_gated: bool = Field(default=False, description="Requires HF login")


class RecommendationResponse(BaseModel):
    """Full recommendation response with Primary and alternatives."""
    primary: ModelRecommendation
    alternatives: list[ModelRecommendation] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response after uploading a Dataset."""
    session_id: str
    stats: DatasetStats
    message: str = "Dataset uploaded successfully!"


class AnalyzeRequest(BaseModel):
    """Request to analyze a Session dataset."""
    session_id: str


class AnalyzeResponse(BaseModel):
    """Detailed analysis of the Dataset."""
    session_id: str
    stats: DatasetStats
    characteristics: DatasetCharacteristics


class RecommendRequest(BaseModel):
    """Request for model Recommendations."""
    session_id: str
    task: TaskType
    deployment: DeploymentTarget


class GenerateRequest(BaseModel):
    """Request to generate a Training notebook."""
    session_id: str
    model_id: Optional[str] = None  # if None, use the primary Recommendation


class NotebookResponse(BaseModel):
    """Response after generating a Notebook."""
    session_id: str
    notebook_filename: str
    download_url: str
    colab_url: Optional[str] = None  # only if GitHub token Configured
    message: str = "Notebook generated successfully!"


# =============================================================================
# Training Progress Tracking Models
# =============================================================================


class TrainingStatusEnum(str, Enum):
    """Status of a training session."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingEventRequest(BaseModel):
    """Webhook payload from Colab notebook."""
    session_id: str
    step: int
    loss: float
    epoch: int = 0
    learning_rate: float = 0.0
    grad_norm: Optional[float] = None
    tokens_per_second: Optional[float] = None
    gpu_memory_used: Optional[float] = None


class TrainingStartRequest(BaseModel):
    """Request to start a training session."""
    session_id: str
    job_id: str
    model_id: str
    total_steps: int
    total_epochs: int = 1


class TrainingCompleteRequest(BaseModel):
    """Request to mark training as completed."""
    session_id: str
    error: Optional[str] = None  # If set, marks as failed


class TrainingEventResponse(BaseModel):
    """A single training event."""
    step: int
    loss: float
    epoch: int
    learning_rate: float
    timestamp: str
    grad_norm: Optional[float] = None
    tokens_per_second: Optional[float] = None
    gpu_memory_used: Optional[float] = None


class TrainingStatusResponse(BaseModel):
    """Current training session status."""
    session_id: str
    job_id: str
    model_id: str
    status: TrainingStatusEnum
    total_steps: int
    total_epochs: int
    current_step: int
    current_epoch: int
    progress_percent: float
    latest_loss: Optional[float] = None
    eta_seconds: Optional[float] = None
    eta_formatted: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    event_count: int = 0
