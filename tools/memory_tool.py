# tools/memory_tool.py

from mood import get_recent_mood, get_conversation_history, get_summaries
from rag.retriever import get_relevant_context
from rag.embedder import embed_and_store
from rag.loader import load_webpage


def get_mood_summary(user_id):
    print(f"🧠 Retrieving mood history...")

    recent_moods = get_recent_mood(user_id, limit=5)

    if not recent_moods:
        return "No mood history found for this user."

    formatted = "Recent mood history:\n"
    for mood_text, sentiment, emotion, intensity, mood_summary, timestamp in recent_moods:
        formatted += (
            f"- {timestamp[:10]}: {mood_summary} "
            f"(emotion: {emotion}, "
            f"intensity: {intensity:.1f}, "
            f"sentiment: {sentiment})\n"
        )

    return formatted.strip()


def get_conversation_summary(user_id):
    print(f"🧠 Retrieving conversation summaries...")

    summaries = get_summaries(user_id)

    if not summaries:
        return "No conversation summaries found."

    formatted = "Long term memory summaries:\n"
    for summary_text, timestamp in summaries:
        formatted += f"[{timestamp[:10]}] {summary_text}\n"

    return formatted.strip()


def search_conversation_history(user_id, keyword):
    print(f"🧠 Searching conversation history for: {keyword}")

    history = get_conversation_history(user_id, limit=50)

    if not history:
        return "No conversation history found."

    matches = []
    keyword_lower = keyword.lower()

    for role, message in history:
        if keyword_lower in message.lower():
            matches.append({
                "role": role,
                "message": message
            })

    if not matches:
        return f"No conversations found containing '{keyword}'"

    formatted = f"Conversations mentioning '{keyword}':\n"
    for match in matches[:5]:
        label = "You" if match["role"] == "user" else "Luma"
        formatted += f"{label}: {match['message'][:200]}\n\n"

    return formatted.strip()


def search_knowledge(query):
    print(f"📚 Searching knowledge base: {query}")

    context = get_relevant_context(query)

    if not context:
        return "No relevant knowledge found in the database."

    return context


def save_to_knowledge(content, source="agent_discovered"):
    print(f"💾 Saving to knowledge base from: {source}")

    try:
        document = {
            "source": source,
            "type": "agent_discovered",
            "content": content
        }

        chunk_count = embed_and_store(document)

        return f"Successfully saved {chunk_count} chunks from {source} to knowledge base."

    except Exception as e:
        return f"Failed to save to knowledge base: {str(e)}"