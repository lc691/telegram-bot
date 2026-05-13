import os
import time
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from configs.logging_setup import log
from db.connect import get_db_cursor

from .chatbox import upload_to_catbox
from .resolve_thumb import resolve_show_from_caption


def _versioned_url(url: str) -> str:
    """
    Tambahkan parameter ?v=timestamp (millisecond)
    untuk memastikan URL selalu berubah (embed reset-safe).
    """
    ts = int(time.time() * 1000)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    qs["v"] = [str(ts)]
    return urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))


async def update_thumbnail_flow(*, client, message):

    file_path = None
    public_url = None
    mode = "telegram_only"

    # =====================================================
    # 1. Resolve Show (source_code based)
    # =====================================================
    show_id, title, source_code, series_no = await resolve_show_from_caption(message)

    # =====================================================
    # 2. Validate & Extract Telegram file_id
    # =====================================================
    if message.photo:
        file_id = message.photo.file_id
    elif (
        message.document
        and message.document.file_name
        and message.document.file_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )
    ):
        file_id = message.document.file_id
    else:
        raise ValueError("File harus berupa gambar")

    # =====================================================
    # 3. Download Telegram File
    # =====================================================
    file_path = await client.download_media(file_id)

    if not file_path or not os.path.isfile(file_path):
        raise ValueError("Gagal download file")

    # =====================================================
    # 4. Upload Catbox (Optional)
    # =====================================================
    try:
        raw_url = await upload_to_catbox(file_path)
        if raw_url:
            public_url = _versioned_url(raw_url)
            mode = "full"
    except Exception:
        log.warning("[THUMBNAIL] Catbox failed", exc_info=True)

    # =====================================================
    # 5. Atomic Transaction (Safe & Conditional Source)
    # =====================================================
    with get_db_cursor(commit=True) as (cursor, _):

        # 5.1 Lock row show saja
        cursor.execute(
            """
            SELECT source_id
            FROM shows
            WHERE id = %s
            FOR UPDATE
            """,
            (show_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError("Show tidak ditemukan")

        current_source_id = row[0]

        # 5.2 Tentukan source_id final
        if current_source_id:
            final_source_id = current_source_id
        else:
            if not source_code:
                raise ValueError(
                    "Show belum memiliki source dan tidak ada source_code dari caption"
                )

            cursor.execute(
                """
                INSERT INTO request_sources (code, label)
                VALUES (%s, %s)
                ON CONFLICT (code)
                DO UPDATE SET code = EXCLUDED.code
                RETURNING id
                """,
                (source_code, source_code),
            )
            final_source_id = cursor.fetchone()[0]

        # 5.3 Update show
        if public_url:
            cursor.execute(
                """
                UPDATE shows
                SET thumbnail = %s,
                    thumbnail_url = %s,
                    source_id = %s
                WHERE id = %s
                RETURNING id
                """,
                (file_id, public_url, final_source_id, show_id),
            )
        else:
            cursor.execute(
                """
                UPDATE shows
                SET thumbnail = %s,
                    source_id = %s
                WHERE id = %s
                RETURNING id
                """,
                (file_id, final_source_id, show_id),
            )

        if not cursor.fetchone():
            raise ValueError("Update gagal")

        # 5.4 Ambil label (tanpa lock)
        cursor.execute(
            "SELECT label FROM request_sources WHERE id = %s",
            (final_source_id,),
        )
        label_row = cursor.fetchone()
        source_label = label_row[0] if label_row else source_code

    log.info(
        "[THUMBNAIL_UPDATED] id=%s mode=%s source=%s",
        show_id,
        mode,
        source_code,
    )

    return {
        "title": title,
        "series_no": series_no,
        "source_label": source_label,
        "url": public_url,
        "mode": mode,
    }, file_path
