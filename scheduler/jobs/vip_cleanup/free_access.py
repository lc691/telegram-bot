from config import DAILY_FREE_LIMIT
from configs.logging_setup import log
from database.connection import get_dict_cursor


def reset_non_vip_free_access() -> int:
    """
    Reset kuota free access harian untuk SEMUA user non-VIP.

    Rules:
    - Gunakan DAILY_FREE_LIMIT sebagai single source of truth
    - Timestamp diambil dari database (NOW()) agar konsisten
    - Aman dijalankan via cron / manual
    """

    with get_dict_cursor() as (cursor, conn):
        cursor.execute(
            """
            UPDATE users
            SET
                free_access_count = %s,
                last_free_access = NOW()
            WHERE is_vip = FALSE
              AND is_active = TRUE
            """,
            (DAILY_FREE_LIMIT,),
        )
        affected = cursor.rowcount
        conn.commit()

    log.info(
        "[FREE ACCESS] Daily reset non-VIP quota → %s | affected=%s",
        DAILY_FREE_LIMIT,
        affected,
    )
    return affected
