# 🚀 SLMGEN - Small Language Model Generator

<div align="center">

![SLMGEN Landing Page](docs/images/screenshot.png)

**Fine-tune SLMs. 2x faster. For free.**

[Live Demo](https://slmgen.vercel.app) · [API Docs](docs/API.md) · [User Guide](docs/USER_GUIDE.md)

</div>

---

## ✨ What is SLMGEN?

SLMGEN is a production-ready web application that automates SLM fine-tuning. Upload your JSONL dataset and receive ready-to-run Google Colab notebooks with Unsloth + LoRA optimization.

**Your Data → Best Model → Matched.** One notebook. Zero setup. Ready to train.

---

## 🎯 Core Features

| Feature | Description |
|---------|-------------|
| 📤 **Smart Upload** | Drag-and-drop JSONL with instant validation (min 50 examples) |
| 📊 **Quality Scoring** | Duplicate detection, consistency checks, 0-100% quality score |
| 🧠 **11 Model Support** | Phi-4, Llama 3.2, Gemma 2, Qwen 2.5, Mistral 7B + more |
| 🎯 **100-Point Matching** | Task fit (50pts) + Deploy target (30pts) + Data traits (20pts) |
| 📓 **Self-Contained Notebooks** | Dataset embedded as base64 - no file uploads needed |
| ☁️ **6 Deploy Targets** | Cloud, Server, Desktop, Edge, Mobile, Browser |

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
| **Frontend** | Next.js 16, TypeScript, React 19 |
| **Auth** | Supabase (OAuth + Email) |
| **Training** | Unsloth + LoRA on Google Colab (Free T4) |
| **Deployment** | Vercel (Frontend) + Render (Backend) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase project

### Backend

```bash
cd libslmgen
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure Supabase keys
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
│   │   ├── routers/            # API endpoints
│   │   │   ├── upload.py       # Dataset upload
│   │   │   ├── analyze.py      # Dataset analysis
│   │   │   ├── recommend.py    # Model recommendation
│   │   │   ├── generate.py     # Notebook generation
│   │   │   ├── advanced.py     # Intelligence features
│   │   │   └── jobs.py         # Job history
│   │   └── session.py          # Thread-safe sessions
│   └── core/
│       ├── ingest.py           # JSONL parsing
│       ├── quality.py          # Quality scoring
│       ├── analyzer.py         # Dataset analysis
│       ├── recommender.py      # 100-point scoring engine
│       ├── notebook.py         # Jupyter generator
│       ├── personality.py      # Personality detection
│       ├── risk.py             # Hallucination risk
│       ├── confidence.py       # Training confidence
│       ├── behavior.py         # Behavior composer
│       ├── prompt_linter.py    # Prompt linting
│       └── model_card.py       # README generator
├── slmgenui/                   # Next.js Frontend
│   └── src/
│       ├── app/                # Pages (dashboard, login, signup)
│       ├── components/         # UI components
│       ├── lib/                # API client & types
│       └── hooks/              # React hooks (with persistence)
├── docs/
│   ├── API.md                  # API reference
│   ├── USER_GUIDE.md           # User guide
│   └── DEPLOY.md               # Deployment guide
└── supabase/
    └── schema.sql              # Database schema
```

---

## 📊 Supported Models

| Model | Size | Context | Best For | Gated |
|-------|------|---------|----------|-------|
| **Phi-4 Mini** | 3.8B | 16K | Classification, Extraction | ❌ |
| **Llama 3.2** | 1B/3B | 8K | Q&A, Conversations | ✅ |
| **Gemma 2** | 2B | 8K | Edge, Mobile | ✅ |
| **Qwen 2.5** | 0.5B-3B | 32K | Multilingual, JSON | ❌ |
| **Mistral 7B** | 7B | 32K | Generation, Creative | ❌ |
| **TinyLlama** | 1.1B | 2K | Ultra-lightweight | ❌ |
| **SmolLM2** | 135M-1.7B | 8K | Small devices | ❌ |

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
UPLOAD_DIR=/tmp/uploads
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
JWT_SECRET=your_jwt_secret

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=https://slmgen-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 👤 Author

**Eshan Roy**
- 📧 eshanized@proton.me
- 🐙 [@eshanized](https://github.com/eshanized)

---

<div align="center">

**⭐ Star this repo if SLMGEN helped you fine-tune faster!**

</div>
