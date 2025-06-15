import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from typing import AsyncIterator

app = FastAPI()

# Redis connection
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_KEY = "nova:events"

def load_graph(graph_id: str):
    # Placeholder for actual graph loading logic
    # In real implementation, retrieve serialized graph from Redis and
    # deserialize into an object with a .stream() async iterator method.
    async def example_stream() -> AsyncIterator[str]:
        # Example: yield numbers as strings
        for i in range(5):
            await asyncio.sleep(0.1)
            yield f"token_{i}"
    class Graph:
        async def stream(self):
            async for token in example_stream():
                yield token
    return Graph()

@app.post("/run")
async def run(graph_id: str):
    graph = load_graph(graph_id)
    run_id = str(uuid.uuid4())

    async def publish():
        async for token in graph.stream():
            await redis_client.xadd(STREAM_KEY, {"run_id": run_id, "token": token})

    asyncio.create_task(publish())
    return {"run_id": run_id}

@app.websocket("/ws/events")
async def websocket_events(ws: WebSocket):
    await ws.accept()
    last_id = "$"
    try:
        while True:
            resp = await redis_client.xread({STREAM_KEY: last_id}, block=0)
            if resp:
                for _, events in resp:
                    for event_id, event in events:
                        last_id = event_id
                        await ws.send_json({"run_id": event.get("run_id"), "token": event.get("token")})
    except WebSocketDisconnect:
        pass
