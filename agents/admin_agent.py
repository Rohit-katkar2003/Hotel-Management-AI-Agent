import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import AgentState
from agents.shared_llm import make_llm
from tools.admin_tools import ADMIN_TOOLS
from config import settings

ADMIN_SYSTEM_PROMPT = """You are the AI operations copilot for Grand Hotel admins.

You have FULL access to:
- Customer CRUD
- Room management & pricing
- Booking lifecycle: create, cancel, check-in, check-out
- Billing, payments, statistics

For destructive actions (delete, cancel, price change) ALWAYS confirm first.
Be concise, data-driven, and cite IDs/dates/amounts.
"""

_llm = make_llm().bind_tools(ADMIN_TOOLS)

def _agent_node(state: AgentState) -> dict:
    msgs = [("system", ADMIN_SYSTEM_PROMPT)] + list(state["messages"])
    return {"messages": [_llm.invoke(msgs)]}

def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "end"

def _build():
    b = StateGraph(AgentState)
    b.add_node("agent", _agent_node)
    b.add_node("tools", ToolNode(ADMIN_TOOLS))
    b.add_edge(START, "agent")
    b.add_conditional_edges("agent", _should_continue, {"tools": "tools", "end": END})
    b.add_edge("tools", "agent")
    conn = sqlite3.connect(settings.CHECKPOINT_DB_PATH + ".admin", check_same_thread=False)
    cp = SqliteSaver(conn); cp.setup()
    return b.compile(checkpointer=cp)

admin_graph = _build()