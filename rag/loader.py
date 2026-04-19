# rag/loader.py

import wikipedia
import requests
from pypdf import PdfReader
import os


def load_pdf(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    print(f"📄 Loaded PDF: {file_path} ({len(reader.pages)} pages)")
    return {
        "source": file_path,
        "type": "pdf",
        "content": text.strip()
    }

def load_wikipedia(topic):
    try:
        page = wikipedia.page(topic, auto_suggest=True)
        print(f"📖 Loaded Wikipedia: {page.title}")
        return {
            "source": f"wikipedia:{page.title}",
            "type": "wikipedia",
            "content": page.content
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Topic matches multiple articles
        # Use the first suggestion
        page = wikipedia.page(e.options[0])
        print(f"📖 Loaded Wikipedia: {page.title}")
        return {
            "source": f"wikipedia:{page.title}",
            "type": "wikipedia",
            "content": page.content
        }
    except wikipedia.exceptions.PageError:
        raise ValueError(f"Wikipedia page not found: {topic}")


def load_webpage(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; MoodMateBot/1.0)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Basic HTML stripping
        text = response.text

        # Remove script and style tags
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        print(f"🌐 Loaded webpage: {url}")
        return {
            "source": url,
            "type": "webpage",
            "content": text
        }
    except Exception as e:
        raise ValueError(f"Failed to load webpage: {e}")

def load_document(source):
    if source.startswith("http://") or source.startswith("https://"):
        return load_webpage(source)
    elif source.endswith(".pdf"):
        return load_pdf(source)
    else:
        # Assume it's a Wikipedia topic
        return load_wikipedia(source)