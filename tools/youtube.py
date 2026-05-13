# tools/youtube.py

import yt_dlp


def youtube_search(query, max_results=3, shorts=False):
    print(f"🎬 YouTube {'Shorts' if shorts else 'video'} search: {query}")

    if shorts:
        # Search directly in YouTube Shorts section
        search_query = f"ytsearch{max_results * 3}:{query} shorts"
        duration_limit = 180
    else:
        search_query = f"ytsearch{max_results * 2}:{query}"
        duration_limit = 99999

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(
                search_query,
                download=False
            )

        if not results or "entries" not in results:
            return "No YouTube videos found."

        entries = [e for e in results["entries"] if e]

        filtered = []
        for entry in entries:
            duration = entry.get("duration") or 99999
            if duration <= duration_limit:
                filtered.append(entry)
            if len(filtered) >= max_results:
                break

        if not filtered:
            filtered = entries[:max_results]

        formatted = ""
        for i, entry in enumerate(filtered):
            title = entry.get("title", "Unknown")
            url = f"https://youtube.com/watch?v={entry.get('id', '')}"
            duration = entry.get("duration", 0)
            channel = entry.get("channel", "Unknown")
            mins = int(duration) // 60
            secs = int(duration) % 60

            formatted += f"{'Short' if shorts else 'Video'} {i + 1}:\n"
            formatted += f"Title: {title}\n"
            formatted += f"Channel: {channel}\n"
            formatted += f"Duration: {mins}:{secs:02d}\n"
            formatted += f"URL: {url}\n\n"

        return formatted.strip()

    except Exception as e:
        return f"YouTube search failed: {str(e)}"