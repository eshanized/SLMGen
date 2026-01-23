# SLMGEN User Guide

**Generate fine-tuning notebooks for Small Language Models in minutes.**

---

## Quick Start

### 1. Sign Up / Login

Visit [localhost:3000/signup](http://localhost:3000/signup) to create an account or login with GitHub.

### 2. Upload Dataset

- Click **Get Started** on the dashboard
- Drag and drop your JSONL file or click to browse (supports live client-side chat preview for first 10KB)
- Required format: ChatML with `messages` array

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### 3. Review Analysis

After upload, you'll see:
- **Total Examples** - Number of training examples
- **Total Tokens** - Approximate token count
- **Quality Score** - Dataset quality rating (0-100%)

### 4. Select Task Type

Choose your fine-tuning goal:
- **Instruction Following** - General task completion
- **Chat/Conversation** - Multi-turn dialogue
- **Code Generation** - Programming tasks
- **Summarization** - Text condensation
- **Classification** - Category assignment

### 5. Choose Deployment Target

Where will your model run?
- **Cloud (A100/H100)** - Maximum performance
- **Cloud (T4/L4)** - Budget-friendly GPU
- **Edge/Mobile** - Optimized for devices
- **CPU Only** - No GPU required

### 6. Get Recommendations

SLMGEN analyzes your dataset and requirements to recommend the best models:
- **Score** - Overall fit percentage
- **VRAM** - GPU memory required
- **Training Time** - Estimated duration

### 7. Configure Training

Select a preset:
- **Fast** (~15 min) - Quick experimentation
- **Balanced** (~45 min) - Best for most cases
- **Quality** (~2 hours) - Maximum quality

Or customize:
- LoRA Rank, Learning Rate, Epochs, Batch Size, etc.

### 8. Generate Notebook

Click **Generate Notebook** to create your Colab notebook.

During generation, you'll see a **Training Terminal Simulator** that visualizes the Unsloth training commands in real-time. Once complete, a **Success Confetti** celebration confirms your notebook is ready.

Options:
- **Open in Colab** - Start training immediately
- **Download** - Save locally

---

## Dataset Format

### ChatML (Recommended)

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 2+2?"},
    {"role": "assistant", "content": "2+2 equals 4."}
  ]
}
```

### Tips for Quality Data

1. **Minimum 100 examples** for basic fine-tuning
2. **1,000+ examples** recommended for best results
3. **Consistent formatting** across all examples
4. **Include system prompts** for better control
5. **Mix easy and hard examples** for robustness

---

## Model Selection Guide

| Model | Size | Best For | VRAM |
|-------|------|----------|------|
| Phi-4 Mini | 3.8B | Instruction, Reasoning | 8GB |
| Llama 3.2 | 1-3B | General, Chat | 4-8GB |
| Gemma 2 | 2B | Efficient fine-tuning | 4GB |
| Qwen 2.5 | 3B | Multilingual | 8GB |
| DeepSeek Coder | 1.3B | Code generation | 4GB |

---

## Training Presets

### Fast
- LoRA Rank: 8
- Learning Rate: 5e-4
- Epochs: 1
- Time: ~15 minutes

### Balanced
- LoRA Rank: 16
- Learning Rate: 2e-4
- Epochs: 3
- Time: ~45 minutes

### Quality
- LoRA Rank: 32
- Learning Rate: 1e-4
- Epochs: 5
- Time: ~2 hours

---

## Export Options

After training, export your model to:

- **HuggingFace Hub** - Share publicly or privately
- **ONNX** - For edge deployment
- **Ollama** - Run locally with Ollama
- **GGUF** - Quantized for llama.cpp

---

## Troubleshooting

### "Dataset quality score is low"

- Check for duplicate examples
- Ensure consistent message formatting
- Add more diverse examples

### "Out of memory during training"

- Reduce batch size
- Lower LoRA rank
- Use a smaller model
- Enable gradient checkpointing

### "Model not converging"

- Increase epochs
- Reduce learning rate
- Check data quality

---

## Support

- GitHub: [github.com/eshanized/slmgen](https://github.com/eshanized/slmgen)
- Email: eshanized@proton.me
