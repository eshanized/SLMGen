#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Behavior Composer.

Generates system prompts from trait sliders.
Users can dial in the exact personality they want.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BehaviorConfig:
    """Configuration for composed behavior."""
    tone: int  # 0 (casual) to 100 (formal)
    depth: int  # 0 (brief) to 100 (thorough)
    risk_tolerance: int  # 0 (safe) to 100 (experimental)
    creativity: int  # 0 (factual) to 100 (creative)


@dataclass
class ComposedBehavior:
    """Result of behavior composition."""
    system_prompt: str
    explanation: str
    traits_summary: str


def _get_tone_phrase(tone: int) -> str:
    """Get tone directive based on slider value."""
    if tone < 20:
        return "Be casual and friendly, like chatting with a buddy"
    elif tone < 40:
        return "Be approachable but helpful"
    elif tone < 60:
        return "Be professional and clear"
    elif tone < 80:
        return "Be formal and precise in your communication"
    else:
        return "Maintain a highly professional, academic tone"


def _get_depth_phrase(depth: int) -> str:
    """Get depth directive based on slider value."""
    if depth < 20:
        return "Keep responses brief and to the point, just the essentials"
    elif depth < 40:
        return "Provide concise answers with key details"
    elif depth < 60:
        return "Give balanced explanations with reasonable detail"
    elif depth < 80:
        return "Provide thorough explanations with context"
    else:
        return "Give comprehensive, in-depth explanations with full context"


def _get_risk_phrase(risk: int) -> str:
    """Get risk tolerance directive based on slider value."""
    if risk < 20:
        return "Only provide well-established, verified information. Say 'I don't know' when uncertain"
    elif risk < 40:
        return "Stick to reliable information, clearly label any speculation"
    elif risk < 60:
        return "Balance accuracy with helpfulness"
    elif risk < 80:
        return "Feel free to speculate when helpful, but be transparent about it"
    else:
        return "Be bold and experimental, explore possibilities even if uncertain"


def _get_creativity_phrase(creativity: int) -> str:
    """Get creativity directive based on slider value."""
    if creativity < 20:
        return "Focus purely on facts and established knowledge"
    elif creativity < 40:
        return "Stay factual with occasional helpful examples"
    elif creativity < 60:
        return "Use examples and analogies to explain concepts"
    elif creativity < 80:
        return "Be creative in explanations, use metaphors and stories"
    else:
        return "Be highly creative and imaginative in your responses"


def compose_behavior(config: BehaviorConfig) -> ComposedBehavior:
    """
    Generate a system prompt from trait sliders.
    
    Each slider (0-100) controls a different aspect of behavior.
    The result is a coherent system prompt that reflects the user's preferences.
    """
    logger.info(f"Composing behavior: tone={config.tone}, depth={config.depth}, "
                f"risk={config.risk_tolerance}, creativity={config.creativity}")
    
    # Get phrase for each trait
    tone_phrase = _get_tone_phrase(config.tone)
    depth_phrase = _get_depth_phrase(config.depth)
    risk_phrase = _get_risk_phrase(config.risk_tolerance)
    creativity_phrase = _get_creativity_phrase(config.creativity)
    
    # Compose the system prompt
    prompt_parts = [
        "You are a helpful AI assistant.",
        "",
        f"**Communication Style:** {tone_phrase}.",
        "",
        f"**Response Depth:** {depth_phrase}.",
        "",
        f"**Accuracy & Risk:** {risk_phrase}.",
        "",
        f"**Creativity:** {creativity_phrase}.",
    ]
    
    system_prompt = "\n".join(prompt_parts)
    
    # Generate traits summary
    tone_label = "casual" if config.tone < 40 else "formal" if config.tone > 60 else "balanced"
    depth_label = "concise" if config.depth < 40 else "thorough" if config.depth > 60 else "moderate"
    risk_label = "safe" if config.risk_tolerance < 40 else "bold" if config.risk_tolerance > 60 else "balanced"
    creativity_label = "factual" if config.creativity < 40 else "creative" if config.creativity > 60 else "balanced"
    
    traits_summary = f"{tone_label}, {depth_label}, {risk_label}, {creativity_label}"
    
    # Generate explanation
    explanation = (
        f"This system prompt creates an assistant that's {tone_label} in tone, "
        f"gives {depth_label} responses, takes a {risk_label} approach to uncertainty, "
        f"and is {creativity_label} in its explanations."
    )
    
    logger.info(f"Composed behavior: {traits_summary}")
    
    return ComposedBehavior(
        system_prompt=system_prompt,
        explanation=explanation,
        traits_summary=traits_summary,
    )


def get_default_config() -> BehaviorConfig:
    """Get a balanced default configuration."""
    return BehaviorConfig(
        tone=50,
        depth=50,
        risk_tolerance=30,  # slightly conservative by default
        creativity=50,
    )
