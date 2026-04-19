# config.example.py
# Copy this to config.py and fill in your values

TELEGRAM_BOT_TOKEN = "your-telegram-bot-token-here"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
DB_PATH = "memory.db"
CHROMA_DB_PATH = "chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 3