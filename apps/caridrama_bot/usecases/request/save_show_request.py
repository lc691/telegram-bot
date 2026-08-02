from configs.logging_setup import log
from database.connection import get_db_cursor

from ...domain.request_repository import insert_show_request


def save_show_request(
    *,
    user_id: int,
    show_id: int,
    username: str | None = None,
    fullname: str | None = None,
) -> bool:
    """
    Usecase untuk menyimpan request drama.

    Return:
        True  -> request berhasil disimpan
        False -> request sudah pernah ada / gagal
    """

    log.info(
        "[SAVE-REQUEST] START user=%s show=%s",
        user_id,
        show_id,
    )

    try:
        with get_db_cursor() as (cursor, _):
            saved = insert_show_request(
                cursor,
                user_id=user_id,
                show_id=show_id,
                username=username,
                fullname=fullname,
            )

        log.info(
            "[SAVE-REQUEST] DONE user=%s show=%s saved=%s",
            user_id,
            show_id,
            saved,
        )
        return saved

    except Exception:
        log.exception(
            "[SAVE-REQUEST] FAILED user=%s show=%s",
            user_id,
            show_id,
        )
        return False


def save_show_request_for_unknown(
    *,
    user_id: int,
    image_path: str,
) -> bool:
    """
    Simpan request ketika show/file belum ada di DB.
    """

    log.info(
        "[SAVE-REQUEST][UNKNOWN] START user=%s image=%s",
        user_id,
        image_path,
    )

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute(
                """
                INSERT INTO pending_show_requests (user_id, image_path)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, image_path),
            )

        log.info(
            "[SAVE-REQUEST][UNKNOWN] DONE user=%s image=%s",
            user_id,
            image_path,
        )
        return True

    except Exception:
        log.exception(
            "[SAVE-REQUEST][UNKNOWN] FAILED user=%s image=%s",
            user_id,
            image_path,
        )
        return False
