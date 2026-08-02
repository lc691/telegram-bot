from configs.logging_setup import log
from database.connection import get_db_cursor

# ========================= #
# === FORWARD MESSAGE    === #
# ========================= #


def save_forward_message(
    original_chat_id: int,
    original_message_id: int,
    forward_from_user_id: int,
    forward_date,
    forward_text: str,
    media_file_id: str = None,
) -> bool:
    """
    Menyimpan pesan yang diforward ke dalam database.
    Menghindari duplikat berdasarkan (original_chat_id, original_message_id).

    Returns:
        bool: True jika penyimpanan berhasil, False jika gagal atau duplikat.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO forward_messages (
                    original_chat_id,
                    original_message_id,
                    forward_from_user_id,
                    forward_date,
                    forward_text,
                    media_file_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (original_chat_id, original_message_id) DO NOTHING
                """,
                (
                    original_chat_id,
                    original_message_id,
                    forward_from_user_id,
                    forward_date,
                    forward_text,
                    media_file_id,
                ),
            )
            conn.commit()

            if cursor.rowcount > 0:
                log.info(
                    "Forward message disimpan: chat_id=%s, msg_id=%s",
                    original_chat_id,
                    original_message_id,
                )
                return True
            else:
                log.debug(
                    "Forward message duplikat (tidak disimpan ulang): chat_id=%s, msg_id=%s",
                    original_chat_id,
                    original_message_id,
                )
                return False
    except Exception as e:
        log.error(
            "Gagal simpan forward message chat_id=%s, msg_id=%s: %s",
            original_chat_id,
            original_message_id,
            e,
            exc_info=True,
        )
        return False
