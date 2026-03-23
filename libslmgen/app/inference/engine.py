#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inference Engine.

Provides async inference capabilities using HuggingFace Inference API.
Supports real-time prompt testing against SLM models.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from core.recommender import MODELS

logger = logging.getLogger(__name__)

# HuggingFace Inference API base URL
HF_INFERENCE_API = "https://api-inference.huggingface.co/models"

# Default generation parameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TIMEOUT = 30.0  # seconds


@dataclass
class GenerationResult:
    """Result from a single inference call."""
    model_id: str
    output: str
    latency_ms: float
    tokens: int
    finish_reason: str
    error: Optional[str] = None


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout: float = DEFAULT_TIMEOUT
    do_sample: bool = True
    top_p: float = 0.9


class InferenceEngine:
    """
    Async inference engine using HuggingFace Inference API.
    
    Provides:
    - Single model inference
    - Parallel model comparison
    - Configurable parameters
    - Error handling with retries
    
    Usage:
        engine = InferenceEngine()
        
        # Single inference
        result = await engine.generate(
            model_id="microsoft/Phi-4-mini-instruct",
            prompt="What is machine learning?",
            system_prompt="You are a helpful assistant.",
        )
        
        # Parallel comparison
        results = await engine.generate_parallel(
            model_ids=["model1", "model2"],
            prompt="Hello!",
        )
    """
    
    def __init__(
        self,
        hf_token: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize inference engine.
        
        Args:
            hf_token: HuggingFace API token (optional, for gated models)
            timeout: Request timeout in seconds
        """
        self._hf_token = hf_token
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {}
            if self._hf_token:
                headers["Authorization"] = f"Bearer {self._hf_token}"
            
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers=headers,
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def generate(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None,
    ) -> GenerationResult:
        """
        Generate text from a model.
        
        Args:
            model_id: HuggingFace model ID
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration
            
        Returns:
            GenerationResult with output and metadata
        """
        if config is None:
            config = InferenceConfig()
        
        start_time = time.perf_counter()
        
        try:
            # Build messages format for chat models
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt,
                })
            messages.append({
                "role": "user",
                "content": prompt,
            })
            
            # Prepare request payload
            payload = {
                "inputs": messages,
                "parameters": {
                    "temperature": config.temperature,
                    "max_new_tokens": config.max_tokens,
                    "do_sample": config.do_sample,
                    "top_p": config.top_p,
                    "return_full_text": False,
                },
                "options": {
                    "use_cache": True,
                },
            }
            
            client = await self._get_client()
            url = f"{HF_INFERENCE_API}/{model_id}"
            
            response = await client.post(url, json=payload)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            if response.status_code == 503:
                # Model loading
                return GenerationResult(
                    model_id=model_id,
                    output="",
                    latency_ms=latency_ms,
                    tokens=0,
                    finish_reason="loading",
                    error="Model is loading. Please wait and retry.",
                )
            
            if response.status_code == 401:
                return GenerationResult(
                    model_id=model_id,
                    output="",
                    latency_ms=latency_ms,
                    tokens=0,
                    finish_reason="auth_error",
                    error="Authentication required. Please provide a valid HuggingFace token.",
                )
            
            if response.status_code == 422:
                # Try text input format for non-chat models
                text_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                payload = {
                    "inputs": text_prompt,
                    "parameters": {
                        "temperature": config.temperature,
                        "max_new_tokens": config.max_tokens,
                        "do_sample": config.do_sample,
                    },
                }
                
                response = await client.post(url, json=payload)
                latency_ms = (time.perf_counter() - start_time) * 1000
            
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response (may be string or list)
            if isinstance(data, list) and len(data) > 0:
                output = data[0].get("generated_text", str(data[0]))
            else:
                output = data.get("generated_text", str(data))
            
            # Estimate token count (rough approximation)
            tokens = len(output.split())
            
            return GenerationResult(
                model_id=model_id,
                output=output,
                latency_ms=round(latency_ms, 1),
                tokens=tokens,
                finish_reason="stop",
            )
            
        except httpx.TimeoutException:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Inference timeout for {model_id}")
            return GenerationResult(
                model_id=model_id,
                output="",
                latency_ms=latency_ms,
                tokens=0,
                finish_reason="timeout",
                error="Request timed out. Try again with a shorter prompt.",
            )
            
        except httpx.HTTPStatusError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Inference HTTP error for {model_id}: {e}")
            return GenerationResult(
                model_id=model_id,
                output="",
                latency_ms=latency_ms,
                tokens=0,
                finish_reason="error",
                error=f"HTTP error: {e.response.status_code}",
            )
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Inference error for {model_id}: {e}")
            return GenerationResult(
                model_id=model_id,
                output="",
                latency_ms=latency_ms,
                tokens=0,
                finish_reason="error",
                error=str(e),
            )
    
    async def generate_parallel(
        self,
        model_ids: list[str],
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None,
    ) -> list[GenerationResult]:
        """
        Generate text from multiple models in parallel.
        
        Args:
            model_ids: List of HuggingFace model IDs
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration
            
        Returns:
            List of GenerationResults (in same order as model_ids)
        """
        import asyncio
        
        tasks = [
            self.generate(model_id, prompt, system_prompt, config)
            for model_id in model_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to GenerationResult with error
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(GenerationResult(
                    model_id=model_ids[i],
                    output="",
                    latency_ms=0,
                    tokens=0,
                    finish_reason="error",
                    error=str(result),
                ))
            else:
                processed_results.append(result)
        
        return processed_results


# Global inference engine instance
_inference_engine: Optional[InferenceEngine] = None


def get_inference_engine() -> InferenceEngine:
    """Get or create the global inference engine."""
    global _inference_engine
    if _inference_engine is None:
        from app.config import settings
        hf_token = getattr(settings, 'hf_token', None) or None
        _inference_engine = InferenceEngine(hf_token=hf_token)
    return _inference_engine


async def shutdown_inference_engine() -> None:
    """Shutdown the global inference engine."""
    global _inference_engine
    if _inference_engine:
        await _inference_engine.close()
        _inference_engine = None
