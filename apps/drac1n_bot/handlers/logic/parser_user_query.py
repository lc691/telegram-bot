from urllib.parse import parse_qs


def parse_query_params(raw_query: str):
    if not raw_query:
        return {}
    parsed = parse_qs(raw_query.strip("?"))
    return {
        "offset": int(parsed.get("offset", [0])[0]),
        "vip": parsed.get("vip", ["false"])[0].lower() == "true",
        "search": parsed.get("search", [None])[0],
    }
