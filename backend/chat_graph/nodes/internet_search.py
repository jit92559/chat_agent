# graph/nodes/internet_search.py

from services.search_service import web_search


async def internet_search_node(state):
    print("i am at internet_search_node")
    try:
        query = state["input_text"]

        search_results = await web_search(query)
        print("serach_result:",search_results)
        return {
            "web_results": search_results,
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