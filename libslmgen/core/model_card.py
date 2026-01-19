#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Card Generator.

Auto-generates deployment documentation (README) for fine-tuned models.
Includes strengths, limitations, example prompts, and deployment notes.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ModelCard:
    """Generated model documentation."""
    title: str
    description: str
    markdown: str  # Full README content


def generate_model_card(
    model_name: str,
    model_id: str,
    task_type: str,
    num_examples: int,
    quality_score: float,
    personality_summary: str | None = None,
    risk_level: str | None = None,
) -> ModelCard:
    """
    Generate a complete model README/card.
    
    This gives users deployment-ready documentation
    without them having to write it themselves.
    """
    logger.info(f"Generating model card for {model_name}")
    
    # Build the markdown content
    title = f"Fine-tuned {model_name}"
    description = f"A fine-tuned version of {model_name} for {task_type} tasks."
    
    sections = []
    
    # Header
    sections.append(f"# {title}")
    sections.append("")
    sections.append(f"> {description}")
    sections.append("")
    sections.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d')}")
    sections.append(f"**Base Model:** [{model_id}](https://huggingface.co/{model_id})")
    sections.append(f"**Task:** {task_type.replace('_', ' ').title()}")
    sections.append(f"**Training Examples:** {num_examples:,}")
    sections.append("")
    
    # Model Details
    sections.append("## 📋 Model Details")
    sections.append("")
    sections.append("| Property | Value |")
    sections.append("|----------|-------|")
    sections.append(f"| Base Model | {model_name} |")
    sections.append(f"| Fine-tuning Method | LoRA (Low-Rank Adaptation) |")
    sections.append(f"| Training Framework | Unsloth + TRL |")
    sections.append(f"| Dataset Quality | {int(quality_score * 100)}% |")
    sections.append("")
    
    # Personality (if provided)
    if personality_summary:
        sections.append("## 🎭 Model Personality")
        sections.append("")
        sections.append(personality_summary)
        sections.append("")
    
    # Strengths
    sections.append("## ✅ Strengths")
    sections.append("")
    
    # Generate strengths based on task type
    if task_type in ["instruction_following", "qa", "generation"]:
        sections.append("- Follows instructions accurately")
        sections.append("- Provides helpful, relevant responses")
    if task_type in ["conversation", "chat"]:
        sections.append("- Natural conversational flow")
        sections.append("- Maintains context across turns")
    if task_type in ["code", "code_generation"]:
        sections.append("- Generates syntactically correct code")
        sections.append("- Understands common programming patterns")
    if task_type in ["classification", "classify"]:
        sections.append("- Consistent classification behavior")
        sections.append("- Clear category assignments")
    
    sections.append("- Trained on quality-checked data")
    sections.append("")
    
    # Limitations
    sections.append("## ⚠️ Limitations")
    sections.append("")
    sections.append("- May still hallucinate on unfamiliar topics")
    sections.append("- Knowledge limited to training data")
    sections.append("- Not suitable for high-stakes decisions without human review")
    
    if risk_level == "high":
        sections.append("- **Note:** Training data has elevated hallucination risk indicators")
    
    sections.append("")
    
    # Usage
    sections.append("## 🚀 Usage")
    sections.append("")
    sections.append("### With Transformers")
    sections.append("")
    sections.append("```python")
    sections.append("from transformers import AutoModelForCausalLM, AutoTokenizer")
    sections.append("from peft import PeftModel")
    sections.append("")
    sections.append(f'base_model = AutoModelForCausalLM.from_pretrained("{model_id}")')
    sections.append('model = PeftModel.from_pretrained(base_model, "path/to/lora_adapter")')
    sections.append(f'tokenizer = AutoTokenizer.from_pretrained("{model_id}")')
    sections.append("")
    sections.append('messages = [{"role": "user", "content": "Your prompt here"}]')
    sections.append("inputs = tokenizer.apply_chat_template(messages, return_tensors='pt')")
    sections.append("outputs = model.generate(inputs, max_new_tokens=256)")
    sections.append("print(tokenizer.decode(outputs[0]))")
    sections.append("```")
    sections.append("")
    
    # With Ollama
    sections.append("### With Ollama (if exported to GGUF)")
    sections.append("")
    sections.append("```bash")
    sections.append("ollama create my-model -f Modelfile")
    sections.append("ollama run my-model")
    sections.append("```")
    sections.append("")
    
    # Example Prompts
    sections.append("## 💬 Example Prompts")
    sections.append("")
    sections.append("Try these prompts to test your model:")
    sections.append("")
    sections.append("```")
    sections.append("User: Hello! What can you help me with?")
    sections.append("```")
    sections.append("")
    sections.append("```")
    sections.append("User: Explain this concept in simple terms.")
    sections.append("```")
    sections.append("")
    
    # Training Details
    sections.append("## 📊 Training Details")
    sections.append("")
    sections.append("```yaml")
    sections.append("training:")
    sections.append("  method: LoRA")
    sections.append("  rank: 16")
    sections.append("  alpha: 16")
    sections.append("  epochs: 3")
    sections.append("  learning_rate: 2e-4")
    sections.append("  batch_size: 2")
    sections.append("  optimizer: AdamW 8-bit")
    sections.append("```")
    sections.append("")
    
    # Footer
    sections.append("---")
    sections.append("")
    sections.append("*Generated by [SLMGEN](https://github.com/eshanized/slmgen)*")
    
    markdown = "\n".join(sections)
    
    logger.info(f"Model card generated ({len(markdown)} chars)")
    
    return ModelCard(
        title=title,
        description=description,
        markdown=markdown,
    )
