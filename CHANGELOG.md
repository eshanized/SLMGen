# Changelog

All notable changes to the SLMGen project.

---

## [3.0.0] - 2026-04-15

### 🚀 Major Upgrades

- **18 Models Supported** - Added Qwen 3.5 (32B), Llama 3.3 (8B/70B), DeepSeek V3 (84B)
- **128K Context** - Extended context windows with new models
- **Version Bump** - Full V3.0.0 release

### ✨ New Features

#### 1. Dataset Converter (`/convert`)
- **CSV/TSV Import** - Convert spreadsheets to ChatML format
- **JSON Support** - Import JSON arrays and nested objects
- **Alpaca Format** - Convert from Alpaca training format
- **ShareGPT Format** - Convert from ShareGPT conversations
- **Auto-Detection** - Automatically detect input format
- **Export Back** - Convert ChatML to CSV/Alpaca/ShareGPT

#### 2. Training Presets (`/presets`)
- **Quick Demo** - Fast testing (1 epoch, r=16)
- **Production** - Full training (3 epochs, r=32)
- **Edge Optimize** - Mobile deployment (r=8, QLoRA)
- **Long Context** - 8K+ token sequences
- **Code Fine-tune** - Optimized for code generation

#### 3. Export Pipeline (`/export`)
- **Ollama Modelfile** - Generate deployable Modelfile
- **GGUF Instructions** - llama.cpp conversion guide
- **vLLM Template** - Docker deployment
- **HuggingFace Push** - Adapter upload instructions

### 🗑️ Removed (V2.0.0 Cleanup)

- Redis dependencies - Simplified to in-memory storage
- Inference Playground - Cost center removed
- Background Job Queue - Sync execution
- RQ/Redis packages

### 📦 Backend Changes

- `core/convert.py` - NEW Dataset converter
- `core/training_presets.py` - NEW Training configurations  
- `core/export.py` - NEW Export pipeline
- `app/routers/convert.py` - NEW Convert API
- `app/routers/export.py` - NEW Export API
- `app/routers/presets.py` - NEW Presets API
- Updated `app/config.py` - Version 3.0.0

### 🛡️ Maintenance & Stabilization Overhaul
- **Upload & Ingestion Pipeline Fixed** - Added `ingest_from_bytes` and `ingest_from_str` to `libslmgen/core/ingest.py`, resolving broken worker dependencies and restoring immediate synchronous dataset processing.
- **Missing Endpoints Restored** - Registered `presets.router` in `app/main.py` and fixed routing for `/presets`.
- **Advanced Intelligence Router Fixed** - Resolved undefined symbol errors (`compare_prompts`, `generate_model_card`) in `app/routers/advanced.py`.
- **Colab GPU Guardrails & VRAM Tiering** - Added automated GPU hardware tiering (`T4 (Free)` for models <10B vs `A100 (Colab Pro)` for heavy weights like 70B/84B MoE) in `recommender.py`, notebook generator `notebook.py`, and interactive UI badge in `model-card.tsx`.
- **Centralized Frontend API Configuration** - Consolidated scattered `NEXT_PUBLIC_API_URL` fallback definitions into exported `API_URL` in `src/lib/api.ts`.
- **Dead Code Pruned** - Removed dead inference playground & polling pipeline artifacts from frontend and backend.
- **Quality Gates & CI/CD** - Added `libslmgen/pyproject.toml`, resolved all ESLint and Ruff linter errors, added full integration test suite in `tests/test_routers.py` (60/60 tests passing), and updated GitHub Actions CI pipeline.
- **Makefile & DX Polish** - Added `make test` target, updated `requirements.txt` to V3.0.0, and updated `README.md` with `uv` quickstart instructions.

### 🎨 Frontend Changes

- Updated homepage to show 18 models
- New model cards for V3 models with GPU requirement badges
- Stats updated (18 models, 128K context)

---

## [2.0.0] - 2026-04-XX

### Cleanup Release

- Removed Redis dependency - Simple in-memory storage
- Removed Inference Playground
- Simplified architecture
- Lighter dependencies (\~47% fewer packages)

---

## [1.0.0] - 2026-01-23

### New Features

- **Live Dataset Chat Preview**
  - DataPreview component to visualize JSONL datasets as chat bubbles
  - Client-side parsing for instant feedback

- **Training Terminal Simulator**
  - TerminalSimulator component with typing animation
  - macOS-like terminal window with syntax highlighting

- **Success Confetti**
  - Confetti component using Framer Motion
  - Particle explosion on notebook generation

### UI/UX

- JetBrains Mono font
- Framer Motion animations
- About page redesign

### Technical

- Next.js configuration updates
- JSDoc documentation