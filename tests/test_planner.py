import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import httpx
from httpx import AsyncClient
from backend.services.planner.main import app, OpenRouter

class DummyCompletions:
    async def create(self, *args, **kwargs):
        return {"domains": ["architecture"], "tasks": {"architecture": {"subtasks": ["a"], "tools": ["b"]}}}

class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()

class DummyRouter:
    def __init__(self, api_key=None):
        self.chat = DummyChat()

@pytest.mark.asyncio
async def test_plan(monkeypatch):
    monkeypatch.setattr("backend.services.planner.main.OpenRouter", lambda api_key=None: DummyRouter(api_key))
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/plan", json={"prompt": "Design a carbon-negative city"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["domains"]
