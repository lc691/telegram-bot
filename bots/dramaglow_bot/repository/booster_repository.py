import asyncio
import random
import string

from datetime import datetime, timedelta

from configs.booster_config import ALERT_TEMPLATES, FAKE_USERS
from db.connect import get_db_cursor, get_dict_cursor
from db.vip_users.vip_service import get_active_vip_count


def generate_alert_message() -> str:
    template = random.choice(ALERT_TEMPLATES)

    # Ambil semua placeholder dalam template
    fields = [field for _, field, _, _ in string.Formatter().parse(template) if field]

    data = {}
    if "username" in fields:
        data["username"] = random.choice(FAKE_USERS)
    if "count" in fields:
        data["count"] = get_active_vip_count()

    return template.format(**data)


def load_last_vip_time_db() -> float:
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            "SELECT value FROM booster_meta WHERE key = %s", ("last_vip_given",)
        )
        row = cursor.fetchone()
        if row:
            try:
                return float(row["value"])
            except Exception:
                return 0
        return 0


def save_last_vip_time_db(timestamp: float):
    with get_db_cursor(commit=True) as (cursor, _):
        cursor.execute(
            """
            INSERT INTO booster_meta (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """,
            ("last_vip_given", str(timestamp)),
        )


async def is_user_already_boosted(user_id: int, days_limit: int = 30) -> bool:
    since_date = datetime.utcnow() - timedelta(days=days_limit)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _check_user_boosted_sync,
        user_id,
        since_date,
    )


def _check_user_boosted_sync(user_id: int, since_date: datetime) -> bool:
    with get_db_cursor() as (cursor, conn):
        query = """
            SELECT 1 FROM broadcast_logs
            WHERE target_user_id = %s
              AND success = true
              AND sent_at >= %s
            LIMIT 1
        """
        cursor.execute(query, (user_id, since_date))
        return cursor.fetchone() is not None
