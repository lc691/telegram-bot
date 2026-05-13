import mimetypes
import os
import requests

from configs.logging_setup import log


VPS_MATCH_URL = os.getenv(
    "IMAGE_MATCH_URL",
    "http://103.150.197.147:9000/match-image",
)


def match_image_via_vps(image_path: str, top_k: int = 5) -> dict:
    """
    Kirim gambar ke VPS image-match service.

    Kontrak:
    - raise exception jika HTTP error / timeout
    - return dict JSON jika sukses
    """

    # ==================================================
    # 1️⃣ MIME TYPE DETECTION
    # ==================================================
    mime, _ = mimetypes.guess_type(image_path)
    mime = mime or "image/jpeg"

    log.info(
        "[VPS_MATCH] send image=%s mime=%s top_k=%s",
        os.path.basename(image_path),
        mime,
        top_k,
    )

    # ==================================================
    # 2️⃣ HTTP POST (BLOCKING)
    # ==================================================
    with open(image_path, "rb") as f:
        response = requests.post(
            VPS_MATCH_URL,
            files={
                "image": (
                    os.path.basename(image_path),
                    f,
                    mime,
                )
            },
            data={"top_k": str(top_k)},
            timeout=40,
        )

    # ==================================================
    # 3️⃣ ERROR HANDLING
    # ==================================================
    try:
        response.raise_for_status()
    except requests.RequestException:
        log.exception(
            "[VPS_MATCH] request failed image=%s",
            os.path.basename(image_path),
        )
        raise

    # ==================================================
    # 4️⃣ JSON PARSE
    # ==================================================
    try:
        payload = response.json()
    except ValueError:
        log.exception(
            "[VPS_MATCH] invalid json image=%s",
            os.path.basename(image_path),
        )
        raise

    log.info(
        "[VPS_MATCH] success image=%s keys=%s",
        os.path.basename(image_path),
        list(payload.keys()),
    )

    return payload
