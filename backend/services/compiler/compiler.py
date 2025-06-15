import pickle
import uuid
from typing import Dict

import redis
from crewai import Agent
from functools import partial
from langgraph.graph import StateGraph, END, START


def _run_agent(state: dict, *, agent: Agent) -> dict:
    """Helper to invoke a crewai Agent and return state."""
    agent.kickoff("run")
    return state


def compile_graph(taskgraph: Dict) -> str:
    """Compile a task graph into a langgraph StateGraph and store it in redis.

    Parameters
    ----------
    taskgraph: Dict
        Specification of the domains, orchestrators and specialists.

    Returns
    -------
    str
        UUID for the stored compiled graph.
    """
    graph = StateGraph(dict)

    for domain in taskgraph.get("domains", []):
        domain_name = domain.get("name", "domain")
        orch_data = domain.get("orchestrator", {})
        orch_agent = Agent(
            name=orch_data.get("name", f"{domain_name}_orchestrator"),
            role=orch_data.get("role", "orchestrator"),
            goal=orch_data.get("goal", "coordinate"),
            backstory=orch_data.get("backstory", ""),
        )
        orch_node = f"{domain_name}_orchestrator"
        graph.add_node(orch_node, partial(_run_agent, agent=orch_agent))
        graph.add_edge(START, orch_node)
        previous = orch_node
        for idx, spec in enumerate(domain.get("specialists", [])):
            spec_agent = Agent(
                name=spec.get("name", f"{domain_name}_spec_{idx}"),
                role=spec.get("role", "specialist"),
                goal=spec.get("goal", "execute"),
                backstory=spec.get("backstory", ""),
            )
            spec_node = f"{domain_name}_specialist_{idx}"
            graph.add_node(spec_node, partial(_run_agent, agent=spec_agent))
            graph.add_edge(previous, spec_node)
            previous = spec_node
        graph.add_edge(previous, END)

    compiled = graph.compile()
    graph_id = str(uuid.uuid4())
    redis.Redis().set(f"graphs:{graph_id}", pickle.dumps(compiled))
    return graph_id
