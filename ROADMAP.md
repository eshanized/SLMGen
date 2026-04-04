# SLMGEN V2.0.0 Roadmap

## What's New in V2.0.0

- ⚡ **Removed Redis dependency** - Simple in-memory storage
- 🚀 **Removed Inference Playground** - Keeps project lean
- 🔄 **Simplified architecture** - Easier to deploy
- 📦 **Lighter dependencies** - Faster installs

---

## 🚀 High-Impact Initiatives

### 1. Universal Dataset Converter
**Goal**: Remove friction by supporting any input format.
- [ ] Auto-detect and ingest CSV, TSV, JSON, Parquet
- [ ] Support popular formats: Alpaca, ShareGPT, OpenAI Fine-tuning
- [ ] Export to multiple standard formats
- [ ] Interactive column mapping UI

### 2. Training Completion Notifications
**Goal**: Keep users engaged during long training jobs.
- [ ] Email notifications on completion
- [ ] Push notifications
- [ ] Webhook integration

### 3. One-Click Deployment Pipelines
**Goal**: Seamlessly move from training to production.
- [ ] **Ollama**: Auto-generate `Modelfile` and GGUF quantization
- [ ] **vLLM/TGI**: Docker compose templates for self-hosting
- [ ] **HuggingFace**: Auto-push models with generated model cards

---

## 💡 Core Enhancements (Medium Impact)

### Model & Training
- [ ] **Training Presets**: "Fast Demo" vs. "Production Quality" configurations
- [ ] **Eval Benchmarks**: Auto-run MMLU/HellaSwag on fine-tuned models

### Platform & UX
- [ ] **Dataset Versioning**: Track changes, rollback, and diff versions
- [ ] **Cost Estimator**: Calculator for Colab Pro/A100 compute costs
- [ ] **Bulk Operations**: Upload multiple datasets for comparison jobs
- [ ] **Job Templates**: Save reusable configurations

### Developer Tools
- [ ] **SLMGEN CLI**: `slmgen upload data.jsonl --task qa --deploy edge`
- [ ] **Public API**: Programmatic access to analysis and recommendation engine

---

## 📅 Phasing Priority Suggestion

### Phase 1: Friction Reduction (V2.1)
Focus on widening the funnel.
1. Universal Dataset Converter (CSV, TSV, JSON, Parquet)
2. Bulk Operations
3. CLI Tool

### Phase 2: Ecosystem Loop (V2.2)
Focus on keeping the user engaged.
1. Training Completion Notifications
2. Dataset Versioning
3. Job Templates

### Phase 3: Value Expansion (V2.3+)
Focus on advanced capabilities.
1. One-Click Deployment Pipelines (Ollama, vLLM, HF)
2. Eval Benchmarks
3. Custom Training Presets

---

## ❌ Not Planned

The following were **removed in V2.0.0** and are not planned for return:

- **Inference Playground** - Requires paid API,成本的 center
- **Redis Session Storage** - Unnecessary for MVP
- **Background Job Queue** - Sync execution simpler
- **Theme Toggle** - Marked as low priority

---

## Version History

| Version | Date | Changes |
|---------|------|--------|
| 1.0.0 | 2025 | Initial release |
| 2.0.0 | 2026 | Simplified architecture, removed Redis |