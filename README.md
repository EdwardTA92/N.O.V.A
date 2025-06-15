# N.O.V.A Runner Service

This repository contains a simple runner service that exposes two endpoints:

- `POST /run` – takes a `graph_id`, loads a graph from Redis, streams tokens from the graph and publishes them to a Redis Stream `nova:events`. Returns a `run_id`.
- `WS /ws/events` – WebSocket endpoint that streams events from the Redis stream to connected clients.

The implementation in `runner/main.py` uses FastAPI and asynchronous Redis.
