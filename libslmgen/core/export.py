#!/usr/bin/env python3
"""
Export Pipeline.

Exports fine-tuned models to various formats.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExportConfig:
    """Export configuration."""
    format: str
    quantization: str = "Q4_K_M"
    base_model: str = ""
    adapter_path: str = ""


def get_system_prompt_template(model_id: str) -> str:
    """Get system prompt template for model."""
    model_lower = model_id.lower()

    templates = {
        "llama": "You are a helpful AI assistant.",
        "llama3": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{{system_prompt}}<|eot_id|>",
        "mistral": "<s>[INST] <<SYS>>\n{{system_prompt}}\n</SYS>>\n\n",
        "qwen": "<|im_start|>system\n{{system_prompt}}<|im_end|>\n",
        "gemma": "<bos><|start_header_id|>model<|end_header_id|>\n\n{{system_prompt}}<|eot_id|>",
        "phi": "<|system|>\n{{system_prompt}}<|end|>",
    }

    for key, template in templates.items():
        if key in model_lower:
            return template

    return "You are a helpful AI assistant."


def generate_ollama_modelfile(model_id: str, system_prompt: str = "", base_model_name: str = "") -> str:
    """Generate Ollama Modelfile."""
    system = system_prompt or "You are a helpful AI assistant."

    if not base_model_name:
        base_model_name = model_id.split("/")[-1].replace("-Instruct", "").replace("-Chat", "")

    template = get_system_prompt_template(model_id)
    template = template.replace("{{system_prompt}}", system)

    return f"""FROM {model_id}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_keep 2048

TEMPLATE \"\"\"{template}\"\"\"
"""


def generate_gguf_template(model_id: str) -> str:
    """Generate GGUF export instructions."""
    return f"""# GGUF Export for {model_id}

## Using llama.cpp

1. Install:
pip install llama-cpp-python

2. Convert:
python
from llama_cpp import LlamaConvert
converter = LlamaConvert(model_path="{model_id}")
converter.convert_merged("./model.gguf", quantize="Q4_K_M")

3. Run:
python
from llama_cpp import Llama
llm = Llama("./model.gguf")
result = llm("Your prompt")
"""


def generate_vllm_template(model_id: str) -> str:
    """Generate vLLM deployment."""
    return f"""# vLLM Deployment for {model_id}

1. Install: pip install vllm
2. Run: vllm serve {model_id} --dtype half --port 8000
3. Query via OpenAI API
"""


def generate_huggingface_push(model_id: str, adapter_name: str = "slmgen-finetuned") -> str:
    """Generate HuggingFace push instructions."""
    return f"""# Push to HuggingFace Hub

from transformers import AutoModelForCausalLM, PeftModel
base_model = AutoModelForCausalLM.from_pretrained("{model_id}")
model = PeftModel.from_pretrained(base_model, "./adapter/")
model.push_to_hub("{adapter_name}")
"""


def get_export_instructions(format: str, model_id: str, system_prompt: str = "") -> str:
    """Get export instructions."""
    generators = {
        "ollama": lambda: generate_ollama_modelfile(model_id, system_prompt),
        "gguf": lambda: generate_gguf_template(model_id),
        "vllm": lambda: generate_vllm_template(model_id),
        "hf": lambda: generate_huggingface_push(model_id),
    }

    generator = generators.get(format)
    if generator:
        return generator()

    return "# Unknown export format"


EXPORT_FORMATS = {
    "ollama": {"name": "Ollama", "description": "Local AI runner", "extension": "Modelfile"},
    "gguf": {"name": "GGUF", "description": "llama.cpp format", "extension": ".gguf"},
    "vllm": {"name": "vLLM", "description": "Inference server", "extension": "docker-compose.yml"},
    "hf": {"name": "HuggingFace", "description": "HF Hub", "extension": ""},
}


def list_export_formats() -> dict:
    """List all export formats."""
    return EXPORT_FORMATS.copy()
