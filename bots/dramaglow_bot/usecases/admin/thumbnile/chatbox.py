import asyncio
import os
import mimetypes
import aiohttp

from configs.logging_setup import log


async def upload_to_catbox(
    file_path: str,
    retries: int = 3,
    base_delay: int = 2,
    max_size_mb: int = 10,
) -> str | None:
    """
    Upload file ke Catbox.
    Return URL jika sukses.
    Return None jika gagal (fallback-safe).
    """

    url = "https://catbox.moe/user/api.php"

    # =====================================================
    # STEP 1 — Size Guard
    # =====================================================
    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if size_mb > max_size_mb:
        log.warning(
            "[catbox] SKIP too large %.1fMB > %dMB",
            size_mb,
            max_size_mb,
        )
        return None

    # =====================================================
    # STEP 2 — Prepare File Data
    # =====================================================
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"

    filename = os.path.basename(file_path)

    # baca sekali (thumbnail kecil jadi aman)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    timeout = aiohttp.ClientTimeout(total=60)

    # =====================================================
    # STEP 3 — Retry Loop
    # =====================================================
    async with aiohttp.ClientSession(timeout=timeout) as session:

        for attempt in range(1, retries + 1):
            try:
                form = aiohttp.FormData()
                form.add_field("reqtype", "fileupload")
                form.add_field(
                    "fileToUpload",
                    file_bytes,
                    filename=filename,
                    content_type=content_type,
                )

                async with session.post(url, data=form) as resp:
                    text = (await resp.text()).strip()

                    if resp.status == 200 and text.startswith("http"):
                        log.info(
                            "[catbox] SUCCESS attempt=%d url=%s",
                            attempt,
                            text,
                        )
                        return text

                    # Non-HTTP response (likely error message)
                    log.warning(
                        "[catbox] FAIL attempt=%d status=%s body=%s",
                        attempt,
                        resp.status,
                        text[:200],
                    )

            except asyncio.TimeoutError:
                log.warning("[catbox] TIMEOUT attempt=%d", attempt)

            except Exception as e:
                log.warning(
                    "[catbox] ERROR attempt=%d err=%s",
                    attempt,
                    e,
                )

            # Exponential backoff
            if attempt < retries:
                delay = base_delay * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

    # =====================================================
    # ALL FAILED
    # =====================================================
    log.error("[catbox] ALL ATTEMPTS FAILED file=%s", filename)
    return None
