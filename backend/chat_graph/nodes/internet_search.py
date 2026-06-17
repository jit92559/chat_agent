# graph/nodes/internet_search.py

from services.search_service import web_search


async def internet_search_node(state):
    try:
        query = state["input_text"]

        search_results = await web_search(query)

        return {
            "web_results": search_results,
            "context": "",
            "status": "web_search_success",
            "error": None,
        }

    except Exception as e:
        return {
            "web_results": "",
            "context": "",
            "status": "web_search_failed",
            "error": str(e),
        }