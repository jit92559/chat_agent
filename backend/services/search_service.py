import os

from tavily import TavilyClient
from fastapi.concurrency import run_in_threadpool


client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


async def web_search(query: str) -> str:
    def _search():
        return client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
        )

    response = await run_in_threadpool(_search)

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