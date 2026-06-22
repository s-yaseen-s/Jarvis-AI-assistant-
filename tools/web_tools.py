import re
import httpx
from fury import create_tool


def fetch_page_tool():
    def fetch_page(url: str, max_chars: int = 8000):
        """Fetch a URL and return its cleaned text content."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text

            # Strip <script>, <style>, <nav>, <footer>, <header> blocks
            for tag in ("script", "style", "nav", "footer", "header", "noscript", "svg"):
                html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", html, flags=re.DOTALL | re.IGNORECASE)

            # Strip all remaining HTML tags
            text = re.sub(r"<[^>]+>", " ", html)

            # Decode HTML entities
            import html as html_mod
            text = html_mod.unescape(text)

            # Collapse whitespace
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

            # Truncate
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n[... truncated at {max_chars} chars]"

            return {"success": True, "url": url, "content": text, "length": len(text)}
        except Exception as e:
            return {"success": False, "url": url, "error": str(e)}

    return create_tool(
        id="fetch_page",
        description=(
            "Fetch the full text content of any URL. Use this after web_search to actually READ "
            "the content of a page — tutorials, code examples, documentation, articles. "
            "web_search only gives snippets; fetch_page gives you the full content to learn from."
        ),
        execute=fetch_page,
        input_schema={
            "type": "object",
            "properties": {
                "url":       {"type": "string",  "description": "Full URL to fetch"},
                "max_chars": {"type": "integer", "description": "Max characters to return (default 8000)"},
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "url":     {"type": "string"},
                "content": {"type": "string"},
                "length":  {"type": "integer"},
            },
            "required": [],
        },
    )


def web_search_tool():
    def web_search(query: str, max_results: int = 5):
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            return {"query": query, "results": results}
        except Exception as e:
            return {"query": query, "results": [], "error": str(e)}

    return create_tool(
        id="web_search",
        description="Search the web for up-to-date information using DuckDuckGo",
        execute=web_search,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Number of results to return (default 5)"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "results": {"type": "array"},
            },
            "required": ["query", "results"],
        },
    )


def get_weather_tool():
    def get_weather(location: str):
        try:
            resp = httpx.get(f"https://wttr.in/{location}?format=j1", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            cur = data["current_condition"][0]
            return {
                "location": location,
                "temperature_c": cur["temp_C"],
                "temperature_f": cur["temp_F"],
                "feels_like_c": cur["FeelsLikeC"],
                "humidity_percent": cur["humidity"],
                "description": cur["weatherDesc"][0]["value"],
                "wind_speed_kmph": cur["windspeedKmph"],
                "visibility_km": cur["visibility"],
            }
        except Exception as e:
            return {"location": location, "error": str(e)}

    return create_tool(
        id="get_weather",
        description="Get current weather conditions for any city or location",
        execute=get_weather,
        input_schema={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or location name, e.g. 'London' or 'New York'"},
            },
            "required": ["location"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "temperature_c": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["location"],
        },
    )
