from .cache import (
    get_cached_search,
    set_cached_search,
    is_user_on_cooldown,
)
from .policies import extract_query
from .group_search_adapter import (
    search_shows_for_group,
)


async def run_group_search_flow(*, text: str, user_id: int):
    trigger, query = extract_query(text)

    if trigger is None:
        return None

    if query is None:
        return {"error": "forbidden"}

    if not query:
        return {"error": "empty", "trigger": trigger}

    if is_user_on_cooldown(user_id):
        return {"error": "cooldown"}

    results = get_cached_search(query)
    if not results:
        results = await search_shows_for_group(
            query=query,
            user_id=user_id,
            limit=10,
        )
        set_cached_search(query, results)

    return {
        "query": query,
        "results": results,
    }
