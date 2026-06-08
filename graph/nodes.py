from langchain_openai import ChatOpenAI 
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT
from graph.state import AgentState
from config import settings

# ─── LLM with tools bound ───
llm = ChatOpenAI(model=settings.open_router_model,
                  temperature=settings.llm_temperature , 
                  api_key=settings.open_router_api , 
                  base_url=settings.open_router_base_url) 

llm_with_tools = llm.bind_tools(ALL_TOOLS) 

SYS_PROMPT = SystemMessage(content=SYSTEM_PROMPT)

def agent_node(state: AgentState) -> dict:
    """The main LLM node — decides what to do next."""
    messages = [SYSTEM_PROMPT] + list(state["messages"])
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Route: if the LLM made tool calls → go to tools. Otherwise → end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


# ─── Prebuilt Tool Node (handles tool execution + ToolMessages) ───
tool_node = ToolNode(ALL_TOOLS)
