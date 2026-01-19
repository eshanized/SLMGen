#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverse Prompt Inference.

Infers what kind of system prompt would likely produce the responses
in the training dataset. Helps users understand their data's implicit behavior.

FIX: C1 - Implementing missing module from spec.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import re
import logging
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class InferredPrompt:
    """Result of reverse prompt inference."""
    suggested_prompt: str
    output_structure: str  # "free_text", "json", "code", "list", "mixed"
    prompt_style: str  # "instructional", "conversational", "task_focused"
    task_intent: str  # "qa", "generation", "classification", "extraction", "chat"
    confidence: float  # 0.0 - 1.0
    reasoning: list[str]


def _detect_output_structure(responses: list[str]) -> tuple[str, str]:
    """
    Detect the predominant output structure from responses.
    Returns (structure_type, reasoning).
    """
    if not responses:
        return "free_text", "No responses to analyze"
    
    json_count = 0
    code_count = 0
    list_count = 0
    
    for resp in responses[:100]:  # Sample for efficiency
        resp_stripped = resp.strip()
        
        # Check for JSON-like structure
        if resp_stripped.startswith(("{", "[")) and resp_stripped.endswith(("}", "]")):
            json_count += 1
        
        # Check for code blocks
        if "```" in resp or re.search(r"^(def |class |function |import |from )", resp, re.M):
            code_count += 1
        
        # Check for list structure
        if re.search(r"^[\d\-\*\•]\s", resp, re.M):
            list_count += 1
    
    total = len(responses[:100])
    
    if total == 0:
        return "free_text", "No responses in sample to analyze"
    
    if json_count / total > 0.5:
        return "json", f"{int(json_count/total*100)}% of responses are JSON-structured"
    elif code_count / total > 0.3:
        return "code", f"{int(code_count/total*100)}% of responses contain code"
    elif list_count / total > 0.4:
        return "list", f"{int(list_count/total*100)}% of responses use list format"
    
    return "free_text", "Responses are primarily free-form text"


def _detect_prompt_style(data: list[dict]) -> tuple[str, str]:
    """
    Infer the implied prompt style from conversation patterns.
    Returns (style, reasoning).
    """
    if not data:
        return "conversational", "No data to analyze"
    
    # Check first user message patterns
    first_messages = []
    for entry in data[:100]:
        messages = entry.get("messages", [])
        for msg in messages:
            if msg.get("role") == "user":
                first_messages.append(msg.get("content", "").lower())
                break
    
    if not first_messages:
        return "conversational", "No user messages found"
    
    # Count command-like patterns
    command_patterns = sum(1 for m in first_messages if re.match(r"^(write|create|generate|explain|list|describe|how|what|why)", m))
    question_patterns = sum(1 for m in first_messages if m.rstrip().endswith("?"))
    
    total = len(first_messages)
    
    if command_patterns / total > 0.6:
        return "instructional", f"{int(command_patterns/total*100)}% of queries are commands"
    elif question_patterns / total > 0.6:
        return "task_focused", f"{int(question_patterns/total*100)}% of queries are questions"
    
    return "conversational", "Mixed query patterns suggest conversational style"


def _detect_task_intent(data: list[dict], output_structure: str) -> tuple[str, str]:
    """
    Infer the primary task intent from data patterns.
    Returns (intent, reasoning).
    """
    if not data:
        return "chat", "No data to analyze"
    
    # Analyze response patterns
    responses = []
    for entry in data[:100]:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                responses.append(msg.get("content", ""))
    
    if not responses:
        return "chat", "No assistant responses found"
    
    # JSON output strongly suggests extraction
    if output_structure == "json":
        return "extraction", "JSON output structure indicates structured extraction task"
    
    # Code output suggests generation
    if output_structure == "code":
        return "generation", "Code output indicates code generation task"
    
    # Check for classification-like patterns
    short_responses = sum(1 for r in responses if len(r.split()) < 20)
    if short_responses / len(responses) > 0.7:
        return "classification", f"{int(short_responses/len(responses)*100)}% of responses are short (classification-like)"
    
    # Check for Q&A patterns (responses with explanations)
    explanatory = sum(1 for r in responses if "because" in r.lower() or "therefore" in r.lower())
    if explanatory / len(responses) > 0.3:
        return "qa", f"{int(explanatory/len(responses)*100)}% of responses contain explanations"
    
    return "chat", "Responses follow general conversational patterns"


def _generate_prompt_from_patterns(
    output_structure: str,
    prompt_style: str,
    task_intent: str,
    responses: list[str]
) -> str:
    """Generate a suggested system prompt based on detected patterns."""
    
    # Base template
    base = "You are a helpful AI assistant."
    
    # Add task-specific instruction
    task_instructions = {
        "qa": "Answer questions clearly and provide explanations when helpful.",
        "generation": "Generate high-quality content based on user requests.",
        "classification": "Provide clear, concise categorizations or decisions.",
        "extraction": "Extract and structure information in the requested format.",
        "chat": "Engage naturally in conversation while being helpful.",
    }
    task_line = task_instructions.get(task_intent, task_instructions["chat"])
    
    # Add output format instruction
    format_instructions = {
        "json": "Respond with properly formatted JSON when appropriate.",
        "code": "Provide clean, well-commented code with explanations.",
        "list": "Use clear lists and bullet points to organize information.",
        "free_text": "",
    }
    format_line = format_instructions.get(output_structure, "")
    
    # Add style instruction
    style_instructions = {
        "instructional": "Follow user instructions precisely and completely.",
        "task_focused": "Focus on directly addressing the user's questions.",
        "conversational": "Be friendly and conversational in your responses.",
    }
    style_line = style_instructions.get(prompt_style, "")
    
    # Analyze response length patterns for verbosity hint
    if responses:
        avg_len = sum(len(r) for r in responses[:50]) / len(responses[:50])
        if avg_len < 200:
            verbosity = "Keep responses concise and to the point."
        elif avg_len > 800:
            verbosity = "Provide thorough, detailed responses."
        else:
            verbosity = ""
    else:
        verbosity = ""
    
    # Combine into prompt
    parts = [base, "", task_line]
    if format_line:
        parts.append(format_line)
    if style_line:
        parts.append(style_line)
    if verbosity:
        parts.append(verbosity)
    
    return "\n".join(p for p in parts if p)


def infer_reverse_prompt(data: list[dict]) -> InferredPrompt:
    """
    Infer what system prompt would produce the responses in this dataset.
    
    This is a heuristic-based analysis that helps users understand
    the implicit behavior their dataset encodes.
    
    LIMITATIONS:
    - This is inference, not ground truth
    - Complex behaviors may not be accurately captured
    - Works best with consistent, well-structured datasets
    
    Returns deterministic results for the same input.
    """
    logger.info(f"Inferring reverse prompt from {len(data)} examples")
    
    if len(data) < 10:
        return InferredPrompt(
            suggested_prompt="You are a helpful AI assistant.",
            output_structure="unknown",
            prompt_style="unknown",
            task_intent="unknown",
            confidence=0.2,
            reasoning=["Insufficient data for reliable inference (need 10+ examples)"],
        )
    
    # Collect all assistant responses
    responses = []
    for entry in data:
        for msg in entry.get("messages", []):
            if msg.get("role") == "assistant":
                responses.append(msg.get("content", ""))
    
    # Run detections
    reasoning = []
    
    output_structure, struct_reason = _detect_output_structure(responses)
    reasoning.append(f"Output: {struct_reason}")
    
    prompt_style, style_reason = _detect_prompt_style(data)
    reasoning.append(f"Style: {style_reason}")
    
    task_intent, intent_reason = _detect_task_intent(data, output_structure)
    reasoning.append(f"Intent: {intent_reason}")
    
    # Generate suggested prompt
    suggested_prompt = _generate_prompt_from_patterns(
        output_structure, prompt_style, task_intent, responses
    )
    
    # Calculate confidence based on data size and pattern clarity
    size_factor = min(1.0, len(data) / 200)  # Max at 200 examples
    pattern_clarity = 0.7  # Base confidence in pattern detection
    confidence = round(size_factor * pattern_clarity, 2)
    
    logger.info(f"Inferred prompt style: {prompt_style}, intent: {task_intent}, confidence: {confidence}")
    
    return InferredPrompt(
        suggested_prompt=suggested_prompt,
        output_structure=output_structure,
        prompt_style=prompt_style,
        task_intent=task_intent,
        confidence=confidence,
        reasoning=reasoning,
    )
