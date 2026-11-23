import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.state import AgentState
from agents.shared_llm import make_llm
from tools.user_tools import USER_TOOLS
from config import settings

USER_SYSTEM_PROMPT = """You are the friendly AI concierge for Grand Hotel.

You can ONLY:
- Show available rooms (with images)
- Answer questions about room types & prices
- Create bookings for guests (collect name, email, phone, room, dates)
- Look up a guest's own booking
- Cancel a guest's own booking (always confirm first)

You CANNOT: change prices, delete customers, view all customers,
check guests in/out, process payments, or run admin reports.
Politely redirect those to "admin staff".

Date format: YYYY-MM-DD. Currency: USD ($).
When search_available_rooms returns room data, summarise it warmly.
"""

_llm = make_llm().bind_tools(USER_TOOLS)

def _agent_node(state: AgentState) -> dict:
    msgs = [("system", USER_SYSTEM_PROMPT)] + list(state["messages"])
    return {"messages": [_llm.invoke(msgs)]}

def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"

def _build():
    b = StateGraph(AgentState)
    b.add_node("agent", _agent_node)
    b.add_node("tools", ToolNode(USER_TOOLS))
    b.add_edge(START, "agent")
    b.add_conditional_edges("agent", _should_continue, {"tools": "tools", "end": END})
    b.add_edge("tools", "agent")
    conn = sqlite3.connect(settings.CHECKPOINT_DB_PATH, check_same_thread=False)
    cp = SqliteSaver(conn); cp.setup()
    return b.compile(checkpointer=cp)

user_graph = _build()