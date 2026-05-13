import re
from common.texts.forbiden_text import contains_forbidden_content


_TRIGGER_REGEX = re.compile(
    r"(?i)\b(dcstv|req|requ?est)\b(?:\s+(.*))?"
)


def extract_query(text: str):
    match = _TRIGGER_REGEX.search(text)
    if not match:
        return None, None

    trigger = match.group(1).lower()
    query = (match.group(2) or "").strip()

    query = re.sub(
        r"(?i)\b(min|admin|bang|kak|mas|mbak|dong|ya|ini|itu|nih)\b",
        "",
        query,
    )
    query = re.sub(r"[^\w\s]", "", query).strip()

    if not query:
        return trigger, ""

    if contains_forbidden_content(query):
        return trigger, None

    return trigger, query
