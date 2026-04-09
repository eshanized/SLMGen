#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Training Presets.

Pre-configured training configurations for different use cases.
Quick Demo, Production, Edge Optimize, and Custom presets.

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TrainingPreset:
    """Training preset configuration."""
    key: str
    name: str
    description: str
    
    # LoRA settings
    lora_rank: int
    lora_alpha: int
    lora_dropout: float
    
    # Training settings
    learning_rate: float
    num_epochs: int
    batch_size: int
    gradient_accumulation: int
    max_seq_length: int
    
    # Optimization
    warmup_steps: int
    scheduler: str  # "cosine", "linear", "constant"
    optimizer: str  # "adamw_torch", "adamw_8bit", "paged_adamw_32bit"
    
    # Target modules
    target_modules: Optional[list[str]] = None
    
    # Quantization
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "bfloat16"
    
    # Use cases
    use_case: str = "general"


# Define presets
PRESETS: dict[str, TrainingPreset] = {
    "quick_demo": TrainingPreset(
        key="quick_demo",
        name="Quick Demo",
        description="Fast testing with minimal resources. 1 epoch, small rank.",
        lora_rank=16,
        lora_alpha=32,
        lora_dropout=0.05,
        learning_rate=2e-4,
        num_epochs=1,
        batch_size=2,
        gradient_accumulation=4,
        max_seq_length=512,
        warmup_steps=10,
        scheduler="cosine",
        optimizer="adamw_8bit",
        use_case="testing",
    ),
    "production": TrainingPreset(
        key="production",
        name="Production",
        description="Full training with best quality. 3 epochs, larger rank.",
        lora_rank=32,
        lora_alpha=64,
        lora_dropout=0.05,
        learning_rate=1e-4,
        num_epochs=3,
        batch_size=4,
        gradient_accumulation=2,
        max_seq_length=2048,
        warmup_steps=100,
        scheduler="cosine",
        optimizer="adamw_torch",
        use_case="production",
    ),
    "edge_optimize": TrainingPreset(
        key="edge_optimize",
        name="Edge Optimize",
        description="Maximum compression for mobile/edge deployment.",
        lora_rank=8,
        lora_alpha=16,
        lora_dropout=0.1,
        learning_rate=3e-4,
        num_epochs=2,
        batch_size=1,
        gradient_accumulation=8,
        max_seq_length=512,
        warmup_steps=20,
        scheduler="linear",
        optimizer="paged_adamw_32bit",
        use_case="edge",
    ),
    "long_context": TrainingPreset(
        key="long_context",
        name="Long Context",
        description="For datasets with 8K+ token sequences.",
        lora_rank=16,
        lora_alpha=32,
        lora_dropout=0.05,
        learning_rate=1e-4,
        num_epochs=2,
        batch_size=1,
        gradient_accumulation=8,
        max_seq_length=8192,
        warmup_steps=50,
        scheduler="cosine",
        optimizer="adamw_8bit",
        use_case="long_context",
    ),
    "code_finetune": TrainingPreset(
        key="code_finetune",
        name="Code Fine-tune",
        description="Optimized for code generation tasks.",
        lora_rank=24,
        lora_alpha=48,
        lora_dropout=0.05,
        learning_rate=1.5e-4,
        num_epochs=3,
        batch_size=2,
        gradient_accumulation=4,
        max_seq_length=2048,
        warmup_steps=50,
        scheduler="cosine",
        optimizer="adamw_8bit",
        use_case="code",
    ),
}


def get_preset(key: str) -> Optional[TrainingPreset]:
    """Get a preset by key."""
    return PRESETS.get(key)


def list_presets() -> dict[str, TrainingPreset]:
    """List all available presets."""
    return PRESETS.copy()


def get_default_targets(model_key: str) -> list[str]:
    """Get default LoRA target modules for a model."""
    # Common target modules by model family
    targets_by_family = {
        "llama": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "mistral": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "qwen": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "gemma": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "phi": ["q_proj", "k_proj", "v_proj", "o_proj", "fc1", "fc2"],
        "smollm": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "deepseek": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    }
    
    model_key_lower = model_key.lower()
    for family, targets in targets_by_family.items():
        if family in model_key_lower:
            return targets
    
    # Default fallback
    return ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def get_recommended_preset(
    model_size: str,
    dataset_size: int,
    use_case: str = "general",
) -> str:
    """
    Get recommended preset based on model size and dataset.
    
    Args:
        model_size: Model size in billions (e.g., "3B", "7B")
        dataset_size: Number of training examples
        use_case: Specific use case override
    
    Returns:
        Preset key
    """
    # Parse model size
    if "B" in model_size:
        size_num = float(model_size.replace("B", ""))
    else:
        size_num = 1.0
    
    # Determine preset
    if use_case == "edge":
        return "edge_optimize"
    elif use_case == "code":
        return "code_finetune"
    elif use_case == "long_context":
        return "long_context"
    elif dataset_size < 100:
        # Small dataset
        return "quick_demo"
    elif size_num > 14:
        # Large model (14B+) - use fewer resources
        return "quick_demo"
    elif dataset_size < 500:
        # Medium dataset
        return "production"
    else:
        # Large dataset - can afford more epochs
        return "production"


def get_notebook_config(
    preset_key: str,
    model_id: str,
    dataset_size: int = 0,
) -> dict:
    """
    Generate notebook cell config for a preset.
    
    Returns dict ready to insert in notebook template.
    """
    preset = get_preset(preset_key)
    if preset is None:
        preset = get_preset("production")
    
    targets = get_default_targets(model_id)
    
    # If model is larger than 14B, use smaller seq length
    max_seq = preset.max_seq_length
    if "70B" in model_id or "84B" in model_id or "32B" in model_id:
        max_seq = min(max_seq, 1024)
    
    return {
        "lora_rank": preset.lora_rank,
        "lora_alpha": preset.lora_alpha,
        "lora_dropout": preset.lora_dropout,
        "learning_rate": preset.learning_rate,
        "num_epochs": preset.num_epochs,
        "batch_size": preset.batch_size,
        "gradient_accumulation": preset.gradient_accumulation,
        "max_seq_length": max_seq,
        "warmup_steps": preset.warmup_steps,
        "scheduler": preset.scheduler,
        "optimizer": preset.optimizer,
        "target_modules": targets,
        "load_in_4bit": preset.load_in_4bit,
    }


# Backward compatibility
def get_quick_preset() -> TrainingPreset:
    """Get quick demo preset."""
    return PRESETS["quick_demo"]


def get_production_preset() -> TrainingPreset:
    """Get production preset."""
    return PRESETS["production"]


def get_edge_preset() -> TrainingPreset:
    """Get edge optimize preset."""
    return PRESETS["edge_optimize"]