"""Linear LangGraph ask path: retrieve then generate."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from atlas_orchestration.nodes.generate import generate_node
from atlas_orchestration.nodes.retrieve import retrieve_node
from atlas_orchestration.state import AskState

_compiled = None


def build_ask_graph():
    graph = StateGraph(AskState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def get_ask_graph():
    global _compiled
    if _compiled is None:
        _compiled = build_ask_graph()
    return _compiled
