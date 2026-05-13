from configs.logging_setup import log
from db.connect import get_dict_cursor


def get_active_post_channel() -> int:
    """
    Ambil chat_id channel yang aktif untuk posting.
    Hanya 1 channel aktif yang diambil (is_active = TRUE)
    """
    with get_dict_cursor() as (cur, _):
        cur.execute(
            "SELECT nilai, alias FROM channel_admin WHERE is_active = TRUE LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            log.info(f"[DB] Menggunakan channel aktif alias '{row['alias']}'")
            return row["nilai"]
        else:
            raise ValueError("Tidak ada channel aktif untuk posting. Silakan set di DB.")
