# Inference Playground — Architecture Walkthrough

## 1. Backend Inference Architecture

### Overview

The inference system provides real-time prompt testing and model comparison via the HuggingFace Inference API.

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Frontend   │────▶│  FastAPI    │────▶│ HuggingFace        │
│  Playground  │     │  Endpoints   │     │ Inference API       │
└──────────────┘     └──────────────┘     └─────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Comparison  │
                    │   Engine    │
                    │ (risk.py,   │
                    │ confidence) │
                    └──────────────┘
```

### Components

```
libslmgen/app/inference/
├── __init__.py           # Module exports
├── engine.py             # HuggingFace API wrapper
└── comparison.py         # Model comparison + metrics

libslmgen/app/routers/
└── inference.py          # API endpoints
```

### Engine Architecture

The `InferenceEngine` class wraps the HuggingFace Inference API:

```python
class InferenceEngine:
    async def generate(
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[InferenceConfig] = None,
    ) -> GenerationResult
```

Key features:
- **Async HTTP**: Uses `httpx.AsyncClient` for non-blocking requests
- **Timeout handling**: Configurable 30s default timeout
- **Error resilience**: Returns structured error responses instead of raising
- **Model loading**: Handles 503 responses for cold-start models

### Request Flow

```
Client Request
      │
      ▼
┌─────────────────────────┐
│ Validate Request         │  ← Check model_id, prompt length
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ Build HF API Payload     │  ← Format for chat vs text models
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ POST to HF Inference API │
└─────────────────────────┘
      │
      ├─── 200 ──▶ Parse Response
      │              │
      │              ▼
      │         ┌─────────────────┐
      │         │ GenerationResult │
      │         │ {output, latency│
      │         │  tokens, error} │
      │         └─────────────────┘
      │
      ├─── 503 ──▶ Model Loading (retry suggested)
      │
      ├─── 401 ──▶ Auth Required
      │
      └─── Timeout ─▶ Error Response
```

---

## 2. Async Parallel Inference

### How Parallel Calls Work

The comparison engine uses `asyncio.gather` for parallel execution:

```python
async def compare(self, base_model, tuned_model, ...):
    # Run both models in parallel
    results = await asyncio.gather(
        self._inference.generate(base_model, prompt, ...),
        self._inference.generate(tuned_model, prompt, ...),
        return_exceptions=True,
    )
```

This means:
- Both API calls execute concurrently
- Total time ≈ max(latency_1, latency_2), not sum
- If one fails, the other still completes

### Why Async?

```python
# Synchronous (blocking)
result1 = requests.post(url1)  # 1000ms
result2 = requests.post(url2)  # 1200ms
# Total: 2200ms

# Async (non-blocking)
result1, result2 = await asyncio.gather(
    client.post(url1),  # Starts immediately
    client.post(url2), # Starts immediately
)
# Total: ~1200ms (parallel)
```

Benefits:
- **2x faster** for comparison mode
- **Non-blocking** server handles more requests
- **Fair comparison** models run at the same time (no cache effects)

---

## 3. Comparison Scoring

### Metrics Computed

| Metric | Description | Range |
|--------|-------------|-------|
| `latency_delta_ms` | Tuned - Base latency | -∞ to +∞ |
| `token_delta` | Tuned - Base tokens | -∞ to +∞ |
| `similarity_score` | Output similarity (Jaccard bigrams) | 0.0 - 1.0 |
| `base_risk_score` | Hallucination risk (base model) | 0.0 - 1.0 |
| `tuned_risk_score` | Hallucination risk (tuned model) | 0.0 - 1.0 |
| `quality_score` | Composite quality (length, coherence, vocab) | 0.0 - 1.0 |

### Similarity Score Algorithm

Uses **Jaccard similarity** on character bigrams:

```python
def _compute_text_similarity(text1: str, text2: str) -> float:
    # Normalize to lowercase words
    words1 = text1.lower().split()
    words2 = text2.lower().split()
    
    # Build bigram sets
    bigrams1 = set((words1[i], words1[i+1]) for i in range(len(words1)-1))
    bigrams2 = set((words2[i], words2[i+1]) for i in range(len(words2)-1))
    
    # Jaccard: |intersection| / |union|
    intersection = len(bigrams1 & bigrams2)
    union = len(bigrams1 | bigrams2)
    
    return intersection / union if union > 0 else 0.0
```

**Example:**
- `"Hello world"` → bigrams: {("hello","world")}
- `"Hello world!"` → bigrams: {("hello","world!")}
- Similarity: 0.5 (different second element)

### Risk Scoring

Simplified from `risk.py` for single outputs:

1. **Abstract density**: Count hedging words (probably, might, etc.)
2. **Grounding markers**: Count factual references (according to, data shows, etc.)
3. **Concrete claims**: Count numbers/dates

```
risk_score = 0.4 * abstract_density + 0.3 * (1 - grounding) + 0.3
```

### Quality Scoring

Factors:
- **Length score**: Optimal 50-500 words (not too short, not too long)
- **Coherence score**: Sentence count (more sentences = more developed)
- **Vocabulary score**: Unique word ratio (higher = more varied)

```
quality = 0.4 * length_score + 0.3 * coherence_score + 0.3 * vocab_score
```

---

## 4. Frontend Data Flow

### API → State → UI

```
┌─────────────────────────────────────────────────────────────┐
│                      React Component                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   State    │◀───│  useEffect │◀───│   API Call  │   │
│  │  (models,  │    │  (on mount)│    │  (fetch)   │   │
│  │  results)  │    │            │    │             │   │
│  └──────┬─────┘    └─────────────┘    └─────────────┘   │
│         │                                                 │
│         ▼                                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │                  JSX Render                       │    │
│  │  {isLoading ? <Loader /> : <Output />}          │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### API Client Functions

```typescript
// Single inference
runInference({
    model_id: "microsoft/Phi-4-mini-instruct",
    prompt: "What is AI?",
    temperature: 0.7,
    max_tokens: 512,
})

// Comparison (parallel)
compareInference({
    base_model_id: "microsoft/Phi-4-mini-instruct",
    tuned_model_id: "my-finetuned-model",
    prompt: "What is AI?",
})

// List available models
listInferenceModels()
```

### State Management

```typescript
// Local component state
const [baseModel, setBaseModel] = useState<string>('');
const [prompt, setPrompt] = useState<string>('');
const [isRunning, setIsRunning] = useState<boolean>(false);
const [result, setResult] = useState<ComparisonResponse | null>(null);

// Prompt history (last 5)
const [history, setHistory] = useState<PromptHistoryItem[]>([]);
```

### UI Components

```
PlaygroundPage
├── Model Selection Card
│   ├── Base Model dropdown
│   └── Tuned Model dropdown (optional)
├── Prompt Card
│   ├── System Prompt textarea
│   ├── User Prompt textarea
│   ├── Temperature slider
│   ├── Max Tokens slider
│   └── Run / Compare buttons
├── History Card (last 5 prompts)
└── Output Section
    ├── MetricsCard (comparison only)
    ├── OutputCard (base model)
    └── OutputCard (tuned model, if comparing)
```

---

## 5. Integration with Session System

### Pre-filling from Recommendations

Users can navigate from the recommendation step to the playground with their model pre-selected:

```typescript
// From recommendation step
<Link href={`/dashboard/playground?model=${selectedModelId}`}>
    Test in Playground
</Link>

// In playground page
useEffect(() => {
    const modelId = searchParams.get('model');
    if (modelId) {
        setBaseModel(modelId);
    }
}, []);
```

### Session Data Flow

```
Upload → Ingest → Analyze → Recommend → Generate
                                    │
                                    ▼
                              Playground
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              Base Model                     Tuned Model
              (from recommend)               (from training)
```

### Integration Points

1. **Model Selection**: Pre-populated with recommended model
2. **Prompt Suggestions**: Can use examples from dataset
3. **System Prompts**: Reuse personality traits from analysis

---

## 6. Performance Considerations

### Client-Side

| Optimization | Implementation |
|-------------|----------------|
| Parallel calls | Both models requested simultaneously |
| Debounce | Not implemented (explicit Run/Compare buttons) |
| Memoization | React.memo for output cards |
| Lazy loading | Models loaded once on mount |

### Server-Side

| Optimization | Implementation |
|-------------|----------------|
| Async HTTP | `httpx.AsyncClient` with connection pooling |
| Timeout handling | 30s default, prevents hanging |
| Error handling | Returns structured errors, doesn't crash |
| Cache headers | HF API caches by default |

### Rate Limiting

Currently not rate-limited, but can be added:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/run")
@limiter.limit("10/minute")
async def run_inference(request: InferenceRequest):
    ...
```

---

## 7. Security Considerations

### Input Validation

```python
class InferenceRequest(BaseModel):
    model_id: str  # Must be valid HF model
    prompt: str = Field(..., min_length=1, max_length=10000)
    system_prompt: Optional[str] = Field(None, max_length=2000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=1, le=4096)
```

### Model Validation

Only models from the SLMGEN registry can be used (or arbitrary HF models via custom input):

```python
# From registry (safe)
MODELS["phi4"].model_id  # Pre-approved

# Custom (validated by HF API)
# May return 401/403 if not accessible
```

### Potential Abuse

| Risk | Mitigation |
|------|------------|
| Prompt injection | Limited (user provides own prompts) |
| Resource exhaustion | Token limits prevent infinite output |
| API key abuse | HF provides rate limits |
| Model access | Gated models require auth token |

---

## 8. Future Extensibility

### Local Models (Ollama)

```python
async def generate_ollama(
    model: str,
    prompt: str,
    base_url: str = "http://localhost:11434",
):
    """Generate using local Ollama server."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt},
        )
        return response.json()["response"]
```

### vLLM Backend

```python
async def generate_vllm(
    model: str,
    prompt: str,
    base_url: str = "http://localhost:8000",
):
    """Generate using vLLM OpenAI-compatible API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/v1/completions",
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": 512,
            },
        )
        return response.json()["choices"][0]["text"]
```

### Multi-Model Ensemble

```python
async def ensemble_generate(
    models: list[str],
    prompt: str,
    strategy: str = "majority",  # or "average", "best"
) -> dict:
    """Generate from multiple models and combine."""
    results = await asyncio.gather(*[
        engine.generate(model, prompt) for model in models
    ])
    
    if strategy == "majority":
        return vote(results)
    elif strategy == "best":
        return select_best(results)
```

### Caching Layer

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_similarity(prompt_hash: str, model_id: str) -> str:
    """Cache frequent prompts."""
    return generate(prompt, model_id)
```

---

## 9. Testing Strategy

### Unit Tests

```python
# Test similarity scoring
def test_identical_texts():
    score = _compute_text_similarity("Hello", "Hello")
    assert score == 1.0

# Test risk scoring
def test_grounded_text_low_risk():
    text = "According to research, 73% prefer option A."
    score, level = _compute_risk_score(text)
    assert level in ["low", "medium"]
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_compare_two_models():
    """Test parallel comparison works."""
    engine = ComparisonEngine(mock_inference)
    result = await engine.compare("model1", "model2", "prompt")
    
    assert result.base_output
    assert result.tuned_output
    assert result.metrics.similarity_score >= 0
```

### Mock Testing

For tests that call real HF API:

```python
@pytest.fixture
def mock_hf_response():
    return {
        "generated_text": "Mock response from model"
    }

@pytest.mark.asyncio
async def test_with_mock(mocker):
    mocker.patch("httpx.AsyncClient.post", 
                 return_value=MockResponse(json=mock_hf_response))
    # ... test
```

---

## 10. Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_TOKEN` | None | HuggingFace API token (for gated models) |
| `INFERENCE_TIMEOUT` | 30 | Request timeout in seconds |

### API Configuration

```python
class InferenceConfig:
    temperature: float = 0.7      # Randomness
    max_tokens: int = 512         # Output length
    timeout: float = 30.0         # Request timeout
    do_sample: bool = True         # Sampling vs greedy
    top_p: float = 0.9            # Nucleus sampling
```

### Model Registry

Models come from the existing recommendation engine:

```python
from core.recommender import MODELS

for key, spec in MODELS.items():
    # spec.model_id, spec.name, spec.size, spec.is_gated
```
