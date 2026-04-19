# rag/retriever.py

import requests
from config import EMBEDDING_MODEL, RAG_TOP_K
from rag.embedder import get_chroma_client, get_collection, get_embedding


def retrieve(query, top_k=RAG_TOP_K):
    client = get_chroma_client()
    collection = get_collection(client)

    print(f"🔍 Searching knowledge base for: '{query[:50]}...'")
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "type": results["metadatas"][0][i]["type"],
            "distance": results["distances"][0][i]
        })

    return chunks


def format_retrieved_context(chunks, min_relevance=0.7):
    if not chunks:
        return ""

    relevant = [c for c in chunks if c["distance"] < min_relevance]

    if not relevant:
        return ""

    context = "Relevant knowledge:\n"
    for chunk in relevant:
        context += f"\n[From {chunk['source']}]\n"
        context += f"{chunk['text']}\n"
        context += "---\n"

    return context


def get_relevant_context(query):
    chunks = retrieve(query)
    context = format_retrieved_context(chunks)

    if context:
        print(f"📚 Found {len(chunks)} relevant chunks")
    else:
        print(f"📚 No relevant knowledge found for this query")

    return context