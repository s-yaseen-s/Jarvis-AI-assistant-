"""Browser navigation tools — opens URLs and searches directly in the default browser."""

import urllib.parse
import webbrowser
from fury import create_tool


def open_url_tool():
    def open_url(url: str):
        url = url.strip()
        # Fix common LLM mistake: "file///" or "file//" without the colon
        if url.startswith("file///") or url.startswith("file//"):
            url = "file:///" + url.lstrip("file/")
        # Convert backslashes in file paths to forward slashes
        if url.startswith("file:///"):
            url = "file:///" + url[8:].replace("\\", "/")
        # If it's a local file path (C:\... or /path/...), convert to file URL
        elif len(url) > 1 and url[1] == ":" and url[0].isalpha():
            url = "file:///" + url.replace("\\", "/")
        # Anything else that's not a known scheme gets https://
        elif not url.startswith(("http://", "https://", "file://", "ftp://")):
            url = "https://" + url
        webbrowser.open(url)
        return {"success": True, "url": url}

    return create_tool(
        id="open_url",
        description=(
            "Open any URL directly in the default browser. "
            "Use this instead of open_application when navigating to websites."
        ),
        execute=open_url,
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to open (e.g. https://youtube.com)"},
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {"success": {"type": "boolean"}, "url": {"type": "string"}},
            "required": ["success"],
        },
    )


def youtube_search_tool():
    def youtube_search(query: str):
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return {"success": True, "url": url, "query": query}

    return create_tool(
        id="youtube_search",
        description="Search YouTube and open results directly in the browser",
        execute=youtube_search,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term to look up on YouTube"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {"success": {"type": "boolean"}, "url": {"type": "string"}},
            "required": ["success"],
        },
    )


def google_search_browser_tool():
    def google_search_browser(query: str):
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return {"success": True, "url": url, "query": query}

    return create_tool(
        id="google_search_browser",
        description="Open a Google search in the browser (shows visual results page)",
        execute=google_search_browser,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query to open in Google"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {"success": {"type": "boolean"}, "url": {"type": "string"}},
            "required": ["success"],
        },
    )
