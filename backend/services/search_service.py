# services/search_service.py

import os
from tavily import TavilyClient


client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


async def web_search(query: str) -> str:
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
    )

    results = []

    for item in response.get("results", []):
        results.append(
            f"""
Title: {item.get('title')}

Content:
{item.get('content')}

Source:
{item.get('url')}
"""
        )

    return "\n\n".join(results)