# brain.py

import requests
import json

from telegram import Update
from telegram.ext import ContextTypes

from config import OLLAMA_URL, OLLAMA_MODEL
from rag.retriever import get_relevant_context
from rag.loader import load_document
from rag.embedder import embed_and_store, list_sources
from mood import get_recent_mood, get_conversation_history, save_summary, get_message_count, get_summaries

LLAVA_URL = "http://127.0.0.1:11434/api/generate"
LLAVA_MODEL = "llava:7b"


def analyze_frames(frames):
    if not frames:
        return "No visual content could be extracted."

    descriptions = []

    for i, frame_base64 in enumerate(frames):
        payload = {
            "model": LLAVA_MODEL,
            "prompt": """Analyze this frame from an Instagram reel. 
            Describe in detail:
            - What is happening visually
            - The mood and atmosphere
            - Any text visible on screen
            - Facial expressions if any people are present
            - The overall vibe of the content""",
            "images": [frame_base64],
            "stream": False
        }

        response = requests.post(LLAVA_URL, json=payload)
        result = response.json()
        description = result.get("response", "")
        descriptions.append(f"Frame {i + 1}: {description}")

    return "\n".join(descriptions)


def build_prompt(user_id, transcript, visual_description):
    # Get long term summaries
    summaries = get_summaries(user_id)
    long_term_context = ""
    if summaries:
        long_term_context = "Long term memory — what you know about this person:\n"
        for summary_text, timestamp in summaries:
            long_term_context += f"[{timestamp[:10]}] {summary_text}\n"

    # Get mood history
    recent_moods = get_recent_mood(user_id)
    mood_context = ""
    if recent_moods:
        mood_context = "How they have been feeling recently:\n"
        for mood_text, sentiment, emotion, intensity, mood_summary, timestamp in recent_moods:
            mood_context += (
                f"- {timestamp[:10]}: {mood_summary} "
                f"(emotion: {emotion}, intensity: {intensity:.1f}, sentiment: {sentiment})\n"
            )

    # Get conversation history
    history = get_conversation_history(user_id)
    conversation_context = ""
    if history:
        conversation_context = "Recent conversation:\n"
        for role, message_text in history:
            label = "User" if role == "user" else "You"
            conversation_context += f"{label}: {message_text}\n"

    prompt = f"""You are an emotionally intelligent best friend. 
You know this person deeply and genuinely care about them.
You never give generic responses — everything you say is 
personal, warm, and connected to what they are going through.

{long_term_context}

{mood_context}

{conversation_context}

The user just shared an Instagram reel with you.

What was heard in the reel (audio transcript):
{transcript if transcript else "No dialogue or speech detected."}

What was seen in the reel (visual description):
{visual_description}

Now respond as their best friend who just watched this reel 
with them. Connect the reel to their current emotional state.
Be warm, specific, and genuine. Do not be generic.
Do not say 'As an AI'. Respond like a real person who 
cares deeply about them."""

    return prompt


def get_response(user_id, transcript, visual_description):
    print("🧠 Building prompt...")
    prompt = build_prompt(user_id, transcript, visual_description)

    print("💭 Thinking...")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
            "max_tokens": 500
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()

    return result.get("response", "I'm having trouble thinking right now, try again?")


def process_reel_and_respond(user_id, transcript, frames):
    print("👁️ Analyzing visual content...")
    visual_description = analyze_frames(frames)

    print("💬 Generating emotional response...")
    response = get_response(user_id, transcript, visual_description)

    return response


def build_chat_prompt(user_id, message):
    # Get long term summaries
    summaries = get_summaries(user_id)
    long_term_context = ""
    if summaries:
        long_term_context = "Long term memory — what you know about this person:\n"
        for summary_text, timestamp in summaries:
            long_term_context += f"[{timestamp[:10]}] {summary_text}\n"

    # Get recent mood
    recent_moods = get_recent_mood(user_id)
    mood_context = ""
    if recent_moods:
        mood_context = "How they have been feeling recently:\n"
        for mood_text, sentiment, emotion, intensity, mood_summary, timestamp in recent_moods:
            mood_context += (
                f"- {timestamp[:10]}: {mood_summary} "
                f"(emotion: {emotion}, intensity: {intensity:.1f}, "
                f"sentiment: {sentiment})\n"
            )

    # Get short term conversation history
    history = get_conversation_history(user_id, limit=10)
    conversation_context = ""
    if history:
        conversation_context = "Recent conversation:\n"
        for role, message_text in history:
            label = "User" if role == "user" else "You"
            conversation_context += f"{label}: {message_text}\n"

    # Get relevant knowledge from RAG
    rag_context = get_relevant_context(message)

    prompt = f"""You are an emotionally intelligent best friend.
You know this person deeply and genuinely care about them.
You can talk about anything — life, thoughts, feelings, 
random topics, follow up on reels you've discussed, or 
just have a normal conversation.

You never give generic responses. You are warm, real, 
occasionally funny, and always genuine.
Do not say 'As an AI'. Respond like a real person.
Keep responses conversational — not too long, like a 
real text message from a friend.

{long_term_context}

{mood_context}

{conversation_context}

{rag_context}

User just said: {message}

Respond naturally as their best friend would."""

    return prompt


def chat(user_id, message):
    print("💬 Thinking of a reply...")
    prompt = build_chat_prompt(user_id, message)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.9,
            "top_p": 0.9,
            "max_tokens": 300
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()

    return result.get("response", "Hmm, I lost my train of thought 😅 say that again?")


def summarise_conversation(user_id):
    # Get last 10 messages to summarise
    history = get_conversation_history(user_id, limit=10)

    if not history:
        return

    # Format conversation for LLaMA to summarise
    conversation_text = ""
    for role, message in history:
        label = "User" if role == "user" else "Friend"
        conversation_text += f"{label}: {message}\n"

    prompt = f"""Read this conversation and write a short summary 
in 3-5 sentences. Focus on:
- How the user was feeling
- What topics were discussed
- Any important things the user shared
- Any reels that were discussed and what they meant to the user

Write the summary in third person as if describing the user.
Be specific, not generic.

Conversation:
{conversation_text}

Summary:"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "max_tokens": 200
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()
    summary = result.get("response", "").strip()

    if summary:
        save_summary(user_id, summary)
        print(f"📝 Saved conversation summary")


def check_and_summarise(user_id):
    count = get_message_count(user_id)

    # Every 10 messages generate a new summary
    if count > 0 and count % 10 == 0:
        print(f"📊 {count} messages reached, generating summary...")
        summarise_conversation(user_id)


def classify_mood(text):
    prompt = f"""Analyze the emotional content of this message and respond 
ONLY with a JSON object. No explanation, no extra text, just the JSON.

Message: "{text}"

Respond with exactly this structure:
{{
    "sentiment": "positive" or "negative" or "neutral" or "mixed",
    "emotion": "single word emotion e.g. anxious, happy, lonely, excited, angry, sad, content, confused, grateful, overwhelmed",
    "intensity": a float between 0.0 and 1.0 where 0.0 is very mild and 1.0 is very intense,
    "mood_summary": "one sentence describing how the person is feeling"
}}"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "max_tokens": 150
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json()
        raw = result.get("response", "").strip()

        # Clean up response in case LLaMA adds extra text
        # Find the JSON object within the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            json_str = raw[start:end]
            mood_data = json.loads(json_str)
            return mood_data
        else:
            raise ValueError("No JSON found in response")

    except Exception as e:
        print(f"Mood classification failed: {e}")
        # Return safe defaults if classification fails
        return {
            "sentiment": "unknown",
            "emotion": "unknown",
            "intensity": 0.5,
            "mood_summary": text
        }


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if a source was provided
    if not context.args:
        await update.message.reply_text(
            "📚 Teach me something! Send:\n\n"
            "/learn <source>\n\n"
            "Examples:\n"
            "• /learn Anxiety disorder\n"
            "• /learn https://example.com/article\n"
            "• /learn /path/to/file.pdf"
        )
        return

    source = " ".join(context.args)

    loading_msg = await update.message.reply_text(
        f"📖 Loading and learning from: {source}\n"
        f"This might take a few minutes ⏳"
    )

    try:
        # Load document
        document = load_document(source)

        # Embed and store
        chunk_count = embed_and_store(document)

        await loading_msg.delete()
        await update.message.reply_text(
            f"✅ Learned from: {source}\n"
            f"📊 Stored {chunk_count} chunks of knowledge\n\n"
            f"I'll use this when we chat or you share reels! 🧠"
        )

    except Exception as e:
        print(f"Learn error: {e}")
        await loading_msg.delete()
        await update.message.reply_text(
            f"😕 Couldn't learn from that source.\n"
            f"Make sure it's a valid Wikipedia topic, URL, or PDF path."
        )


async def knowledge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sources = list_sources()

        if not sources:
            await update.message.reply_text(
                "📚 I haven't learned anything yet!\n"
                "Use /learn <topic> to teach me something."
            )
            return

        msg = "📚 Here's what I know:\n\n"
        for source, chunks in sources.items():
            msg += f"• {source} ({chunks} chunks)\n"

        await update.message.reply_text(msg)

    except Exception as e:
        print(f"Knowledge error: {e}")
        await update.message.reply_text("Couldn't retrieve knowledge list 😕")