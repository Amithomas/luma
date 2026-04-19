# rag/embedder.py

import chromadb
import requests
import hashlib
from config import (CHROMA_DB_PATH, EMBEDDING_MODEL,
                    RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)


def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)


def get_collection(client):
    return client.get_or_create_collection(
        name="moodmate_knowledge",
        metadata={"hnsw:space": "cosine"}
    )


def chunk_text(text, chunk_size=RAG_CHUNK_SIZE,
               overlap=RAG_CHUNK_OVERLAP):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def get_embedding(text):
    response = requests.post(
        "http://127.0.0.1:11434/api/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text
        }
    )
    result = response.json()
    return result["embedding"]


def generate_id(source, chunk_index):
    raw = f"{source}_{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def embed_and_store(document):
    client = get_chroma_client()
    collection = get_collection(client)

    source = document["source"]
    content = document["content"]
    doc_type = document["type"]

    print(f"✂️ Chunking {source}...")
    chunks = chunk_text(content)
    print(f"   → {len(chunks)} chunks created")

    print(f"🔢 Embedding and storing chunks...")
    for i, chunk in enumerate(chunks):
        chunk_id = generate_id(source, i)
        embedding = get_embedding(chunk)

        collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{
                "source": source,
                "type": doc_type,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }]
        )

        if (i + 1) % 10 == 0:
            print(f"   → {i + 1}/{len(chunks)} chunks stored")

    print(f"✅ Stored {len(chunks)} chunks from {source}")
    return len(chunks)


def list_sources():
    client = get_chroma_client()
    collection = get_collection(client)

    results = collection.get(include=["metadatas"])

    sources = {}
    for metadata in results["metadatas"]:
        source = metadata["source"]
        if source not in sources:
            sources[source] = metadata["total_chunks"]

    return sources


def get_total_chunks():
    client = get_chroma_client()
    collection = get_collection(client)
    return collection.count()