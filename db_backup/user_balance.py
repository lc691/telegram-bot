from datetime import datetime, timezone

from psycopg2 import errors

from configs.logging_setup import log
from db.connect import get_dict_cursor  # asumsi ada helper untuk cursor dict


def add_user_balance(
    user_id: int, amount: int, reason: str = "Top-up via redeem", admin_id: int = 0
):
    """
    Tambah saldo user dengan log.
    - user_id: ID user
    - amount: jumlah saldo (positif)
    - reason: alasan penambahan saldo
    - admin_id: opsional, siapa yang menambahkan saldo
    """
    if amount <= 0:
        log.warning(
            f"[BALANCE] Gagal add saldo: amount harus positif, user_id={user_id}"
        )
        return False

    now = datetime.now(timezone.utc)

    try:
        with get_dict_cursor() as (cur, conn):
            # Update saldo
            cur.execute(
                """
                UPDATE users
                SET balance = COALESCE(balance, 0) + %s,
                    updated_at = NOW()
                WHERE user_id = %s
                RETURNING balance
                """,
                (amount, user_id),
            )
            row = cur.fetchone()
            if not row:
                log.warning(f"[BALANCE] User tidak ditemukan: user_id={user_id}")
                return False

            new_balance = row["balance"]

            # Catat log
            cur.execute(
                """
                INSERT INTO balance_logs (user_id, admin_id, amount, reason, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, admin_id, amount, reason, now),
            )

            conn.commit()
            log.info(
                f"[BALANCE] Saldo user_id={user_id} bertambah {amount}, total={new_balance}"
            )
            return True

    except errors.UniqueViolation:
        log.warning(f"[BALANCE] Duplicate entry log? user_id={user_id}")
        return False

    except Exception as e:
        log.error(f"[BALANCE] Gagal add saldo user_id={user_id}: {e}", exc_info=True)
        return False
