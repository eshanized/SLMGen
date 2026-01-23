#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Colab Notebook Generator.

Creates complete, self-contained Jupyter notebooks for fine-tuning SLMs.
The dataset is base64-encoded and embedded directly in the notebook,
so users don't need to do any file management.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import json
import base64
import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from core.registry import get_lora_targets

logger = logging.getLogger(__name__)

# Setup Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def _estimate_training_time(model_size: str, num_examples: int) -> int:
    """
    Estimate training time in minutes on T4 GPU.
    """
    base_times = {
        "1B": 5,
        "1.1B": 5,
        "1.3B": 6,
        "1.7B": 7,
        "2B": 8,
        "3B": 12,
        "3.8B": 15,
        "7B": 25,
    }
    # Get base time or default to 15 for unknown sizes
    base = base_times.get(model_size, 15)
    
    # Scale by dataset size (100 examples = 1x scale)
    scale = num_examples / 100
    
    # 3 epochs by default
    return int(base * scale * 3)


def generate_notebook(
    dataset_jsonl: str,
    model_id: str,
    model_name: str,
    model_size: str,
    task_type: str,
    num_examples: int,
    is_gated: bool,
) -> str:
    """
    Generate a complete Jupyter notebook for fine-tuning using Jinja2 templates.
    """
    logger.info(f"Generating notebook for {model_name} with {num_examples} examples")
    
    # Encode dataset as Base64
    dataset_b64 = base64.b64encode(dataset_jsonl.encode()).decode()
    
    # Get model-specific config
    lora_targets = get_lora_targets(model_id)
    training_time = _estimate_training_time(model_size, num_examples)
    
    # Prepare context for template
    context = {
        "model_name": model_name,
        "model_id": model_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "num_examples": f"{num_examples:,}",
        "task_type": task_type.replace("_", " ").title(),
        "training_time": training_time,
        "is_gated": is_gated,
        "dataset_b64": dataset_b64,
        "lora_targets": str(lora_targets),
    }
    
    # Render template
    template = env.get_template("notebook.json.j2")
    notebook_json = template.render(**context)
    
    logger.info("Notebook generated successfully")
    return notebook_json
