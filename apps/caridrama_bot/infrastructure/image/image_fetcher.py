# infrastructure/image/image_fetcher.py
"""
Image fetcher utility untuk image-matching pipeline.
- Download gambar dengan retry & timeout
- Validasi ukuran file
- Resize hemat memori
- Aman dipakai di thread (non-async)
"""

from __future__ import annotations

import io
import time

from typing import Optional

import requests

from PIL import Image

from configs.logging_setup import log

# ==========================================================
# === Konstanta ============================================
# ==========================================================

MAX_IMG_FILESIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMG_SIZE = 512  # sisi terpanjang
REQUEST_TIMEOUT = 8
REQUEST_RETRIES = 2

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# ==========================================================
# === Public API ===========================================
# ==========================================================


def fetch_image(
    url: str,
    *,
    retries: int = REQUEST_RETRIES,
    timeout: int = REQUEST_TIMEOUT,
    max_filesize: int = MAX_IMG_FILESIZE,
    max_size: int = MAX_IMG_SIZE,
) -> Optional[Image.Image]:
    """
    Download image dari URL dan return PIL.Image (RGB).

    - Return None jika gagal / invalid
    - Aman dipanggil dari ThreadPool
    """

    if not url:
        return None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=timeout,
            )
            resp.raise_for_status()

            if len(resp.content) > max_filesize:
                log.warning(
                    "[IMG-FETCH] ⚠️ Skip >%sMB | %s",
                    max_filesize // (1024 * 1024),
                    url,
                )
                return None
            
            img = Image.open(io.BytesIO(resp.content)).convert("RGB").copy()
            # Resize hemat memori
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size))

            return img

        except Exception as e:
            log.warning(
                "[IMG-FETCH] ⚠️ Failed (%s/%s) | %s | %s",
                attempt,
                retries,
                url,
                e,
            )
            time.sleep(0.3)

    return None


# ==========================================================
# === Helpers ==============================================
# ==========================================================


def is_valid_image(img: Image.Image | None) -> bool:
    """Validasi ringan image object."""
    return img is not None and hasattr(img, "size") and min(img.size) > 0
