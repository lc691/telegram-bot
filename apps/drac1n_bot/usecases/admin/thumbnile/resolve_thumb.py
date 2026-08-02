from typing import Tuple

from pyrogram.types import Message

from configs.logging_setup import log
from database.connection import get_db_cursor


async def resolve_show_from_caption(
    message: Message,
) -> Tuple[int, str, str | None, int]:
    """
    Resolve show berdasarkan caption:

    - Judul
    - Judul | SourceCode
    - Judul | SourceCode | Series

    Return:
        show_id, title, source_code, series_no
    """

    # =====================================================
    # STEP 1 — Validasi Caption
    # =====================================================
    if not message.caption:
        raise ValueError(
            "Gunakan format:\n"
            "Judul\n"
            "Judul | SourceCode\n"
            "Judul | SourceCode | Series"
        )

    caption = message.caption.replace("｜", "|")
    parts = [p.strip() for p in caption.split("|") if p.strip()]

    title = parts[0]
    source_code = parts[1].lower() if len(parts) >= 2 else None
    series_no = None

    if len(parts) >= 3:
        try:
            series_no = int(parts[2])
        except ValueError:
            raise ValueError("Series harus berupa angka")

    # =====================================================
    # STEP 2 — Query Join ke request_sources
    # =====================================================
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT s.id,
                   s.title,
                   s.series_no,
                   rs.code
            FROM shows s
            LEFT JOIN request_sources rs
                   ON s.source_id = rs.id
            WHERE lower(s.title) = lower(%s)
            ORDER BY rs.code, s.series_no
            """,
            (title,),
        )
        rows = cursor.fetchall()

    if not rows:
        raise ValueError(f"Drama '{title}' tidak ditemukan")

    # =====================================================
    # CASE 1 — Hanya 1 show total
    # =====================================================
    if len(rows) == 1:
        show_id, db_title, ser, db_source_code = rows[0]

        # Jika user memberikan source_code di caption → pakai itu
        final_source_code = source_code or db_source_code

        log.info(
            "[resolve] AUTO title=%s source=%s series=%s",
            db_title,
            final_source_code,
            ser,
        )

        return show_id, db_title, final_source_code, ser

    # =====================================================
    # CASE 2 — Banyak source → source wajib
    # =====================================================
    if source_code is None:
        available_sources = sorted({r[3] for r in rows if r[3]})
        raise ValueError(
            "Judul ini ada di beberapa source:\n"
            f"{', '.join(available_sources)}\n\n"
            "Gunakan: Judul | SourceCode"
        )

    filtered = [r for r in rows if r[3] and r[3].lower() == source_code]

    if not filtered:
        raise ValueError(f"Source '{source_code}' tidak ditemukan untuk judul ini")

    # =====================================================
    # CASE 3 — Source unik
    # =====================================================
    if len(filtered) == 1:
        show_id, db_title, ser, db_source_code = filtered[0]
        log.info(
            "[resolve] AUTO source title=%s source=%s series=%s",
            db_title,
            db_source_code,
            ser,
        )
        return show_id, db_title, db_source_code, ser

    # =====================================================
    # CASE 4 — Banyak series → series wajib
    # =====================================================
    if series_no is None:
        available_series = sorted({r[2] for r in filtered})
        raise ValueError(
            f"Source '{source_code}' punya beberapa series:\n"
            f"{', '.join(map(str, available_series))}\n\n"
            "Gunakan: Judul | SourceCode | Series"
        )

    match = next((r for r in filtered if r[2] == series_no), None)

    if not match:
        available_series = sorted({r[2] for r in filtered})
        raise ValueError(
            f"Series {series_no} tidak ditemukan.\n"
            f"Tersedia: {', '.join(map(str, available_series))}"
        )

    show_id, db_title, ser, db_source_code = match

    log.info(
        "[resolve] EXACT title=%s source=%s series=%s",
        db_title,
        db_source_code,
        ser,
    )

    return show_id, db_title, db_source_code, ser
