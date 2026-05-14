# agent/tools.py

from tools.web_search import web_search
from tools.weather import get_weather
from tools.youtube import youtube_search
from tools.memory_tool import (
    get_mood_summary,
    get_conversation_summary,
    search_conversation_history,
    search_knowledge,
    save_to_knowledge
)

# Registry — maps tool name strings to actual functions
TOOL_REGISTRY = {
    "web_search": web_search,
    "get_weather": get_weather,
    "youtube_search": youtube_search,
    "youtube_shorts": lambda query: youtube_search(query, shorts=True),
    "get_mood_summary": get_mood_summary,
    "search_memory": search_conversation_history,
    "search_knowledge": search_knowledge,
    "save_to_knowledge": save_to_knowledge,
    "no_tool": lambda: None
}


def execute_tool(tool_name, parsed_args, user_id):
    print(f"⚙️ Executing tool: {tool_name}")

    # Check tool exists
    if tool_name not in TOOL_REGISTRY:
        return f"Unknown tool: {tool_name}"

    tool_fn = TOOL_REGISTRY[tool_name]
    args = parsed_args.get("args", [])
    kwargs = parsed_args.get("kwargs", {})

    try:

        # Tools that need user_id injected automatically
        if tool_name in ["get_mood_summary"]:
            return tool_fn(user_id)

        # Tools that need user_id as first arg
        elif tool_name in ["search_memory"]:
            return tool_fn(user_id, *args)

        # RAG tools — no user_id needed
        elif tool_name in ["search_knowledge", "save_to_knowledge"]:
            return tool_fn(*args)

        # no_tool — LLaMA wants to respond directly
        elif tool_name == "no_tool":
            return None

        # All other tools — just pass args
        else:
            return tool_fn(*args, **kwargs)

    except Exception as e:
        print(f"Tool execution error: {e}")
        return f"Tool {tool_name} failed: {str(e)}"


def get_available_tools_text():
    from agent.parser import build_tool_description
    return build_tool_description()