import html
import re
from typing import Optional, Literal


def safe(text: Optional[str]) -> str:
    return html.escape(text or "")

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()

def highlight_query_adaptive(
    title: str,
    query: str,
    *,
    device: Literal["mobile", "desktop"] = "mobile",
) -> str:
    """
    Adaptive highlight (FINAL + FULL MATCH):

    Priority rules:
    1️⃣ Jika query == title (normalized) → highlight FULL title
    2️⃣ Else → token-based adaptive highlight
    """

    title_safe = safe(title)
    query = query.strip()

    if not query or not title:
        return title_safe

    # ==================================================
    # 0️⃣ FULL TITLE MATCH (PRIORITAS PALING ATAS)
    # ==================================================
    def _normalize(text: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            re.sub(r"[^\w\s]", "", text.lower()),
        ).strip()

    if _normalize(query) == _normalize(title):
        # Highlight seluruh judul
        return f"【{title_safe}】"

    # ==================================================
    # 1️⃣ TOKEN EXTRACTION
    # ==================================================
    tokens = [
        w.lower()
        for w in re.findall(r"\w+", query)
        if len(w) >= 3
    ]

    if not tokens:
        return title_safe

    tokens.sort(key=len, reverse=True)

    # ==================================================
    # 2️⃣ FILTER TOKEN YANG ADA DI TITLE
    # ==================================================
    title_lower = title.lower()
    matched_tokens = [t for t in tokens if t in title_lower]

    if not matched_tokens:
        return title_safe

    # ==================================================
    # 3️⃣ BATAS HIGHLIGHT
    # ==================================================
    max_hits = 1 if device == "mobile" else 2
    keywords = matched_tokens[:max_hits]

    # ==================================================
    # 4️⃣ REGEX AMAN
    # ==================================================
    pattern = re.compile(
        r"(" + "|".join(map(re.escape, keywords)) + ")",
        re.IGNORECASE,
    )

    hits = 0

    def replacer(match):
        nonlocal hits
        if hits >= max_hits:
            return match.group(0)
        hits += 1
        return f"【{match.group(0)}】"

    # ==================================================
    # 5️⃣ APPLY
    # ==================================================
    return pattern.sub(replacer, title_safe)
