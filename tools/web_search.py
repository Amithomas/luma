# tools/web_search.py

from duckduckgo_search import DDGS


def web_search(query, max_results=3):
    print(f"🔍 Web search: {query}")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                max_results=max_results
            ))

        if not results:
            return "No results found for that search."

        formatted = ""
        for i, r in enumerate(results):
            formatted += f"Result {i + 1}:\n"
            formatted += f"Title: {r.get('title', '')}\n"
            formatted += f"Summary: {r.get('body', '')}\n"
            formatted += f"URL: {r.get('href', '')}\n\n"

        return formatted.strip()

    except Exception as e:
        return f"Search failed: {str(e)}"