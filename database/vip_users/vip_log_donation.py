# ========== DONATION REGULAR ==========
from configs.logging_setup import log
from database.connection import get_db_cursor


def insert_donation_log(
    email: str,
    amount: int,
    message: str,
    user_id: int = None,
    paket: str = None,
    tipe: str = "vip",
    source_bot: str = "drac1n",
) -> int | None:
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO donation_log (email, amount, message, user_id, paket, type, source_bot)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (email, amount, message, user_id, paket, tipe, source_bot),
            )
            donation_id = cursor.fetchone()[0]
            conn.commit()
            log.info(
                f"[DONASI] Log disimpan (id={donation_id}): email={email}, bot={source_bot}, tipe={tipe}"
            )
            return donation_id
    except Exception as e:
        log.error(f"[DONASI] ❌ Gagal insert log donasi: {e}", exc_info=True)
        return None
