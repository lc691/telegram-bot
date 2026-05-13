# dcst_mbot/utils/text_normalizer.py
import re


def normalize_for_match(text: str) -> str:
    """
    HANYA untuk SQL LIKE matching.
    """
    cleaned = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return f"%{cleaned.replace(' ', '%')}%"
