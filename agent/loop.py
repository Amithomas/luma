# agent/loop.py

import requests
import json

from brain import analyze_frames
from config import OLLAMA_URL, OLLAMA_MODEL
from agent.parser import (
    parse_action,
    parse_final_answer,
    parse_thought,
    is_final_answer,
    format_observation,
    build_tool_description
)
from agent.tools import execute_tool
from mood import get_recent_mood, get_conversation_history, get_summaries

MAX_ITERATIONS = 5

def build_agent_prompt(user_id, message, conversation_history=""):
    # Get context
    recent_moods = get_recent_mood(user_id)
    mood_context = ""
    if recent_moods:
        mood_context = "Recent mood history:\n"
        for mood_text, sentiment, emotion, intensity, mood_summary, timestamp in recent_moods:
            mood_context += (
                f"- {timestamp[:10]}: {mood_summary} "
                f"(emotion: {emotion}, intensity: {intensity:.1f})\n"
            )

    summaries = get_summaries(user_id)
    long_term = ""
    if summaries:
        long_term = "Long term memory:\n"
        for summary_text, timestamp in summaries:
            long_term += f"[{timestamp[:10]}] {summary_text}\n"

    history = get_conversation_history(user_id, limit=6)
    recent_convo = ""
    if history:
        recent_convo = "Recent conversation:\n"
        for role, msg in history:
            label = "User" if role == "user" else "Luma"
            recent_convo += f"{label}: {msg}\n"

    tools = build_tool_description()

    prompt = f"""You are Luma, an emotionally intelligent AI companion.
You know this person deeply and genuinely care about them.
You respond like a warm, real best friend — never generic.
Do not say 'As an AI'.

{long_term}

{mood_context}

{recent_convo}

{tools}

IMPORTANT INSTRUCTIONS:
- You MUST use at least one tool before giving a Final Answer
- When user feels low, sad, anxious or overwhelmed → ALWAYS use web_search + youtube_shorts
- When user mentions going outside or activities → ALWAYS use get_weather
- When user asks about past conversations → use search_memory
- Only use no_tool() for simple greetings like "hi" or "hello"
- Never use more than {MAX_ITERATIONS} tools in one response
- Always end with Final Answer:
- Keep Final Answer warm, personal and conversational
- Naturally weave tool results into your response
- Do not say "I searched for..." or mention tools in Final Answer
- If YouTube videos were found ALWAYS include the video URLs in Final Answer
- Format videos like: "🎬 [Video Title](URL)"
- For entertainment, funny videos, cheering up → ALWAYS use youtube_shorts not youtube_search
- youtube_search is only for tutorials or long form content
- NEVER generate or modify YouTube URLs
- ONLY use URLs exactly as they appear in the Observation
- If a URL appears in Observation, copy it character by character
- ALWAYS call search_knowledge() first before web_search — check existing knowledge first
- After a useful web_search result, consider calling save_to_knowledge() to remember it
- Only save genuinely useful, factual content — not casual conversation
- When responding to a reel, ALWAYS search youtube_shorts for related content if the reel has a clear topic or theme


You must respond in this exact format:

Thought: [your reasoning about what the user needs]
Action: [tool_name("arg")] or [no_tool()]
Observation: [result will be inserted here by the system]
... (repeat Thought/Action/Observation as needed)
Final Answer: [your warm personal response to the user]

STOP after writing Action: and wait for Observation. Do NOT write Observation yourself.


{conversation_history}

User: {message}
"""
    return prompt

def run_agent(user_id, message):
    print(f"\n🤖 Agent starting for: '{message[:50]}...'")

    conversation_history = ""
    iterations = 0

    while iterations < MAX_ITERATIONS:
        iterations += 1
        print(f"\n--- Iteration {iterations} ---")

        # Build prompt with accumulated history
        prompt = build_agent_prompt(user_id, message, conversation_history)

        # Call LLaMA
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 600,
                "stop": ["Observation:", "\nObservation"]
            }
        }

        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json()
        llama_output = result.get("response", "").strip()
        # Strip any hallucinated observations
        if "Observation:" in llama_output:
            llama_output = llama_output.split("Observation:")[0].strip()

        print(f"LLaMA output:\n{llama_output}\n")

        # Check if LLaMA gave a final answer
        if is_final_answer(llama_output):
            final = parse_final_answer(llama_output)
            if final:
                print(f"✅ Final answer reached after {iterations} iterations")
                return final

        # Parse the action LLaMA wants to take
        tool_name, parsed_args = parse_action(llama_output)

        if not tool_name:
            # No action found — treat entire output as final answer
            print("⚠️ No action found, using output as final answer")
            return llama_output

        # Log the thought
        thought = parse_thought(llama_output)
        if thought:
            print(f"💭 Thought: {thought[:100]}...")

        # Execute the tool
        tool_result = execute_tool(tool_name, parsed_args, user_id)

        # no_tool means respond directly
        if tool_result is None:
            print("💬 no_tool selected — responding directly")
            prompt_direct = build_agent_prompt(user_id, message, "")
            prompt_direct += "\nThought: I can respond directly to this.\nFinal Answer:"

            payload["prompt"] = prompt_direct
            payload["options"]["stop"] = []
            response = requests.post(OLLAMA_URL, json=payload)
            result = response.json()
            return result.get("response", "").strip()

        # Format observation and add to history
        observation = format_observation(tool_name, tool_result)
        conversation_history += f"\n{llama_output}{observation}"

        print(f"📊 Observation added, continuing loop...")

    # Max iterations reached — ask LLaMA for final answer with all context
    print(f"⚠️ Max iterations reached, forcing final answer...")
    prompt = build_agent_prompt(user_id, message, conversation_history)
    prompt += "\nFinal Answer:"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "max_tokens": 400,
            "stop": []
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    return result.get("response", "I'm having trouble thinking right now 😅").strip()


def run_agent_with_reel(user_id, reel_data):
    transcript = reel_data.get("transcript", "")
    frames = reel_data.get("frames", [])

    print(f"\n🎬 Agent processing reel...")

    # Step 1 — Get visual description from LLaVA
    print("👁️ Analysing frames with LLaVA...")
    visual_description = analyze_frames(frames)

    # Step 2 — Build reel context
    reel_context = f"""The user just shared an Instagram reel with you.

What was heard (audio transcript):
{transcript if transcript else "No speech detected."}

What was seen (visual description):
{visual_description}

Based on this reel and the user's emotional state:
1. Respond emotionally as their best friend who just watched it
2. Consider finding related YouTube Shorts if the reel topic warrants it
3. Consider searching knowledge base for relevant information
4. Save any useful discoveries to knowledge base"""

    # Step 3 — Run agent with reel context as the message
    print("🤖 Agent deciding how to respond...")

    conversation_history = ""
    iterations = 0

    while iterations < MAX_ITERATIONS:
        iterations += 1
        print(f"\n--- Reel Agent Iteration {iterations} ---")

        prompt = build_agent_prompt(user_id, reel_context, conversation_history)

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 600,
                "stop": ["Observation:", "\nObservation"]
            }
        }

        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json()
        llama_output = result.get("response", "").strip()

        # Strip hallucinated observations
        if "Observation" in llama_output:
            llama_output = llama_output.split("Observation")[0].strip()
        if "appeared on screen" in llama_output:
            llama_output = llama_output.split("appeared on screen")[0].strip()
            llama_output = llama_output.rsplit("\n", 1)[0].strip()

        print(f"Agent output:\n{llama_output}\n")

        # Check for final answer
        if is_final_answer(llama_output):
            final = parse_final_answer(llama_output)
            if final:
                print(f"✅ Reel response ready after {iterations} iterations")
                return final

        # Parse and execute tool
        tool_name, parsed_args = parse_action(llama_output)

        if not tool_name:
            print("⚠️ No action found, using output as final answer")
            return llama_output

        thought = parse_thought(llama_output)
        if thought:
            print(f"💭 Thought: {thought[:100]}...")

        tool_result = execute_tool(tool_name, parsed_args, user_id)

        if tool_result is None:
            prompt_direct = build_agent_prompt(user_id, reel_context, "")
            prompt_direct += "\nThought: I have enough context to respond.\nFinal Answer:"
            payload["prompt"] = prompt_direct
            payload["options"]["stop"] = []
            response = requests.post(OLLAMA_URL, json=payload)
            result = response.json()
            return result.get("response", "").strip()

        observation = format_observation(tool_name, tool_result)
        conversation_history += f"\n{llama_output}{observation}"
        print(f"📊 Observation added, continuing...")

    # Force final answer
    print("⚠️ Max iterations reached, forcing final answer...")
    prompt = build_agent_prompt(user_id, reel_context, conversation_history)
    prompt += "\nFinal Answer:"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "max_tokens": 400,
            "stop": []
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    return result.get("response", "I'm having trouble thinking right now 😅").strip()