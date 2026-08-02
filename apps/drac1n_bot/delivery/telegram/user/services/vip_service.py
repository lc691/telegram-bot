# services/users/vip_service.py
from datetime import datetime, timezone

from shared.utils.parse_date import ensure_aware

from database.user.user_repository import (
    get_user,
    insert_default_user,
    update_quota,
)

DAILY_FREE_LIMIT = 2
UNLIMITED = 9999


async def check_access(user_id: int, is_admin: bool):
    now = datetime.now(timezone.utc)

    if is_admin:
        return True, True, UNLIMITED

    user = get_user(user_id)
    if not user:
        insert_default_user(user_id, DAILY_FREE_LIMIT, now)
        return True, False, DAILY_FREE_LIMIT

    is_vip = user["is_vip"]
    vip_expired = user["vip_expired"]
    quota = user["free_access_count"]
    last_access = user["last_free_access"]

    # VIP expired
    if is_vip and vip_expired and ensure_aware(vip_expired) <= now:
        is_vip = False
        quota = DAILY_FREE_LIMIT
        update_quota(user_id, quota, now)

    # Reset harian
    if not is_vip:
        today = now.date()
        if not last_access or ensure_aware(last_access).date() < today:
            quota = DAILY_FREE_LIMIT
            update_quota(user_id, quota, now)

    allowed = is_vip or quota > 0
    return allowed, is_vip, (UNLIMITED if is_vip else quota)


async def consume_free_quota(user_id: int):
    user = get_user(user_id)
    if not user:
        return 0

    quota = user["free_access_count"]
    if quota <= 0:
        return 0

    new_quota = quota - 1
    update_quota(user_id, new_quota, datetime.now(timezone.utc))
    return new_quota
