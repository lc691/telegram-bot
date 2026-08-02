from typing import Optional, Iterable

from config import DEFAULT_THUMBNAIL_URL
from configs.logging_setup import log
from database.connection import get_db_cursor


# =====================================================
# TEXT UTIL
# =====================================================
def sanitize_utf8(text: str) -> str:
    """
    Pastikan string aman dikirim ke Telegram (UTF-8 clean).
    """
    if not text:
        return ""
    return text.encode("utf-8", "ignore").decode("utf-8", "ignore")


# =====================================================
# THUMBNAIL RESOLVER
# =====================================================
async def resolve_thumbnail(thumbnail: Optional[str]) -> str:

    if not thumbnail:
        return DEFAULT_THUMBNAIL_URL  # pastikan ini URL

    return thumbnail


# =====================================================
# SHOW DATA ACCESS
# =====================================================
def fetch_show_by_id(show_id: int):
    if not show_id:
        return None

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.title,
                    s.sinopsis,
                    COALESCE(s.thumbnail_url, s.thumbnail) AS thumbnail,
                    s.genre,
                    s.hashtags,
                    s.is_adult,
                    rs.code,
                    rs.label
                FROM shows s
                LEFT JOIN request_sources rs
                    ON s.source_id = rs.id
                WHERE s.id = %s
                """,
                (show_id,),
            )
            return cursor.fetchone()

    except Exception:
        log.exception("[fetch_show_by_id] query failed")
        return None


def search_show_by_title(title: str):
    if not title:
        return []

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.title,
                    s.series_no,
                    rs.label
                FROM shows s
                LEFT JOIN request_sources rs
                    ON s.source_id = rs.id
                WHERE lower(s.title) = lower(%s)
                ORDER BY s.id DESC
                """,
                (title.strip(),),
            )

            return cursor.fetchall()

    except Exception:
        log.exception("[search_show_by_title] query failed")
        return []


def fetch_shows_for_inline(query: str) -> list[tuple]:
    """
    Inline query helper.
    Return: list of (id, title, thumbnail)
    """
    try:
        with get_db_cursor() as (cursor, _):
            if query:
                cursor.execute(
                    """
                    SELECT id, title, thumbnail
                    FROM shows
                    WHERE title ILIKE %s
                    ORDER BY id DESC
                    LIMIT 20
                    """,
                    (f"%{query.strip()}%",),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, title, thumbnail
                    FROM shows
                    ORDER BY created_at DESC
                    LIMIT 10
                    """
                )

            return cursor.fetchall()

    except Exception:
        log.exception("[fetch_shows_for_inline] query failed")
        return []


# =====================================================
# FILE ACCESS
# =====================================================
def fetch_files_by_show(show_id: int) -> list[tuple]:
    if not show_id:
        return []

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT file_name, free_hash, paid_hash
                FROM files
                WHERE show_id = %s
                ORDER BY file_name ASC
                """,
                (show_id,),
            )
            return cursor.fetchall()

    except Exception:
        log.exception(
            "[fetch_files_by_show] query failed show_id=%s",
            show_id,
        )
        return []


# =====================================================
# PARSE POST
# =====================================================
def parse_batch_ids(raw: str):
    """
    Support:
    [1,2,3]
    [1-5]
    [1-3,7,10-12]
    """
    result = set()

    parts = [p.strip() for p in raw.split(",") if p.strip()]

    for part in parts:
        # Range case
        if "-" in part:
            start, end = part.split("-", 1)

            if start.isdigit() and end.isdigit():
                start_i = int(start)
                end_i = int(end)

                if start_i <= end_i:
                    for i in range(start_i, end_i + 1):
                        result.add(i)
        # Single ID
        elif part.isdigit():
            result.add(int(part))

    return sorted(result)
