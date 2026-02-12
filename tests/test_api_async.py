import pytest
import httpx

import api


@pytest.mark.asyncio
async def test_search_endpoint(monkeypatch):
    async def fake_search_async(query, candidates=5):
        return {
            "status": "success",
            "query": query,
            "timestamp": "2026-02-12T00:00:00",
            "candidates": [
                {
                    "title": "Python",
                    "url": "https://en.wikipedia.org/wiki/Python",
                    "description": "Test description",
                    "score": 1.0,
                    "disambiguation": False,
                    "pageid": 123,
                }
            ],
        }

    monkeypatch.setattr(api.agent, "search_async", fake_search_async)

    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/search/Python?candidates=1")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 1
    assert data["candidates"][0]["title"] == "Python"


@pytest.mark.asyncio
async def test_summarize_endpoint(monkeypatch):
    async def fake_summarize_async(query, bullets=5):
        return {
            "status": "success",
            "title": query,
            "timestamp": "2026-02-12T00:00:00",
            "summary": ["Point 1", "Point 2"],
            "source_url": "https://en.wikipedia.org/wiki/Python",
        }

    monkeypatch.setattr(api.agent, "summarize_async", fake_summarize_async)

    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/summarize/Python?bullets=2")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["bullets_requested"] == 2
    assert data["bullets_returned"] == 2


@pytest.mark.asyncio
async def test_compare_endpoint(monkeypatch):
    async def fake_compare_async(topic1, topic2, bullets=5):
        return {
            "status": "success",
            "topic1": topic1,
            "topic2": topic2,
            "timestamp": "2026-02-12T00:00:00",
            "comparison": {
                "similarities": ["Similar A"],
                "differences": ["Different B"],
            },
        }

    monkeypatch.setattr(api.agent, "compare_async", fake_compare_async)

    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/compare?topic1=Python&topic2=JavaScript&bullets=1")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["comparison"]["similarities"] == ["Similar A"]


@pytest.mark.asyncio
async def test_batch_endpoint(monkeypatch):
    async def fake_fetch_pages_async(titles, use_cache=True):
        return [
            {
                "success": True,
                "title": "Python",
                "url": "https://en.wikipedia.org/wiki/Python",
                "timestamp": "2026-02-12T00:00:00",
                "content": "Content",
                "html": "",
                "sections": ["Content"],
            },
            {
                "success": False,
                "title": "Missing",
                "error": "Page not found",
            },
        ]

    monkeypatch.setattr(api.agent, "fetch_pages_async", fake_fetch_pages_async)

    payload = {"titles": ["Python", "Missing"], "use_cache": True}

    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/batch", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 2
    assert data["results"][0]["title"] == "Python"
