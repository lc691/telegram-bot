from datetime import timedelta

from shared.utils.parse_date import _now_utc
from configs.logging_setup import log
from database.connection import get_db_cursor

# Referral hanya valid untuk user baru (dalam menit)
NEW_USER_WINDOW_MINUTES = 10


def assign_referral_once(
    *,
    new_user_id: int,
    referrer_user_id: int,
) -> bool:
    """
    FINAL referral assignment (IMMUTABLE).

    Rules (HARD GUARANTEE):
    1. Referral hanya boleh SATU KALI.
    2. Referral tidak boleh diubah.
    3. Referral hanya untuk user BARU (time window).
    4. Race-condition SAFE (row-level lock).
    5. DB adalah single source of truth.
    """

    try:
        with get_db_cursor(commit=True) as (cursor, _):

            # --------------------------------------------------
            # 1️⃣ Lock target user row
            # --------------------------------------------------
            cursor.execute(
                """
                SELECT
                    referrer_user_id,
                    created_at
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (new_user_id,),
            )

            row = cursor.fetchone()
            if not row:
                log.warning(
                    "[REFERRAL] assign failed: user not found user=%s",
                    new_user_id,
                )
                return False

            current_referrer, created_at = row

            # --------------------------------------------------
            # 2️⃣ Immutable guard (already assigned)
            # --------------------------------------------------
            if current_referrer is not None:
                return False

            # --------------------------------------------------
            # 3️⃣ New user window guard
            # --------------------------------------------------
            if created_at is None:
                log.warning(
                    "[REFERRAL] assign failed: missing created_at user=%s",
                    new_user_id,
                )
                return False

            if (_now_utc() - created_at) > timedelta(minutes=NEW_USER_WINDOW_MINUTES):
                return False

            # --------------------------------------------------
            # 4️⃣ Atomic assignment (defense in depth)
            # --------------------------------------------------
            cursor.execute(
                """
                UPDATE users
                SET
                    referrer_user_id = %s,
                    referral_assigned_at = now()
                WHERE user_id = %s
                  AND referrer_user_id IS NULL
                """,
                (
                    referrer_user_id,
                    new_user_id,
                ),
            )

            # Jika tidak ada row ter-update → gagal / race kalah
            if cursor.rowcount != 1:
                return False

            return True

    except Exception:
        log.exception(
            "[REFERRAL] assign_referral_once fatal error user=%s referrer=%s",
            new_user_id,
            referrer_user_id,
        )
        return False
