# SLMGEN V3.0.0 Roadmap

## What's New in V3.0.0

- 🚀 **18 Models** - Including Qwen 3.5, Llama 3.3, DeepSeek V3
- 📊 **128K Context** - Extended context windows  
- ⚡ **Dataset Converter** - CSV, TSV, JSON, Alpaca, ShareGPT
- 🎯 **Training Presets** - Quick Demo, Production, Edge
- 📦 **Export Pipeline** - Ollama, GGUF, vLLM, HuggingFace
- ⚙️ **Simplified** - No Redis, in-memory storage only

---

## 🎯 Current Features (V3.0.0)

### Dataset Converter ✅
- [x] CSV/TSV ingestion
- [x] JSON (array format)
- [x] Alpaca format
- [x] ShareGPT format
- [x] Auto-detection
- [ ] Parquet support (V3.1)

### Training Presets ✅
- [x] Quick Demo mode
- [x] Production mode
- [x] Edge Optimize mode
- [x] Long Context mode
- [x] Code Fine-tune mode

### Export Pipeline ✅
- [x] Colab notebook (existing)
- [x] Ollama Modelfile
- [x] GGUF instructions
- [x] vLLM template
- [ ] Direct GGUF conversion (V3.1)

### Evaluation ✅
- [ ] MMLU benchmark runner (V3.2)
- [ ] HellaSwag benchmark (V3.2)
- [ ] Humaneval benchmark (V3.2)

---

## 📅 Phasing V3

### Phase 1: Converter + Export (V3.1)
1. Parquet support
2. Direct GGUF conversion
3. Batch conversion

### Phase 2: Evaluation (V3.2)
1. Benchmark runners
2. Training analytics
3. Model comparison

### Phase 3: Scale (V3.3)
1. Multi-dataset processing
2. CLI tool
3. Python SDK

---

## 📦 Supported Models V3.0.0

| Model | Size | Context | Architecture |
|------|------|---------|--------------|
| DeepSeek V3 | 84B | 64K | MoE |
| Llama 3.3 70B | 70B | 128K | Dense |
| Qwen 3.5 32B | 32B | 64K | Dense |
| Mistral Small 3 | 24B | 131K | MoE |
| Llama 3.3 8B | 8B | 128K | Dense |
| Qwen 2.5 14B | 14B | 32K | Dense |
| Qwen 3 | 4B | 32K | Dense |
| Gemma 3 | 4B | 128K | Dense |
| SmolLM3 | 3B | 128K | Dense |
| Phi-4 Mini | 3.8B | 16K | Dense |
| Llama 3.2 3B | 3B | 8K | Dense |
| Gemma 2 | 2B | 8K | Dense |
| Qwen 2.5 | 3B | 32K | Dense |
| Mistral | 7B | 32K | Dense |
| SmolLM2 | 1.7B | 8K | Dense |
| Llama 3.2 1B | 1B | 8K | Dense |
| DeepSeek Coder | 1.3B | 16K | Dense |
| Phi-3.5 Mini | 3.8B | 128K | Dense |

**Total: 18 models** (up from 11 in V1.x)

---

## ❌ Not Planned

- Inference Playground (paid API cost)
- Redis dependencies
- Background job queue
- Complex theme system

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01 | Initial release |
| 2.0.0 | 2026-04 | Simplified, removed Redis |
| 3.0.0 | 2026-04 | 18 models, converter, presets |

---

## Quick Start

```bash
# Backend
cd libslmgen
AUTH_DISABLED=true uvicorn app.main:app --reload --port 8000

# Frontend
cd slmgenui
npm run dev
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/convert` | POST | Convert dataset format |
| `/detect-format` | POST | Auto-detect format |
| `/export/generate` | POST | Generate export |
| `/presets/` | GET | List presets |
| `/presets/recommend` | POST | Recommend preset |