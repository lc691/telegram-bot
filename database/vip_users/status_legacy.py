from datetime import datetime, timezone

import pytz

from shared.bot_utils import get_table_name
from configs.logging_setup import log
from database.connection import get_db_cursor


def check_vip_status(user_id: int, source_bot: str = "drac1n") -> dict:
    table_name = get_table_name(source_bot)
    if not table_name:
        log.error(f"[LEGACY VIP] ❌ Bot tidak valid: {source_bot}")
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
            return _build_vip_status_result(row[0])
    except Exception as e:
        log.error(
            f"[LEGACY VIP] ❌ Error fallback user_id={user_id} bot={source_bot}: {e}",
            exc_info=True,
        )
        return _vip_result_false()


def _build_vip_status_result(vip_expired) -> dict:
    if isinstance(vip_expired, str):
        vip_expired = datetime.fromisoformat(vip_expired)
    if vip_expired.tzinfo is None:
        vip_expired = vip_expired.replace(tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)
    end_of_day = vip_expired.replace(hour=23, minute=59, second=59, microsecond=999999)
    is_vip = end_of_day > now_utc
    expired_local = end_of_day.astimezone(pytz.timezone("Asia/Jakarta"))

    return {
        "is_vip": is_vip,
        "expired_at": expired_local.strftime("%Y-%m-%d %H:%M:%S"),
        "expired_utc": end_of_day.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _vip_result_false():
    return {"is_vip": False, "expired_at": None, "expired_utc": None}
