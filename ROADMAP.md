# SLMGEN V2 Roadmap

## 🚀 High-Impact Initiatives

### 1. Training Progress Tracking & Feedback Loop
**Goal**: Keep users engaged within the ecosystem during long training jobs.
- [x] Real-time training logs via webhook callbacks from Colab
- [x] Live loss curve visualization in the dashboard
- [ ] Training completion notifications (Email/Push)
- [x] Estimated time remaining prediction

### 2. Universal Dataset Converter
**Goal**: Remove friction by supporting any input format.
- [ ] Auto-detect and ingest CSV, TSV, JSON, Parquet
- [ ] Support popular formats: Alpaca, ShareGPT, OpenAI Fine-tuning
- [ ] Export to multiple standard formats
- [ ] Interactive column mapping UI

### 3. Inference Playground
**Goal**: Immediate validation of fine-tuned models.
- [ ] Hosted inference API (Free tier: ~10 req/day)
- [ ] Side-by-side comparison (Base Model vs. Fine-tuned)
- [ ] Shareable public demo links for stakeholders
- [ ] Prompt template testing

### 4. Intelligent Data Augmentation
**Goal**: Enable high-quality training even with small datasets.
- [ ] Paraphrase generation to expand dataset size
- [ ] Synthetic example generation based on existing patterns
- [ ] Back-translation for linguistic diversity
- [ ] Persona variation (e.g., convert "Formal" to "Casual")

### 5. One-Click Deployment Pipelines
**Goal**: seamlessly move from training to production.
- [ ] **Ollama**: Auto-generate `Modelfile` and GGUF quantization
- [ ] **vLLM/TGI**: Docker compose templates for self-hosting
- [ ] **HuggingFace**: Auto-push models with generated model cards
- [ ] **Replicate**: Auto-deploy as a scalable API endpoint

---

## 💡 Core Enhancements (Medium Impact)

### Model & Training
- [ ] **Custom Model Registry**: Support user-defined base models
- [ ] **Training Presets**: "Fast Demo" vs. "Production Quality" configurations
- [ ] **LoRA Adapter Gallery**: Public library of community fine-tunes
- [ ] **Eval Benchmarks**: Auto-run MMLU/HellaSwag on fine-tuned models

### Platform & UX
- [ ] **Dataset Versioning**: Track changes, rollback, and diff versions
- [ ] **Cost Estimator**: Calculator for Colab Pro/A100 compute costs
- [ ] **Bulk Operations**: Upload multiple datasets for comparison jobs
- [ ] **Dark/Light Mode**: Full theme support
- [ ] **Job Templates**: Save reusable configurations (Task + Deployment + Model)

### Developer Tools
- [ ] **SLMGEN CLI**: `slmgen upload data.jsonl --task qa --deploy edge`
- [ ] **Public API**: Programmatic access to analysis and recommendation engine

---

## 📅 Phasing Priority suggestion

### Phase 1: Ecosystem Loop (Months 1-2)
Focus on keeping the user engaged.
1. Training Progress Tracking
2. Inference Playground

### Phase 2: Friction Reduction (Months 3-4)
Focus on widening the funnel.
1. Universal Dataset Converter
2. Bulk Operations
3. CLI Tool

### Phase 3: value Expansion (Months 5+)
Focus on advanced capabilities.
1. Data Augmentation
2. One-Click Deployment Pipelines
