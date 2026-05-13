import re


def normalize_for_match(text: str) -> str:
    """
    Dipakai HANYA untuk matching.
    Judul asli tetap disimpan apa adanya.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)   # buang ! ? , . : dll
    text = re.sub(r"\s+", " ", text).strip()
    return f"%{text.replace(' ', '%')}%"
