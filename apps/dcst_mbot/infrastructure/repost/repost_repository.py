from configs.logging_setup import log
from database.connection import get_db_cursor, get_dict_cursor
from ...utils.text_normalizer import normalize_for_match


# ==================================================
# MAIN TITLE UPDATE
# ==================================================
def update_main_title_and_message_id_safe(
    *,
    title: str,
    message_id: int,
) -> None:
    original_title = title.strip()
    like_pattern = normalize_for_match(original_title)

    log.info(
        "[REPOST-REPO] Resolve title | title=%r | msg_id=%s",
        original_title,
        message_id,
    )

    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute(
            """
            SELECT ctid, file_name
            FROM files
            WHERE LOWER(file_name) LIKE %s
            """,
            (like_pattern,),
        )
        rows = cursor.fetchall()

        if not rows:
            log.warning("[REPOST-REPO] No match | title=%r", original_title)
            return

        if len(rows) > 100:
            log.error(
                "[REPOST-REPO] ABORT update | match=%d | title=%r",
                len(rows),
                original_title,
            )
            return

        if len(rows) == 1:
            ctid, file_name = rows[0]
            cursor.execute(
                """
                UPDATE files
                SET
                    main_title = COALESCE(main_title, %s),
                    message_id = %s
                WHERE ctid = %s
                """,
                (original_title, message_id, ctid),
            )
            log.info("[REPOST-REPO] Updated 1 file | %s", file_name)
        else:
            cursor.execute(
                """
                UPDATE files
                SET
                    main_title = COALESCE(main_title, %s),
                    message_id = %s
                WHERE LOWER(file_name) LIKE %s
                """,
                (original_title, message_id, like_pattern),
            )
            log.info(
                "[REPOST-REPO] Mass update | count=%d | title=%r",
                cursor.rowcount,
                original_title,
            )

# ==================================================
# VIEW INITIALIZER
# ==================================================
def bulk_insert_initial_views(view_data: dict[str, int]) -> None:
    if not view_data:
        return

    with get_db_cursor(commit=True) as (cursor, _):
        hashes = list(view_data.keys())

        cursor.execute(
            """
            SELECT file_id, free_hash, paid_hash
            FROM files
            WHERE free_hash = ANY(%s)
               OR paid_hash = ANY(%s)
            """,
            (hashes, hashes),
        )
        results = cursor.fetchall()

        if not results:
            return

        file_ids = set()
        for file_id, free_hash, paid_hash in results:
            if free_hash in view_data or paid_hash in view_data:
                file_ids.add(file_id)

        cursor.executemany(
            """
            INSERT INTO video_stats (file_id, play_count, last_played)
            VALUES (%s, 0, NOW())
            ON CONFLICT (file_id) DO NOTHING
            """,
            [(fid,) for fid in file_ids],
        )

        cursor.executemany(
            """
            INSERT INTO file_views (hash, views)
            VALUES (%s, %s)
            ON CONFLICT (hash)
            DO UPDATE SET views = EXCLUDED.views
            """,
            list(view_data.items()),
        )


# ==================================================
# READ HELPERS
# ==================================================
def get_existing_view_hashes() -> set[str]:
    with get_dict_cursor() as (cursor, _):
        cursor.execute("SELECT hash FROM file_views")
        return {row["hash"] for row in cursor.fetchall()}


def get_free_hashes_by_main_title(main_title: str) -> list[str]:
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT free_hash
            FROM files
            WHERE LOWER(TRIM(main_title)) = LOWER(TRIM(%s))
              AND free_hash IS NOT NULL
            """,
            (main_title,),
        )
        return [row["free_hash"] for row in cursor.fetchall()]


def update_main_title(
    *,
    title: str,
    message_id: int,
) -> None:
    update_main_title_and_message_id_safe(
        title=title,
        message_id=message_id,
    )


def insert_initial_views_for_title(
    *,
    title: str,
    views: int,
) -> None:
    if views <= 0:
        return

    hashes = get_free_hashes_by_main_title(title)
    if not hashes:
        return

    existing = get_existing_view_hashes()
    new_hashes = [h for h in hashes if h not in existing]
    if not new_hashes:
        return

    per_hash = max(1, views // len(new_hashes))
    view_data = {h: per_hash for h in new_hashes}

    bulk_insert_initial_views(view_data)
