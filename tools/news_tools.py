"""News retrieval tools for J.A.R.V.I.S.

Provides access to current news headlines on any topic using DuckDuckGo news search.
"""

from fury import create_tool


def news_tool():
    """Create a tool for retrieving current news headlines.
    
    Gets latest news from DuckDuckGo news search on specified topics.
    
    Returns:
        Fury tool object for news retrieval
    """
    def get_news(topic: str = "top news", max_results: int = 6):
        """Get the latest news headlines on any topic.
        
        Args:
            topic: News topic or keyword (default: 'top news')
            max_results: Number of headlines to return (default: 6)
            
        Returns:
            Dict with topic and list of headline dicts (title, source, date, url, summary)
        """
        try:
            from duckduckgo_search import DDGS
            headlines = []
            with DDGS() as ddgs:
                for r in ddgs.news(topic, max_results=max_results):
                    headlines.append({
                        "title":   r.get("title", ""),
                        "source":  r.get("source", ""),
                        "date":    r.get("date", ""),
                        "url":     r.get("url", ""),
                        "summary": r.get("body", ""),
                    })
            return {"topic": topic, "headlines": headlines}
        except Exception as e:
            return {"topic": topic, "headlines": [], "error": str(e)}

    return create_tool(
        id="get_news",
        description="Get the latest news headlines on any topic",
        execute=get_news,
        input_schema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "News topic or keyword (default: 'top news')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of headlines to return (default 6)",
                },
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "topic":     {"type": "string"},
                "headlines": {"type": "array"},
            },
            "required": ["topic", "headlines"],
        },
    )