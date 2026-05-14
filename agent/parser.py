# agent/parser.py

import re
from brain import analyze_frames

# Define what tools LLaMA is allowed to call
AVAILABLE_TOOLS = {
    "web_search": {
        "description": "Search the web for current information",
        "args": ["query"],
        "example": 'web_search("anxiety management techniques")'
    },
    "get_weather": {
        "description": "Get current weather for a city",
        "args": ["city"],
        "example": 'get_weather("Perth, Australia")'
    },
    "youtube_shorts": {
        "description": "Find short videos under 60 seconds on YouTube. ALWAYS use this for entertainment, mood lifting, funny videos, cheering up",
        "args": ["query"],
        "example": 'youtube_shorts("funny animals")'
    },
    "youtube_search": {
        "description": "Find longer YouTube videos for tutorials or detailed content only",
        "args": ["query"],
        "example": 'youtube_search("meditation guide")'
    },
    "get_mood_summary": {
        "description": "Get the user's recent mood history",
        "args": ["user_id"],
        "example": 'get_mood_summary(user_id)'
    },
    "search_memory": {
        "description": "Search past conversations for a keyword",
        "args": ["user_id", "keyword"],
        "example": 'search_memory(user_id, "Perth move")'
    },
    "no_tool": {
        "description": "Respond directly without using any tool",
        "args": [],
        "example": "no_tool()"
    },
    "search_knowledge": {
        "description": "Search the personal knowledge base for relevant information. ALWAYS use this first before web_search — it may already have what you need",
        "args": ["query"],
        "example": 'search_knowledge("anxiety management techniques")'
    },
    "save_to_knowledge": {
        "description": "Save useful information discovered from web search to the knowledge base for future use. Use this when web_search returns genuinely useful content worth remembering",
        "args": ["content", "source"],
        "example": 'save_to_knowledge("article content here", "https://source-url.com")'
    }
}


def build_tool_description():
    desc = "You have access to these tools:\n\n"
    for name, info in AVAILABLE_TOOLS.items():
        desc += f"- {name}: {info['description']}\n"
        desc += f"  Example: {info['example']}\n"
    return desc


def parse_action(text):
    # Look for Action: tool_name("arg1", "arg2")
    action_match = re.search(
        r'Action:\s*(\w+)\s*\((.*?)\)',
        text,
        re.DOTALL
    )

    if not action_match:
        return None, None

    tool_name = action_match.group(1).strip()
    args_str = action_match.group(2).strip()

    # Parse arguments
    args = []
    kwargs = {}

    if args_str:
        # Split by comma but respect quotes
        raw_args = re.findall(
            r'"([^"]*?)"|\'([^\']*?)\'|(\w+)=(\w+)|(\w+)',
            args_str
        )

        for match in raw_args:
            quoted1, quoted2, kwkey, kwval, plain = match
            if quoted1:
                args.append(quoted1)
            elif quoted2:
                args.append(quoted2)
            elif kwkey and kwval:
                kwargs[kwkey] = kwval == "True"

    return tool_name, {"args": args, "kwargs": kwargs}


def parse_final_answer(text):
    # Look for Final Answer: ...
    match = re.search(
        r'Final Answer:\s*(.*?)(?:Thought:|Action:|$)',
        text,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()
    return None


def parse_thought(text):
    # Extract the Thought: portion
    match = re.search(
        r'Thought:\s*(.*?)(?:Action:|Final Answer:|$)',
        text,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()
    return None


def is_final_answer(text):
    return "Final Answer:" in text


def format_observation(tool_name, result):
    if tool_name in ["youtube_search", "youtube_shorts"]:
        return (
            f"\nObservation: [{tool_name}] returned:\n{result}\n"
            f"CRITICAL: Copy the EXACT URLs from above into Final Answer. "
            f"Do NOT modify or generate new URLs. "
            f"Only use URLs that appear in the Observation above.\n"
        )
    return f"\nObservation: [{tool_name}] returned:\n{result}\n"

