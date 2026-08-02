# =====================================================
# Telegram / Runtime Settings
# =====================================================

ALLOWED_CHAT_IDS = {
    -1003754267431,  # Dramamint GRUP
    -1003752336498,  # Dramaglow GRUP
    -1003738715410,  # Dramaglow
    -1003529839254,  # DramaMint
    -1003721964537,  # Posting Utama
    -1002515868345,
    -1002750559395,
    -1002593474221,
    -1003701890250,
}

MAX_IMG_FILESIZE = 5 * 1024 * 1024  # 5 MB


# =====================================================
# Image Match Thresholds
# =====================================================

CONFIDENT_THRESHOLD = 0.85  # similarity langsung dianggap match
MIN_ACCEPT_THRESHOLD = 0.78  # minimal untuk dipertimbangkan
AMBIGUITY_GAP = 0.03  # selisih similarity untuk ambiguity


# =====================================================
# OCR Fallback Settings
# =====================================================

OCR_MAX_HITS = 5  # ⬅️ FIX ERROR (WAJIB)
OCR_MIN_TEXT_LENGTH = 3  # optional, future-proof


# =====================================================
# Rate Limit Settings
# =====================================================

RATE_LIMIT = 3  # max request
WINDOW = 30  # detik


DEFAULT_THUMBNAIL_URL = "https://files.catbox.moe/c6vyt0.jpg"
INLINE_LIMIT = 20

EMBED_MIN_SIMILARITY = 0.30
