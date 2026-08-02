from configs.logging_setup import log
from database.connection import get_db_cursor

# ========================= #
# === DONASI & STATISTIK === #
# ========================= #


def save_token_for_user(user_id: int, token: str, metode: str) -> None:
    """
    Simpan token donasi user. Jika sudah ada, update token berdasarkan user_id dan metode.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO donasi_token (user_id, token, metode)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, metode) DO UPDATE SET token = EXCLUDED.token
                """,
                (user_id, token, metode),
            )
            conn.commit()
            log.info(
                "Token donasi disimpan untuk user_id=%s, metode=%s", user_id, metode
            )
    except Exception as e:
        log.error("Gagal simpan token user_id=%s: %s", user_id, e, exc_info=True)


def update_donation_status(token: str, status: str) -> bool:
    """
    Update status donasi berdasarkan token.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                "UPDATE pending_donations SET status = %s WHERE token = %s",
                (status, token),
            )
            conn.commit()
            log.info("Status donasi diperbarui: token=%s, status=%s", token, status)
            return True
    except Exception as e:
        log.error("Gagal update status donasi token=%s: %s", token, e, exc_info=True)
        return False


def get_donation_by_token(token: str):
    """
    Ambil data donasi berdasarkan token.
    """
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT user_id, method, status, created_at
                FROM pending_donations
                WHERE token = %s
                """,
                (token,),
            )
            data = cursor.fetchone()
            log.debug("Data donasi ditemukan: %s", data)
            return data
    except Exception as e:
        log.error("Gagal ambil data donasi token=%s: %s", token, e, exc_info=True)
        return None


def get_donation_daily_stats(days: int = 7, source_bot: str = "drac1n"):
    """
    Ambil statistik donasi harian selama X hari untuk bot tertentu.
    """
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT DATE(timestamp) AS date, SUM(amount)
                FROM donation_log
                WHERE timestamp >= CURRENT_DATE - INTERVAL %s
                  AND source_bot = %s
                  AND type = 'vip'
                GROUP BY date
                ORDER BY date ASC
                """,
                (f"{days} days", source_bot),
            )
            result = cursor.fetchall()
            log.debug("Statistik harian donasi berhasil diambil: %d hari", days)
            return result
    except Exception as e:
        log.error("Gagal ambil statistik donasi harian: %s", e, exc_info=True)
        return []
