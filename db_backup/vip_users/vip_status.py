from datetime import datetime, timezone

import pytz

from common.bot_utils import get_table_name
from configs.logging_setup import log
from db.connect import get_db_cursor
from db.vip_users.status_legacy import check_vip_status as legacy_check_vip_status


def check_vip_status(user_id: int, source_bot: str = "drac1n") -> dict:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT end_date FROM vip_users
                WHERE user_id = %s AND source_bot = %s AND status = 'active'
                ORDER BY end_date DESC
                LIMIT 1
                """,
                (user_id, source_bot),
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return _check_vip_from_legacy_table(user_id, source_bot)
            return _build_vip_status_result(user_id, row[0], source_bot)
    except Exception as e:
        log.error(
            f"[CHECK VIP] ❌ Error saat cek VIP user_id={user_id} bot={source_bot}: {e}",
            exc_info=True,
        )
        return _vip_result_false()


def _check_vip_from_legacy_table(user_id: int, source_bot: str) -> dict:
    table_name = get_table_name(source_bot)
    if not table_name:
        log.error(f"[CHECK VIP] ❌ Bot tidak valid: {source_bot}")
        return _vip_result_false()

    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                f"SELECT vip_expired FROM {table_name} WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row or not row[0]:
                return _vip_result_false()
            return _build_vip_status_result(user_id, row[0], source_bot)
    except Exception as e:
        log.error(
            f"[CHECK VIP] ❌ Fallback gagal user_id={user_id} bot={source_bot}: {e}",
            exc_info=True,
        )
        return _vip_result_false()


def _build_vip_status_result(user_id: int, vip_expired, source_bot: str) -> dict:
    if isinstance(vip_expired, str):
        vip_expired = datetime.fromisoformat(vip_expired)
    if vip_expired.tzinfo is None:
        vip_expired = vip_expired.replace(tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)
    end_of_day = vip_expired.replace(hour=23, minute=59, second=59, microsecond=999999)
    is_vip = end_of_day > now_utc
    expired_local = end_of_day.astimezone(pytz.timezone("Asia/Jakarta"))

    log.debug(
        f"[CHECK VIP] user_id={user_id} | expired={vip_expired} | bot={source_bot}"
    )

    return {
        "is_vip": is_vip,
        "expired_at": expired_local.strftime("%Y-%m-%d %H:%M:%S"),
        "expired_utc": end_of_day.strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_vip_status(user_id: int, source_bot: str = "drac1n"):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT paket, start_date, end_date, status
            FROM vip_users
            WHERE user_id = %s
              AND source_bot = %s
            ORDER BY end_date DESC
            LIMIT 1
            """,
            (user_id, source_bot),
        )
        row = cursor.fetchone()
        if row:
            paket, start_date, end_date, status = row
            expired_str = end_date.strftime("%d %b %Y") if end_date else "-"
            return {
                "is_vip": status == "active" and end_date > datetime.now(timezone.utc),
                "paket": paket,
                "start_date": start_date,
                "end_date": end_date,
                "expired_str": expired_str,
                "status": status,
            }

    # 🔁 Fallback ke legacy table
    legacy = legacy_check_vip_status(user_id, source_bot=source_bot)
    legacy_expired = legacy.get("expired_utc")
    legacy_expired_str = legacy_expired.strftime("%d %b %Y") if legacy_expired else "-"
    return {
        "is_vip": legacy["is_vip"],
        "paket": "legacy",
        "start_date": None,
        "end_date": legacy_expired,
        "expired_str": legacy_expired_str,
        "status": "legacy" if legacy["is_vip"] else "none",
    }


def get_all_active_vip_users(limit=5, offset=0, source_bot="drac1n"):
    with get_db_cursor() as (cursor, _):
        cursor.execute(
            """
            SELECT user_id, username, start_date, end_date, paket
            FROM vip_users
            WHERE status = 'active'
              AND end_date > %s
              AND source_bot = %s
            ORDER BY end_date ASC
            LIMIT %s OFFSET %s
            """,
            (datetime.now(timezone.utc), source_bot, limit, offset),
        )
        rows = cursor.fetchall()
        return [
            {
                "user_id": row[0],
                "username": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "paket": row[4],
            }
            for row in rows
        ]


def _vip_result_false():
    return {"is_vip": False, "expired_at": None, "expired_utc": None}
