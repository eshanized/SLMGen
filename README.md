# 🚀 SLMGEN - Small Language Model Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eshanized/slmgen/actions/workflows/ci.yml/badge.svg)](https://github.com/eshanized/slmgen/actions/workflows/ci.yml)

<div align="center">

![SLMGEN Landing Page](docs/images/screenshot_v2.png)

**Fine-tune SLMs. 2x faster. For free.**

[Live Demo](https://slmgen.vercel.app) · [API Docs](docs/API.md) · [User Guide](docs/USER_GUIDE.md)

</div>

---

## ✨ What is SLMGEN?

SLMGEN is a web application that automates SLM fine-tuning. Upload your JSONL dataset and receive ready-to-run Google Colab notebooks with Unsloth + LoRA optimization.

**Your Data → Best Model → Matched.** One notebook. Zero setup. Ready to train.

---

## 🎯 Core Features (V3.0.0)

| Feature | Description |
|---------|-------------|
| 📤 **Smart Upload** | Drag-and-drop JSONL with **Live Chat Preview** (min 50 examples) |
| 📊 **Quality Scoring** | Duplicate detection, consistency checks, 0-100% quality score |
| 🧠 **18 Model Support** | Qwen 3.5, Llama 3.3, DeepSeek V3, Phi-4, Gemma 3, SmolLM3 + more |
| 🎯 **100-Point Matching** | Task fit (50pts) + Deploy target (30pts) + Data traits (20pts) |
| 💻 **Training Simulator** | Real-time terminal simulation during generation phase |
| 📓 **Self-Contained Notebooks** | Dataset embedded as base64 - no file uploads needed |
| 🔄 **Dataset Converter** | CSV, TSV, JSON, Alpaca, ShareGPT → ChatML |
| ⚡ **Training Presets** | Quick Demo, Production, Edge, Code, Long Context |
| 📦 **Export Options** | Ollama, GGUF, vLLM, HuggingFace |

---

## 🧠 Advanced Intelligence Features

### Dataset Intelligence Layer
- **Personality Detection** - Infers tone, verbosity, technicality, strictness
- **Hallucination Risk** - Scores likelihood of model fabrication (0-1)
- **Confidence Score** - Measures training reliability via coverage/diversity

### Prompt & Behavior Engine
- **Behavior Composer** - Generate system prompts from trait sliders
- **Prompt Linter** - Detects contradictions, redundancy, ambiguity
- **Prompt Diff** - Semantic comparison between prompts

### Model Transparency
- **"Why This Model?"** - Strength/weakness deep dive per model
- **Failure Previews** - Synthetic failure cases before training
- **Model Card Generator** - Auto-generated deployment README

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2 |
| **Session Store** | In-Memory (Thread-safe TTL eviction, zero Redis dependency) |
| **Frontend** | Next.js 16, TypeScript, React 19, Framer Motion |
| **Design** | Tailwind CSS, JetBrains Mono, Everblush Theme |
| **Auth** | Supabase (Optional OAuth + Email, or local mock) |
| **Training** | Unsloth + LoRA on Google Colab (Free T4 & A100 tiers) |
| **Deployment** | Vercel (Frontend) + Render (Backend) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (or [uv](https://github.com/astral-sh/uv))
- Node.js 18+
- Supabase project *(optional — set `AUTH_DISABLED=true` for 100% local development without Supabase)*

### Backend

```bash
cd libslmgen

# Option A: Instant run with uv (recommended)
uv run uvicorn app.main:app --reload --port 8000

# Option B: Standard virtualenv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd slmgenui
npm install
cp .env.example .env.local  # Configure API URL + Supabase
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🎉

---

## 📁 Project Structure

```
slmgen/
├── libslmgen/                  # Python Backend
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── session_store.py    # Thread-safe in-memory session store
│   │   ├── models.py           # Pydantic data schemas
│   │   ├── config.py           # Environment & settings
│   │   └── routers/            # API endpoints
│   │       ├── upload.py       # Dataset upload & validation
│   │       ├── analyze.py      # Dataset analysis
│   │       ├── recommend.py    # Model recommendation
│   │       ├── generate.py     # Notebook generation
│   │       ├── convert.py      # Dataset format conversion (CSV, JSON, Alpaca, ShareGPT)
│   │       ├── presets.py      # Training presets (Quick Demo, Production, etc.)
│   │       ├── export.py       # Model export guides (Ollama, GGUF, vLLM)
│   │       ├── advanced.py     # Intelligence features
│   │       └── jobs.py         # Job history (Supabase)
│   └── core/
│       ├── ingest.py           # JSONL parsing & validation
│       ├── quality.py          # Quality scoring
│       ├── analyzer.py         # Dataset analysis
│       ├── recommender.py      # 100-point scoring engine + GPU tiering
│       ├── notebook.py         # Jupyter notebook generator
│       ├── convert.py          # Format converters
│       ├── training_presets.py # Hyperparameter presets
│       ├── export.py           # Export template generator
│       ├── personality.py      # Personality detection
│       ├── risk.py             # Hallucination risk
│       ├── confidence.py       # Training confidence
│       ├── behavior.py         # Behavior composer
│       ├── prompt_linter.py    # Prompt linting
│       └── model_card.py       # README generator
├── slmgenui/                   # Next.js 16 Frontend
│   └── src/
│       ├── app/                # Pages (dashboard, login, signup, history, settings)
│       ├── components/         # UI components & charts
│       ├── lib/                # API client & types
│       └── hooks/              # React hooks (with sessionStorage persistence)
├── docs/
│   ├── API.md                  # API reference
│   ├── USER_GUIDE.md           # User guide
│   └── DEPLOY.md               # Deployment guide
└── supabase/
    └── schema.sql              # Database schema
```

---

## 📊 Supported Models (V3.0.0)

| Model | Size | Context | Colab GPU Tier | Best For | Gated |
|-------|------|---------|----------------|----------|-------|
| **DeepSeek V3** | 84B | 64K | A100 (Pro) | MoE reasoning, complex QA | ❌ |
| **Llama 3.3 70B** | 70B | 128K | A100 (Pro) | SOTA quality, reasoning | ✅ |
| **Qwen 3.5 32B** | 32B | 64K | A100 (Pro) | Hybrid thinking, coding | ❌ |
| **Mistral Small 3**| 24B | 131K | A100 (Pro) | Code, 128K context | ❌ |
| **Qwen 2.5 14B** | 14B | 32K | A100 (Pro) | Long context, reasoning | ❌ |
| **Llama 3.3 8B** | 8B | 128K | T4 (Free) | General purpose, 128K context | ✅ |
| **Mistral 7B** | 7B | 32K | T4 (Free) | Creative generation, QA | ❌ |
| **Qwen 3 4B** | 4B | 32K | T4 (Free) | Thinking mode, math, code | ❌ |
| **Gemma 3 4B** | 4B | 131K | T4 (Free) | Multimodal, long context | ✅ |
| **Phi-4 Mini** | 3.8B | 16K | T4 (Free) | Classification, extraction | ❌ |
| **SmolLM3 3B** | 3B | 128K | T4 (Free) | Multilingual, edge-ready | ❌ |
| **Llama 3.2 3B** | 3B | 8K | T4 (Free) | Fast Q&A, conversations | ✅ |
| **Qwen 2.5 3B** | 3B | 32K | T4 (Free) | Multilingual, JSON output | ❌ |
| **Gemma 2 2B** | 2B | 8K | T4 (Free) | Edge, mobile, browser | ✅ |
| **SmolLM2 1.7B** | 1.7B | 8K | T4 (Free) | Ultra-compact, low memory | ❌ |
| **Llama 3.2 1B** | 1B | 8K | T4 (Free) | Lightweight mobile | ✅ |
| **TinyLlama** | 1.1B | 2K | T4 (Free) | Minimal compute demos | ❌ |

---

## 📦 Dataset Format

Each line in your JSONL file should be a conversation:

```json
{"messages": [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there!"}]}
{"messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

**Requirements:**
- ✅ Minimum 50 examples
- ✅ At least one user and one assistant message
- ✅ UTF-8 encoding
- ✅ Valid JSON per line

---

## 🌐 Deployment

### Vercel (Frontend)
```bash
npx vercel --prod
```

### Render (Backend)
Uses `render.yaml` blueprint for auto-deployment.

See [DEPLOY.md](docs/DEPLOY.md) for full instructions.

---

## ⚙️ Environment Variables

```bash
# Backend (.env)
ALLOWED_ORIGINS=https://slmgen.vercel.app,http://localhost:3000
SESSION_TTL_SECONDS=1800
AUTH_DISABLED=true  # Set to true for zero-setup local dev without Supabase

# Optional: Supabase (for persistent job history and user authentication)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Optional: HuggingFace Token (for validating gated models like Llama/Gemma)
HF_TOKEN=hf_...

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 👥 Authors

**Vedant Singh Rajput**
- 🐙 [@vedanthq](https://github.com/vedanthq)

**Eshan Roy**
- 📧 eshanized@proton.me
- 🐙 [@eshanized](https://github.com/eshanized)

---

<div align="center">

**⭐ Star this repo if SLMGEN helped you fine-tune faster!**

</div>
