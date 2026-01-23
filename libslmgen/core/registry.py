#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Registry Module.

Provides dynamic model metadata fetching from Hugging Face Hub
while ensuring compatibility with Unsloth's supported architectures.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import RepositoryNotFoundError, GatedRepoError

logger = logging.getLogger(__name__)

# Unsloth-compatible architectures
# These are the model architectures that Unsloth can optimize
SUPPORTED_ARCHITECTURES = frozenset([
    "LlamaForCausalLM",
    "MistralForCausalLM", 
    "Phi3ForCausalLM",
    "PhiForCausalLM",
    "Qwen2ForCausalLM",
    "GemmaForCausalLM",
    "Gemma2ForCausalLM",
    "GPTNeoXForCausalLM",  # TinyLlama uses this
    "StableLmForCausalLM",
    "DeepseekForCausalLM",
    "InternLM2ForCausalLM",
])


@dataclass
class ModelInfo:
    """Validated model information from Hugging Face."""
    model_id: str
    name: str
    architecture: str
    context_window: int
    is_gated: bool
    downloads: int
    likes: int
    is_compatible: bool
    compatibility_reason: str


class ModelRegistry:
    """
    Registry for validating and fetching model metadata from Hugging Face.
    
    This class provides:
    - Validation of model IDs against Hugging Face Hub
    - Architecture compatibility checking with Unsloth
    - Caching of model metadata to reduce API calls
    """
    
    def __init__(self):
        self.api = HfApi()
        self._cache: dict[str, ModelInfo] = {}
    
    def validate_model(self, model_id: str) -> ModelInfo:
        """
        Validate a Hugging Face model ID and return its metadata.
        
        Args:
            model_id: The Hugging Face model ID (e.g., "meta-llama/Llama-3.2-3B")
            
        Returns:
            ModelInfo with validation results
            
        Raises:
            ValueError: If model doesn't exist on Hugging Face
        """
        # Check cache first
        if model_id in self._cache:
            return self._cache[model_id]
        
        try:
            # Fetch model info from HF
            model_info = self.api.model_info(model_id)
        except RepositoryNotFoundError:
            raise ValueError(f"Model '{model_id}' not found on Hugging Face Hub")
        except GatedRepoError:
            # Model exists but is gated - we can still use it
            logger.info(f"Model {model_id} is gated, fetching limited info")
            return self._create_gated_model_info(model_id)
        except Exception as e:
            logger.error(f"Error fetching model info for {model_id}: {e}")
            raise ValueError(f"Failed to fetch model info: {e}")
        
        # Extract architecture from config
        architecture = self._get_architecture(model_id, model_info)
        
        # Check compatibility
        is_compatible = architecture in SUPPORTED_ARCHITECTURES
        compatibility_reason = (
            f"✅ Architecture '{architecture}' is supported by Unsloth"
            if is_compatible
            else f"⚠️ Architecture '{architecture}' may not be optimized by Unsloth"
        )
        
        # Get context window
        context_window = self._get_context_window(model_id, model_info)
        
        # Build result
        result = ModelInfo(
            model_id=model_id,
            name=model_info.id.split("/")[-1] if "/" in model_info.id else model_info.id,
            architecture=architecture,
            context_window=context_window,
            is_gated=model_info.gated if hasattr(model_info, 'gated') else False,
            downloads=model_info.downloads or 0,
            likes=model_info.likes or 0,
            is_compatible=is_compatible,
            compatibility_reason=compatibility_reason,
        )
        
        # Cache the result
        self._cache[model_id] = result
        return result
    
    def _get_architecture(self, model_id: str, model_info) -> str:
        """Extract model architecture from config."""
        # Try to get from model card config
        if hasattr(model_info, 'config') and model_info.config:
            config = model_info.config
            if hasattr(config, 'architectures') and config.architectures:
                return config.architectures[0]
        
        # Try to fetch config.json directly
        try:
            import json
            config_path = hf_hub_download(
                repo_id=model_id,
                filename="config.json",
                local_dir_use_symlinks=False,
            )
            with open(config_path, 'r') as f:
                config = json.load(f)
                if 'architectures' in config and config['architectures']:
                    return config['architectures'][0]
        except Exception as e:
            logger.warning(f"Could not fetch config.json for {model_id}: {e}")
        
        return "Unknown"
    
    def _get_context_window(self, model_id: str, model_info) -> int:
        """Extract context window from model config."""
        # Try from config
        if hasattr(model_info, 'config') and model_info.config:
            config = model_info.config
            # Try common attribute names
            for attr in ['max_position_embeddings', 'max_seq_length', 'n_positions']:
                if hasattr(config, attr):
                    return getattr(config, attr)
        
        # Try to fetch config.json directly  
        try:
            import json
            config_path = hf_hub_download(
                repo_id=model_id,
                filename="config.json",
                local_dir_use_symlinks=False,
            )
            with open(config_path, 'r') as f:
                config = json.load(f)
                for key in ['max_position_embeddings', 'max_seq_length', 'n_positions']:
                    if key in config:
                        return config[key]
        except Exception:
            pass
        
        return 4096  # Default fallback
    
    def _create_gated_model_info(self, model_id: str) -> ModelInfo:
        """Create ModelInfo for gated models with limited access."""
        return ModelInfo(
            model_id=model_id,
            name=model_id.split("/")[-1] if "/" in model_id else model_id,
            architecture="Unknown (gated)",
            context_window=4096,  # Conservative default
            is_gated=True,
            downloads=0,
            likes=0,
            is_compatible=True,  # Assume compatible if gated
            compatibility_reason="⚠️ Gated model - requires HF token for full validation",
        )
    
    def is_compatible(self, model_id: str) -> tuple[bool, str]:
        """
        Quick check if a model is compatible with Unsloth.
        
        Returns:
            Tuple of (is_compatible, reason)
        """
        try:
            info = self.validate_model(model_id)
            return info.is_compatible, info.compatibility_reason
        except ValueError as e:
            return False, str(e)


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Get or create the global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


@lru_cache(maxsize=100)
def validate_hf_model(model_id: str) -> ModelInfo:
    """
    Validate a Hugging Face model ID (cached).
    
    This is a convenience function that uses the global registry.
    """
    return get_registry().validate_model(model_id)


def check_compatibility(model_id: str) -> tuple[bool, str]:
    """
    Check if a model ID is compatible with Unsloth.
    
    Returns:
        Tuple of (is_compatible, reason_message)
    """
    return get_registry().is_compatible(model_id)
