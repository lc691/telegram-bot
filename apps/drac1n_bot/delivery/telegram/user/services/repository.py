# services/users/repository.py
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config import DAILY_FREE_LIMIT
from configs.logging_setup import log
from database.connection import get_db_cursor, get_dict_cursor


def user_exists(user_id: int) -> bool:
    with get_db_cursor() as (cur, _):
        cur.execute("SELECT 1 FROM users WHERE user_id=%s LIMIT 1", (user_id,))
        return cur.fetchone() is not None


def get_user(user_id: int):
    with get_dict_cursor() as (cur, _):
        cur.execute(
            """
            SELECT is_vip, vip_expired, free_access_count, last_free_access
            FROM users WHERE user_id=%s
            """,
            (user_id,),
        )
        return cur.fetchone()


def insert_default_user(user_id: int, free_limit: int, now):
    with get_db_cursor(commit=True) as (cur, _):
        cur.execute(
            """
            INSERT INTO users (user_id, is_vip, free_access_count, last_free_access)
            VALUES (%s, false, %s, %s)
            """,
            (user_id, free_limit, now),
        )


def update_quota(user_id: int, quota: int, now):
    with get_db_cursor(commit=True) as (cur, _):
        cur.execute(
            """
            UPDATE users
            SET free_access_count=%s, last_free_access=%s
            WHERE user_id=%s
            """,
            (quota, now, user_id),
        )


def atomic_consume_free_quota(user_id: int):
    """
    Atomic consume free quota (PostgreSQL).

    Behavior:
    - free_access_count > 0  → decrement & return remaining
    - free_access_count <= 0 → return None

    Guarantee:
    - Atomic
    - Race-condition safe
    - No negative quota
    - Minimal IO
    """

    with get_dict_cursor(commit=True) as (cur, _):
        cur.execute(
            """
            UPDATE users
            SET
                free_access_count = free_access_count - 1,
                last_free_access = NOW()
            WHERE user_id = %s
              AND free_access_count > 0
              AND is_active = TRUE
            RETURNING free_access_count
            """,
            (user_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return row["free_access_count"]


def reset_vip_status(user_id: int, quota: int, now):
    with get_db_cursor(commit=True) as (cur, _):
        cur.execute(
            """
            UPDATE users
            SET is_vip = false,
                vip_expired = NULL,
                free_access_count = %s,
                last_free_access = %s
            WHERE user_id = %s
            """,
            (quota, now, user_id),
        )


def update_vip_reminder(user_id: int, reminded: bool = True):
    with get_db_cursor(commit=True) as (cur, _):
        cur.execute(
            "UPDATE users SET vip_reminded=%s WHERE user_id=%s", (reminded, user_id)
        )

def add_user_if_not_exists(
    user_id: int,
    first_name: Optional[str] = None,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insert user baru jika belum ada.

    Rules:
    - free_access_count selalu = DAILY_FREE_LIMIT
    - Tidak boleh override quota dari luar
    - Aman dipanggil berkali-kali (idempotent)
    """

    first_name = first_name.strip() if first_name else None
    username = username.strip() if username else None
    now = datetime.now(timezone.utc)

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute(
                """
                INSERT INTO users (
                    user_id,
                    first_name,
                    username,
                    free_access_count,
                    last_free_access,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (
                    user_id,
                    first_name,
                    username,
                    DAILY_FREE_LIMIT,
                    now,
                    now,
                    now,
                ),
            )

        return {
            "created": cursor.rowcount > 0,
            "user_id": user_id,
        }

    except Exception as e:
        log.warning(
            "[DB] add_user_if_not_exists failed user_id=%s | %s",
            user_id,
            e,
            exc_info=True,
        )
        return {
            "created": False,
            "user_id": user_id,
        }
