from configs.logging_setup import log
from db.connect import get_db_cursor

# ===================== #
# === CHANNEL FUNGSI === #
# ===================== #


def add_user(user_id: int) -> None:
    """
    Menambahkan user ke tabel `adding_channel_users`.
    Jika user sudah ada, abaikan (ON CONFLICT DO NOTHING).
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                "INSERT INTO adding_channel_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
                (user_id,),
            )
            conn.commit()
            log.info("User ditambahkan ke adding_channel_users: user_id=%s", user_id)
    except Exception as e:
        log.error("Gagal menambahkan user user_id=%s: %s", user_id, e, exc_info=True)


def discard_user(user_id: int) -> None:
    """
    Menghapus user dari tabel `adding_channel_users`.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                "DELETE FROM adding_channel_users WHERE user_id = %s",
                (user_id,),
            )
            conn.commit()
            log.info("User dihapus dari adding_channel_users: user_id=%s", user_id)
    except Exception as e:
        log.error("Gagal menghapus user user_id=%s: %s", user_id, e, exc_info=True)


def is_user_adding(user_id: int) -> bool:
    """
    Mengecek apakah user sedang dalam proses 'adding'.
    """
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT 1 FROM adding_channel_users WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone() is not None
            log.debug("Cek status user_id=%s: %s", user_id, result)
            return result
    except Exception as e:
        log.error("Gagal cek status user_id=%s: %s", user_id, e, exc_info=True)
        return False
