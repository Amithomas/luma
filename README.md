# Luma 🌟

> An emotionally intelligent AI companion that watches reels with you and actually gets how you feel.

Luma is a multimodal AI companion built on a fully local stack — no cloud APIs, no data leaving your machine. Share an Instagram reel and Luma analyzes the audio, video frames, and your emotional context to respond like a friend who genuinely knows you.

---

## Features

- 🎬 **Multimodal reel analysis** — downloads Instagram reels, extracts key video frames and transcribes audio
- 👁️ **Vision understanding** — LLaVA analyzes video frames to understand visual content
- 🎤 **Audio transcription** — Whisper converts speech to text locally
- ❤️ **Emotional memory** — tracks your mood over time with structured sentiment and emotion classification
- 🧠 **Long term memory** — automatically summarizes past conversations so Luma remembers you across sessions
- 📚 **RAG knowledge base** — teach Luma from PDFs, Wikipedia articles, or web pages
- 💬 **Natural conversation** — chat about anything, not just reels
- 🔒 **100% local** — everything runs on your machine via Ollama

---

## Architecture

```
You (Telegram)
      │
      ▼
   bot.py — receives messages, routes logic
      │
      ├── Instagram URL
      │       │
      │   reel.py
      │   ├── yt-dlp      → download reel
      │   ├── OpenCV      → extract frames
      │   └── Whisper     → transcribe audio
      │
      ├── Plain text
      │       │
      │   mood.py → classify + store mood
      │   SQLite  → conversations, moods, summaries
      │
      └── brain.py — assembles prompt + calls models
              │
              ├── LLaVA 7B    → visual description
              ├── LLaMA 3.1 8B → emotional response
              └── RAG retriever → relevant knowledge
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | LLaMA 3.1 8B via Ollama |
| Vision model | LLaVA 7B via Ollama |
| Transcription | faster-whisper (base) |
| Embeddings | nomic-embed-text via Ollama |
| Vector database | ChromaDB |
| Memory | SQLite |
| Bot framework | python-telegram-bot |
| Video processing | yt-dlp + OpenCV |

---

## Prerequisites

- Mac with Apple Silicon (M1/M2/M3) or a machine with a CUDA GPU
- [Ollama](https://ollama.com) installed
- Python 3.10+
- Telegram account

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/luma.git
cd luma
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Pull Ollama models**
```bash
ollama pull llama3.1:8b
ollama pull llava:7b
ollama pull nomic-embed-text
```

**4. Configure**
```bash
cp config.example.py config.py
```
Edit `config.py` and add your Telegram bot token from [@BotFather](https://t.me/botfather)

**5. Start Ollama**
```bash
ollama serve
```

**6. Run Luma**
```bash
python bot.py
```

---

## Usage

| Command | What it does |
|---|---|
| `/start` | Introduce yourself to Luma |
| `/mood` | Tell Luma how you're feeling |
| `/learn <topic>` | Teach Luma from Wikipedia, a URL, or a PDF |
| `/knowledge` | See what Luma has learned |
| Send any text | Have a natural conversation |
| Send an Instagram reel URL | Get an emotionally aware response |

---

## Example

```
You: "feeling really anxious about my move to a new city"
Luma: saves structured mood → emotion: anxious, intensity: 0.7

You: https://www.instagram.com/reel/xyz
Luma: downloads reel → extracts frames → transcribes audio
      → retrieves relevant knowledge from RAG
      → responds connecting the reel to your anxiety
```

---

## Roadmap

- [x] LLM + persistent emotional memory
- [x] Multimodal reel analysis (audio + video)
- [x] Structured mood classification
- [x] Long term memory via conversation summarisation
- [x] RAG knowledge base
- [ ] Agentic tools — web search, weather, YouTube
- [ ] Autonomous proactive suggestions
- [ ] GCP Cloud Run deployment
- [ ] Instagram DM integration

---

## Local Models

Luma runs entirely on your machine — no OpenAI, no Anthropic, no data sent to the cloud.

| Model | Purpose | Size |
|---|---|---|
| llama3.1:8b | Conversation + reasoning | ~5GB |
| llava:7b | Video frame analysis | ~4GB |
| nomic-embed-text | RAG embeddings | ~270MB |
| faster-whisper base | Audio transcription | ~150MB |

---

## Author

Built by Amith — [LinkedIn](https://linkedin.com/in/YOUR_LINKEDIN) · [GitHub](https://github.com/YOUR_USERNAME)