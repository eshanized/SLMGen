#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Presets Router.

Training presets configuration.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.training_presets import (
    PRESETS,
    get_preset,
    list_presets,
    get_recommended_preset,
    get_notebook_config,
    get_default_targets,
    TrainingPreset,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/presets", tags=["Training Presets"])


class PresetInfo(BaseModel):
    """Preset information."""
    key: str
    name: str
    description: str
    use_case: str


class PresetDetail(BaseModel):
    """Full preset details."""
    key: str
    name: str
    description: str
    use_case: str
    
    # LoRA
    lora_rank: int
    lora_alpha: int
    lora_dropout: float
    
    # Training
    learning_rate: float
    num_epochs: int
    batch_size: int
    gradient_accumulation: int
    max_seq_length: int
    
    # Optimization
    warmup_steps: int
    scheduler: str
    optimizer: str
    
    # Quantization
    load_in_4bit: bool
    bnb_4bit_quant_type: str


class PresetListResponse(BaseModel):
    """List of presets."""
    presets: list[PresetInfo]


class PresetDetailResponse(BaseModel):
    """Single preset details."""
    preset: PresetDetail


class RecommendPresetRequest(BaseModel):
    """Recommend preset request."""
    model_size: str  # "3B", "7B", etc.
    dataset_size: int
    use_case: str = "general"


class RecommendPresetResponse(BaseModel):
    """Recommended preset."""
    preset_key: str
    preset_name: str
    reason: str


class NotebookConfigRequest(BaseModel):
    """Get notebook config request."""
    preset_key: str
    model_id: str
    dataset_size: int = 0


class NotebookConfigResponse(BaseModel):
    """Notebook configuration."""
    config: dict


class TargetsResponse(BaseModel):
    """Target modules."""
    model_key: str
    target_modules: list[str]


@router.get("/", response_model=PresetListResponse)
async def list_presets_endpoint():
    """List all available presets."""
    presets = [
        PresetInfo(
            key=key,
            name=preset.name,
            description=preset.description,
            use_case=preset.use_case,
        )
        for key, preset in PRESETS.items()
    ]
    
    return PresetListResponse(presets=presets)


@router.get("/{preset_key}", response_model=PresetDetailResponse)
async def get_preset_endpoint(preset_key: str):
    """Get preset details."""
    preset = get_preset(preset_key)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_key}")
    
    return PresetDetailResponse(
        preset=PresetDetail(
            key=preset.key,
            name=preset.name,
            description=preset.description,
            use_case=preset.use_case,
            lora_rank=preset.lora_rank,
            lora_alpha=preset.lora_alpha,
            lora_dropout=preset.lora_dropout,
            learning_rate=preset.learning_rate,
            num_epochs=preset.num_epochs,
            batch_size=preset.batch_size,
            gradient_accumulation=preset.gradient_accumulation,
            max_seq_length=preset.max_seq_length,
            warmup_steps=preset.warmup_steps,
            scheduler=preset.scheduler,
            optimizer=preset.optimizer,
            load_in_4bit=preset.load_in_4bit,
            bnb_4bit_quant_type=preset.bnb_4bit_quant_type,
        )
    )


@router.post("/recommend", response_model=RecommendPresetResponse)
async def recommend_preset_endpoint(request: RecommendPresetRequest):
    """Recommend a preset based on model and dataset."""
    preset_key = get_recommended_preset(
        model_size=request.model_size,
        dataset_size=request.dataset_size,
        use_case=request.use_case,
    )
    
    preset = get_preset(preset_key)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_key}")
    
    # Generate reason
    reason = ""
    if request.use_case == "edge":
        reason = "Optimized for mobile/edge with smallest rank"
    elif request.use_case == "code":
        reason = "Optimized for code generation"
    elif request.dataset_size < 100:
        reason = "Small dataset - quick demo mode"
    else:
        reason = "Production-ready settings"
    
    return RecommendPresetResponse(
        preset_key=preset_key,
        preset_name=preset.name,
        reason=reason,
    )


@router.post("/notebook-config", response_model=NotebookConfigResponse)
async def get_notebook_config_endpoint(request: NotebookConfigRequest):
    """Get training config for notebook."""
    config = get_notebook_config(
        preset_key=request.preset_key,
        model_id=request.model_id,
        dataset_size=request.dataset_size,
    )
    
    return NotebookConfigResponse(config=config)


@router.get("/targets/{model_key}", response_model=TargetsResponse)
async def get_targets_endpoint(model_key: str):
    """Get default LoRA targets for a model."""
    targets = get_default_targets(model_key)
    
    return TargetsResponse(
        model_key=model_key,
        target_modules=targets,
    )