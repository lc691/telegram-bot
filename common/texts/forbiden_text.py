import re

# =========================
# 🔒 Deteksi Konten Terlarang
# =========================
FORBIDDEN_PATTERNS = [
    r"\bagama\b",
    r"\b(islam|kristen|budha|hindu|yahudi|nasrani|syiah|atheis|zionis|israel|palestina)\b",
    r"\b(peli|kontol|memek|memew|jembut)\b",
    r"\bkafir\b",
    r"\bpribumi\b",
    r"\bnonpribumi\b",
    r"\b(hitam|putih|cina|arab|jawa|batak|sunda|minoritas|mayoritas)\b",
    r"\bsalib\b",
    r"\bustadz\b",
    r"\bpendeta\b",
    r"\bsara\b",
]

def contains_forbidden_content(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in FORBIDDEN_PATTERNS)