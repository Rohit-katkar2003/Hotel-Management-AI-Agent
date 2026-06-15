import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import AgentState
from graph.nodes import agent_node, tool_node, should_continue
from config import settings


def build_graph():
    """Build and compile the Hotel Agent graph with SQLite checkpointing."""
    # ─── Build graph ───
    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        "end": END
    })
    builder.add_edge("tools", "agent")  # After tools → back to agent (loop)

    # ─── Checkpointer (persists conversation state) ───
    conn = sqlite3.connect(settings.CHECKPOINT_DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    # ─── Compile ───
    graph = builder.compile(checkpointer=checkpointer)
    return graph


# Create the graph instance
graph = build_graph()