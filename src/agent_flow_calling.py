import asyncio
from IPython.display import clear_output, Markdown, display
from agentsandnodes import supervisor_node, law_node, procedure_node, general_node, State
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing import Callable, Optional
from dotenv import load_dotenv
load_dotenv()

def build_app():
    graph = StateGraph(State)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("law", law_node)
    graph.add_node("procedure", procedure_node)
    graph.add_node("general", general_node)

    graph.add_edge(START, "supervisor")
    graph.add_edge("law", END)
    graph.add_edge("procedure", END)
    graph.add_edge("general", END)

    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)
    return app


async def call_multi_agent_system_async(agent, prompt, userid, file_path=None,on_token: Optional[Callable[[str], None]] = None):
    config = {"configurable": {"thread_id": userid}, "recursion_limit": 20}
    inputs = {"messages": [("user", prompt)], "file_path": file_path}
    accumulated_text = ""

    async for event in agent.astream_events(inputs, config=config, version="v2"):
        # Only care about LLM token events
        if event.get("event") != "on_chat_model_stream":
            continue

        data = event.get("data") or {}
        chunk = data.get("chunk")
        content = None
        if chunk is not None and hasattr(chunk, "content"):
            content = chunk.content
        elif isinstance(data, dict) and "content" in data:
            content = data.get("content")

        if content:
            stripped = content.strip()
            upper = stripped.upper()

            # Filter out spurious YES/NO tokens and short strings like 'NONO'
            if upper in {"YES", "NO"}:
                continue
            if len(upper) <= 5 and set(upper).issubset({"N", "O"}):
                continue

            accumulated_text += content
            if on_token:
                on_token(content)
            else:
                print(content, end="", flush=True)

    if not on_token and accumulated_text:
        print()

    return clean_agent_prefix(accumulated_text)

def clean_agent_prefix(text: str) -> str:
    """Remove any agent name prefixes from the response."""
    prefixes = ["law!", "procedure!", "general!", "law:", "procedure:", "general:","law", "procedure", "general"]
    
    for prefix in prefixes:
        if text.strip().startswith(prefix):
            text = text.strip()[len(prefix):].strip()
    
    return text

def call_multi_agent_system(
    agent, 
    prompt: str, 
    userid: str, 
    file_path: Optional[str] = None,
    on_token: Optional[Callable[[str], None]] = None
) -> str:
    """
    Synchronous wrapper for the async multi-agent system call.
    Works in both Streamlit and Jupyter notebooks.
    
    Args:
        agent: The compiled LangGraph application
        prompt: User's input message
        userid: Thread ID for conversation persistence
        file_path: Optional path to uploaded document
        on_token: Optional callback function for real-time token streaming
    
    Returns:
        Complete response text
    """
    try:
        # Preferred path for Streamlit (no running loop)
        return asyncio.run(
            call_multi_agent_system_async(agent, prompt, userid, file_path, on_token)
        )
    except RuntimeError as e:
        # Fallback if a loop is already running (e.g., in notebooks)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new loop in a separate context
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(
                    call_multi_agent_system_async(agent, prompt, userid, file_path, on_token)
                )
            finally:
                new_loop.close()
                asyncio.set_event_loop(loop)
        else:
            return loop.run_until_complete(
                call_multi_agent_system_async(agent, prompt, userid, file_path, on_token)
            )