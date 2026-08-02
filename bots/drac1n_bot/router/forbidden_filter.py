import re

FORBIDDEN_PATTERNS = [
    r"\bagama\b",
    r"\b(islam|kristen|budha|hindu|yahudi|nasrani|syiah|atheis|zionis|israel|palestina)\b",
    r"\bkafir\b",
    r"\bpribumi\b",
    r"\bnonpribumi\b",
    r"\b(sara|rasis|teroris|jihad)\b",
    r"\bpeli\b",
    r"\bkontol\b",
    r"\bmemek\b",
    r"\bjembut\b",
    r"\bngentot\b",
    r"\bsex\b",
    r"\bporno\b",
    r"\bbokep\b",
    r"\bidiot\b",
    r"\bangsat\b",
    r"\bgoblok\b",
    r"\banjing\b",
    r"\btolol\b",
    r"\bpolitik\b",
]

def contains_forbidden_word(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in FORBIDDEN_PATTERNS)