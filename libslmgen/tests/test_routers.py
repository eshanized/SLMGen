#!/usr/bin/env python3
"""
Integration tests for SLMGEN API routers.

Covers:
- Root and health endpoints
- Dataset upload (valid, invalid, malformed)
- Dataset analysis
- Model recommendation
- Notebook generation
- Training presets
- Advanced intelligence features (behavior composer, prompt linter, prompt diff, model card)
"""

import io
import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.session_store import session_store


def _make_jsonl_content(count: int = 55) -> str:
    """Generate sample conversation JSONL content."""
    lines = []
    for i in range(count):
        entry = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"How do I solve problem {i}?"},
                {"role": "assistant", "content": f"Here is the step-by-step solution for problem {i}: first examine the input."}
            ]
        }
        lines.append(json.dumps(entry))
    return "\n".join(lines)


@pytest.fixture(autouse=True)
def clean_session_store():
    """Ensure in-memory session store is active for tests."""
    session_store.start()
    yield
    session_store.stop()


@pytest.mark.asyncio
async def test_root_and_health():
    """Test health check endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "running"
        assert "version" in data

        res_health = await client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_upload_valid_dataset():
    """Test uploading a valid dataset with at least 50 examples."""
    content = _make_jsonl_content(55)
    file_bytes = content.encode("utf-8")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("dataset.jsonl", io.BytesIO(file_bytes), "application/jsonl")}
        res = await client.post("/upload", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "session_id" in data
        assert data["stats"]["total_examples"] == 55
        assert data["stats"]["quality_score"] > 0
        assert data["stats"]["has_system_prompts"] is True


@pytest.mark.asyncio
async def test_upload_invalid_extension():
    """Test uploading a non-jsonl file returns 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")}
        res = await client.post("/upload", files=files)
        assert res.status_code == 400
        assert "jsonl" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_insufficient_examples():
    """Test uploading fewer than MIN_EXAMPLES returns 400."""
    content = _make_jsonl_content(10)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("dataset.jsonl", io.BytesIO(content.encode()), "application/jsonl")}
        res = await client.post("/upload", files=files)
        assert res.status_code == 400
        assert "at least" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    """Test upload -> analyze -> recommend -> generate notebook flow."""
    content = _make_jsonl_content(60)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Upload
        files = {"file": ("dataset.jsonl", io.BytesIO(content.encode()), "application/jsonl")}
        upload_res = await client.post("/upload", files=files)
        assert upload_res.status_code == 200
        session_id = upload_res.json()["session_id"]

        # 2. Analyze
        analyze_res = await client.post("/analyze", json={"session_id": session_id})
        assert analyze_res.status_code == 200
        chars = analyze_res.json()["characteristics"]
        assert "dominant_language" in chars

        # 3. Recommend
        rec_res = await client.post("/recommend", json={
            "session_id": session_id,
            "task": "qa",
            "deployment": "cloud"
        })
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        assert "primary" in rec_data
        model_id = rec_data["primary"]["model_id"]
        assert len(model_id) > 0

        # 4. Generate Notebook
        gen_res = await client.post("/generate-notebook", json={
            "session_id": session_id,
            "model_id": model_id,
        })
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert "notebook_filename" in gen_data
        assert "download_url" in gen_data


@pytest.mark.asyncio
async def test_presets_router():
    """Test training presets endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/presets")
        assert res.status_code == 200
        presets = res.json()
        assert len(presets) > 0

        res_quick = await client.get("/presets/quick_demo")
        assert res_quick.status_code == 200
        assert res_quick.json()["preset"]["key"] == "quick_demo"


@pytest.mark.asyncio
async def test_advanced_features():
    """Test behavior composer, prompt linter, diff, and session intelligence endpoints."""
    content = _make_jsonl_content(55)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Behavior composer
        res_behavior = await client.post("/behavior/compose", json={
            "tone": 70,
            "depth": 80,
            "risk_tolerance": 20,
            "creativity": 60,
        })
        assert res_behavior.status_code == 200
        assert "system_prompt" in res_behavior.json()

        # 2. Prompt linter
        res_lint = await client.post("/lint-prompt", json={
            "prompt": "You are a concise AI assistant. Always answer accurately."
        })
        assert res_lint.status_code == 200
        assert "score" in res_lint.json()

        # 3. Prompt diff
        res_diff = await client.post("/prompt-diff", json={
            "prompt_a": "Be helpful and concise.",
            "prompt_b": "You are a helpful and very detailed assistant."
        })
        assert res_diff.status_code == 200
        assert "similarity" in res_diff.json()

        # 4. Upload dataset to test session intelligence endpoints
        files = {"file": ("dataset.jsonl", io.BytesIO(content.encode()), "application/jsonl")}
        up = await client.post("/upload", files=files)
        assert up.status_code == 200
        session_id = up.json()["session_id"]

        # Personality
        res_pers = await client.get(f"/personality/{session_id}")
        assert res_pers.status_code == 200
        assert "tone" in res_pers.json()

        # Risk
        res_risk = await client.get(f"/risk/{session_id}")
        assert res_risk.status_code == 200
        assert "score" in res_risk.json()

        # Confidence
        res_conf = await client.get(f"/confidence/{session_id}")
        assert res_conf.status_code == 200
        assert "score" in res_conf.json()

        # Model card
        res_card = await client.get(f"/model-card/{session_id}")
        assert res_card.status_code == 200
        assert "markdown" in res_card.json()
