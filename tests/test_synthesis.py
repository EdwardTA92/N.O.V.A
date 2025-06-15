import asyncio
import os
import sys
from pathlib import Path

import fakeredis.aioredis
from fastapi.testclient import TestClient

# Ensure the package can be imported when the repository root contains dots.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import synthesis.main as main


class DummyResponse:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": content})()})]


async def dummy_generate_report(events):
    return "dummy markdown"


async def setup_redis():
    fake = fakeredis.aioredis.FakeRedis()
    await fake.rpush("run:test:events", "e1", "e2")
    return fake


def test_synthesize(monkeypatch):
    redis_instance = asyncio.run(setup_redis())
    monkeypatch.setattr(main, "redis_client", redis_instance)
    monkeypatch.setattr(main, "generate_report", dummy_generate_report)
    client = TestClient(main.app)
    resp = client.post("/synthesize/test")
    assert resp.status_code == 200
    assert resp.json()["markdown"] == "dummy markdown"
