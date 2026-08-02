# ========== VIP UTILITIES ==========
# File: db/vip_users/vip_utils.py

from datetime import datetime, timedelta

from dateutil import parser

from shared.bot_utils import get_table_name
from configs.logging_setup import log
from database.connection import get_db_cursor


# ===============================
# 🔹 Nonaktifkan VIP Expired (WIB)
# ===============================
def deactivate_expired_vips(
    table: str = "vip_users",
    source_bot: str | None = None,
) -> int:
    """
    Menonaktifkan VIP yang sudah expired.

    Rules:
    - VIP expired jika end_date <= now() (presisi detik)
    - Tidak menggunakan WIB / timezone manual
    - Sinkronisasi ke tabel users ditangani oleh trigger database
    """
    table = table.lower()
    if table != "vip_users":
        log.error("[VIP AUTO OFF] ❌ Tabel tidak dikenali: %s", table)
        return 0

    try:
        with get_db_cursor() as (cursor, conn):
            condition = """
                status = 'active'
                AND end_date IS NOT NULL
                AND end_date <= now()
            """
            params: list = []

            if source_bot:
                condition += " AND source_bot = %s"
                params.append(source_bot)

            cursor.execute(
                f"""
                WITH expired AS (
                    UPDATE {table}
                    SET
                        status = 'expired',
                        updated_at = now()
                    WHERE {condition}
                    RETURNING user_id
                )
                SELECT COUNT(*) FROM expired;
                """,
                tuple(params),
            )

            count = cursor.fetchone()[0]
            conn.commit()

            if count:
                log.info(
                    "[VIP AUTO OFF] ✅ %s VIP expired dinonaktifkan%s",
                    count,
                    f" (bot: {source_bot})" if source_bot else "",
                )
            else:
                log.info(
                    "[VIP AUTO OFF] ℹ️ Tidak ada VIP expired%s",
                    f" (bot: {source_bot})" if source_bot else "",
                )

            return count

    except Exception:
        log.exception(
            "[VIP AUTO OFF] ❌ Gagal menonaktifkan VIP expired%s",
            f" (bot: {source_bot})" if source_bot else "",
        )
        return 0



# ===============================
# 🔹 Sinkronkan Status VIP
# ===============================
def sync_vip_status(table: str = "vip_users") -> int:
    """Sinkronkan status VIP agar semua yang lewat end_date otomatis expired."""
    return deactivate_expired_vips(source_bot=None, table=table)


# ===============================
# 🔹 Parsing Tanggal VIP
# ===============================
def parse_vip_dates(new_expired, total_days):
    """
    Hitung tanggal mulai & akhir VIP dari tanggal expired.
    Mengembalikan tuple (start_str, expired_str) dalam format "dd Mon YYYY HH:MM".
    """
    try:
        if isinstance(new_expired, str):
            expired_dt = parser.parse(new_expired)
        elif isinstance(new_expired, datetime):
            expired_dt = new_expired
        else:
            raise ValueError("Format `new_expired` tidak valid.")

        start_dt = expired_dt - timedelta(days=total_days)

        return (
            start_dt.strftime("%d %b %Y %H:%M"),
            expired_dt.strftime("%d %b %Y %H:%M"),
        )
    except Exception as e:
        log.warning(f"[parse_vip_dates] ⚠️ Gagal parsing tanggal VIP: {e}")
        return "—", "—"


# ===============================
# 🔹 Tandai User Sudah Diingatkan
# ===============================
def mark_vip_notified(user_id: int):
    with get_db_cursor() as (cur, conn):
        cur.execute(
            """
            UPDATE vip_users
            SET vip_reminded = TRUE
            WHERE user_id = %s
            """,
            (user_id,),
        )
        conn.commit()


# ===============================
# 🔹 Reset Status Reminder User
# ===============================
def reset_vip_notified(user_id: int, source_bot: str = "drac1n", cursor=None):
    """Reset flag vip_reminded ke FALSE (biasanya saat aktivasi VIP baru)."""
    table = get_table_name(source_bot)
    if not table:
        log.error(f"[RESET NOTIFIED] ❌ Bot tidak valid: {source_bot}")
        return

    try:
        if cursor is None:
            with get_db_cursor() as (cur, conn):
                cur.execute(
                    f"UPDATE {table} SET vip_reminded = FALSE WHERE user_id = %s",
                    (user_id,),
                )
                conn.commit()
        else:
            cursor.execute(
                f"UPDATE {table} SET vip_reminded = FALSE WHERE user_id = %s",
                (user_id,),
            )
        # log.info(f"[RESET NOTIFIED] ✅ vip_reminded FALSE user_id={user_id}")
    except Exception as e:
        log.error(
            f"[RESET NOTIFIED] ❌ Gagal reset user_id={user_id} ({source_bot}): {e}",
            exc_info=True,
        )


def mark_vip_reminded(user_id: int):
    with get_db_cursor() as (cur, conn):
        cur.execute(
            """
            UPDATE vip_users
            SET vip_reminded = TRUE
            WHERE user_id = %s
              AND vip_reminded = FALSE
            """,
            (user_id,),
        )
        conn.commit()
