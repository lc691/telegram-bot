# utils/net_utils.py
import re

from urllib.parse import urlparse

import requests


def is_image_url_accessible(url: str, timeout: int = 5) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200 and r.headers.get("Content-Type", "").startswith(
            "image/"
        )
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except:
        return False


def clean_surrogates(text: str) -> str:
    """Hapus karakter surrogate ilegal dari teks UTF-8."""
    return re.sub(r"[\uD800-\uDFFF]", "", text)


def safe_caption(text: str) -> str:
    """Sanitasi caption sebelum dikirim ke Telegram."""
    if not text:
        return ""
    # Hapus surrogate pairs rusak
    text = re.sub(r"[\uD800-\uDFFF]", "", text)
    # Hapus karakter kontrol tak terlihat
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    return text.strip()
