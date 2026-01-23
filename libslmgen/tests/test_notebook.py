#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for notebook generation module.

Covers:
- Notebook JSON validity
- LoRA target correctness per model
- Base64 dataset round-trip
- Gated vs non-gated behavior
"""

import json
import base64
from pathlib import Path

# Import with path adjustment for test environment
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.notebook import generate_notebook
from core.registry import (
    get_lora_targets,
    _DEFAULT_LORA_TARGETS,
)


def _make_sample_dataset(n: int = 10) -> str:
    """Create a sample JSONL dataset string."""
    lines = []
    for i in range(n):
        entry = {
            "messages": [
                {"role": "user", "content": f"Question {i}"},
                {"role": "assistant", "content": f"Answer {i}"}
            ]
        }
        lines.append(json.dumps(entry))
    return "\n".join(lines)


class TestNotebookJSONValidity:
    """Test that generated notebooks are valid JSON."""
    
    def test_notebook_is_valid_json(self):
        """Generated notebook should be valid JSON."""
        dataset = _make_sample_dataset(50)
        notebook_json = generate_notebook(
            dataset_jsonl=dataset,
            model_id="microsoft/Phi-4-mini-instruct",
            model_name="Phi-4 Mini",
            model_size="3.8B",
            task_type="qa",
            num_examples=50,
            is_gated=False,
        )
        
        # Should not raise
        notebook = json.loads(notebook_json)
        assert isinstance(notebook, dict)
    
    def test_notebook_has_required_structure(self):
        """Notebook should have nbformat structure."""
        dataset = _make_sample_dataset(50)
        notebook_json = generate_notebook(
            dataset_jsonl=dataset,
            model_id="microsoft/Phi-4-mini-instruct",
            model_name="Phi-4 Mini",
            model_size="3.8B",
            task_type="qa",
            num_examples=50,
            is_gated=False,
        )
        
        notebook = json.loads(notebook_json)
        
        # Required Jupyter notebook fields
        assert "nbformat" in notebook
        assert "cells" in notebook
        assert "metadata" in notebook
        assert notebook["nbformat"] == 4
        assert isinstance(notebook["cells"], list)
        assert len(notebook["cells"]) > 0
    
    def test_cells_have_proper_structure(self):
        """Each cell should have correct structure."""
        dataset = _make_sample_dataset(50)
        notebook_json = generate_notebook(
            dataset_jsonl=dataset,
            model_id="microsoft/Phi-4-mini-instruct",
            model_name="Phi-4 Mini",
            model_size="3.8B",
            task_type="qa",
            num_examples=50,
            is_gated=False,
        )
        
        notebook = json.loads(notebook_json)
        
        for cell in notebook["cells"]:
            assert "cell_type" in cell
            assert cell["cell_type"] in ("code", "markdown")
            assert "source" in cell
            assert isinstance(cell["source"], list)


class TestLoRATargetCorrectness:
    """Test LoRA target mappings for different model architectures."""
    
    def test_phi_models_get_correct_targets(self):
        """Phi-3/4 models should get standard targets (gate/up/down) not fc1/fc2."""
        targets = get_lora_targets("microsoft/Phi-4-mini-instruct")
        # Phi-4 uses Llama architecture style
        assert "gate_proj" in targets
        assert "up_proj" in targets
        assert "down_proj" in targets
    
    def test_gemma_models_get_correct_targets(self):
        """Gemma models should NOT get gate_proj/up_proj/down_proj."""
        targets = get_lora_targets("google/gemma-2-2b-it")
        assert "q_proj" in targets
        assert "k_proj" in targets
        assert "v_proj" in targets
        assert "o_proj" in targets
        # Gemma doesn't have MLP gate/up/down exposed for LoRA
        assert "gate_proj" not in targets
        assert "up_proj" not in targets
        assert "down_proj" not in targets
    
    def test_llama_models_get_correct_targets(self):
        """Llama models should get standard targets including gate_proj."""
        targets = get_lora_targets("meta-llama/Llama-3.2-3B-Instruct")
        assert "q_proj" in targets
        assert "gate_proj" in targets
        assert "up_proj" in targets
        assert "down_proj" in targets
    
    def test_mistral_models_get_correct_targets(self):
        """Mistral models should get standard targets."""
        targets = get_lora_targets("mistralai/Mistral-7B-Instruct-v0.3")
        assert "gate_proj" in targets
    
    def test_qwen_models_get_correct_targets(self):
        """Qwen models should get standard targets."""
        targets = get_lora_targets("Qwen/Qwen2.5-3B-Instruct")
        assert "gate_proj" in targets
    
    def test_unknown_model_gets_default(self):
        """Unknown models should get default targets."""
        targets = get_lora_targets("some-unknown/model-name")
        assert targets == _DEFAULT_LORA_TARGETS


class TestBase64RoundTrip:
    """Test that embedded dataset survives base64 encoding."""
    
    def test_dataset_survives_encoding(self):
        """Dataset should be recoverable from notebook."""
        original_dataset = _make_sample_dataset(20)
        notebook_json = generate_notebook(
            dataset_jsonl=original_dataset,
            model_id="microsoft/Phi-4-mini-instruct",
            model_name="Phi-4 Mini",
            model_size="3.8B",
            task_type="qa",
            num_examples=20,
            is_gated=False,
        )
        
        notebook = json.loads(notebook_json)
        
        # Find the cell with embedded dataset
        dataset_cell = None
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                if "DATASET_B64" in source:
                    dataset_cell = source
                    break
        
        assert dataset_cell is not None
        
        # Extract the base64 string
        import re
        match = re.search(r'DATASET_B64 = "([^"]+)"', dataset_cell)
        assert match is not None
        
        b64_content = match.group(1)
        decoded = base64.b64decode(b64_content).decode()
        
        assert decoded == original_dataset


class TestGatedModelBehavior:
    """Test that gated models get HuggingFace login cell."""
    
    def test_gated_model_has_login_cell(self):
        """Gated models should include HuggingFace login cell."""
        dataset = _make_sample_dataset(50)
        notebook_json = generate_notebook(
            dataset_jsonl=dataset,
            model_id="meta-llama/Llama-3.2-3B-Instruct",
            model_name="Llama 3.2 3B",
            model_size="3B",
            task_type="qa",
            num_examples=50,
            is_gated=True,  # Explicitly marked gated
        )
        
        notebook = json.loads(notebook_json)
        
        # Should have a cell mentioning HuggingFace login
        all_content = " ".join(
            "".join(cell["source"]) for cell in notebook["cells"]
        )
        assert "huggingface" in all_content.lower() or "login" in all_content.lower()
    
    def test_non_gated_model_no_login_cell(self):
        """Non-gated models should not require login."""
        dataset = _make_sample_dataset(50)
        notebook_json = generate_notebook(
            dataset_jsonl=dataset,
            model_id="microsoft/Phi-4-mini-instruct",
            model_name="Phi-4 Mini",
            model_size="3.8B",
            task_type="qa",
            num_examples=50,
            is_gated=False,
        )
        
        notebook = json.loads(notebook_json)
        
        # Should NOT have "login()" call in code cells
        code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
        login_found = any(
            "login()" in "".join(cell["source"]) 
            for cell in code_cells
        )
        assert not login_found
