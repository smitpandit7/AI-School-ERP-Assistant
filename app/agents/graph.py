from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (
    intent_classifier_node,
    planner_node,
    tool_executor_node,
    response_generator_node
)
from app.utils.logger import get_logger

logger = get_logger()


def build_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph agent.

    Flow:
    START
      ↓
    intent_classifier   → identifies what user wants
      ↓
    planner             → decides which tools to call + args
      ↓
    tool_executor       → calls ERP tools, collects results
      ↓
    response_generator  → formats final response using Groq
      ↓
    END
    """

    graph = StateGraph(AgentState)

    # ── Register Nodes ─────────────────────────────────────────────
    graph.add_node("intent_classifier",   intent_classifier_node)
    graph.add_node("planner",             planner_node)
    graph.add_node("tool_executor",       tool_executor_node)
    graph.add_node("response_generator",  response_generator_node)

    # ── Define Edges ───────────────────────────────────────────────
    graph.set_entry_point("intent_classifier")

    graph.add_edge("intent_classifier", "planner")
    graph.add_edge("planner",           "tool_executor")
    graph.add_edge("tool_executor",     "response_generator")
    graph.add_edge("response_generator", END)

    # ── Compile ────────────────────────────────────────────────────
    compiled = graph.compile()
    logger.info("✅ LangGraph agent compiled successfully")

    return compiled


# Singleton — import this in routes.py
erp_agent = build_graph()