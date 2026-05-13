import asyncio

from datetime import datetime, timezone
from typing import Optional

from common.webhook.bot.notifier import notify_user_reminder
from common.webhook.core.config import CHECK_INTERVAL_SECONDS
from configs.logging_setup import log
from db.vip_users.vip_deactivate import get_expiring_vips
from db.vip_users.vip_status import check_vip_status
from db.vip_users.vip_utils import mark_vip_notified, reset_vip_notified

BOTS = ("drac1n", "utbk")
BATCH_LIMIT = 50
DAYS_AHEAD = 2
EXPIRING_SECONDS = 86400  # 1 hari


async def reminder_loop(client):
    while True:
        try:
            for bot in BOTS:
                await _process_bot_reminders(client, bot)
        except Exception as e:
            log.exception(f"[REMINDER] 💥 Global loop error: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _process_bot_reminders(client, bot: str):
    offset = 0
    now = datetime.now(timezone.utc)

    while True:
        batch = get_expiring_vips(
            bot=bot,
            days_ahead=DAYS_AHEAD,
            offset=offset,
            limit=BATCH_LIMIT,
        )
        if not batch:
            return

        for user_id, _, vip_reminded in batch:
            try:
                await _process_user(
                    client=client,
                    bot=bot,
                    user_id=user_id,
                    vip_reminded=vip_reminded,
                    now=now,
                )
            except Exception as e:
                log.exception(f"[REMINDER] ❌ user_id={user_id}: {e}")

        offset += BATCH_LIMIT


async def _process_user(
    *,
    client,
    bot: str,
    user_id: int,
    vip_reminded: bool,
    now: datetime,
):
    status = check_vip_status(user_id, source_bot=bot)
    expired_at = _safe_parse_datetime(status.get("expired_at"))

    if not expired_at:
        log.warning(f"[REMINDER] ❗ invalid expired_at: user_id={user_id}")
        return

    remaining_seconds = (expired_at - now).total_seconds()
    is_expiring = remaining_seconds < EXPIRING_SECONDS

    if is_expiring and not vip_reminded:
        await notify_user_reminder(
            client=client,
            user_id=user_id,
            paket=status.get("paket", "-"),
            is_extend=status.get("is_extend", False),
            expired=expired_at,
            total=status.get("total", 0),
            remaining_days=status.get("remaining_days", 0),
        )
        mark_vip_notified(user_id, source_bot=bot)
        return

    if not is_expiring and vip_reminded:
        reset_vip_notified(user_id, source_bot=bot)


def _safe_parse_datetime(value) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(value) if isinstance(value, str) else value
        return dt.replace(tzinfo=timezone.utc) if dt and dt.tzinfo is None else dt
    except Exception:
        return None
