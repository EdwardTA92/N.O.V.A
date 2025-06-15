import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pickle
from unittest.mock import patch

import fakeredis
from langgraph.graph.state import CompiledStateGraph

from backend.services.compiler.compiler import compile_graph


def test_compile_graph_stores_in_redis():
    taskgraph = {
        "domains": [
            {
                "name": "demo",
                "orchestrator": {"name": "orch"},
                "specialists": [
                    {"name": "spec1"},
                    {"name": "spec2"},
                ],
            }
        ]
    }

    fake = fakeredis.FakeRedis()
    with patch("backend.services.compiler.compiler.redis.Redis", return_value=fake):
        uid = compile_graph(taskgraph)

    stored = fake.get(f"graphs:{uid}")
    assert stored is not None
    graph = pickle.loads(stored)
    assert isinstance(graph, CompiledStateGraph)
