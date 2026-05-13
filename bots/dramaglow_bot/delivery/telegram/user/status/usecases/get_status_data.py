from datetime import datetime, timezone

from configs.logging_setup import log
from db.vip_users.vip_service import get_active_vip

from .parse_date import parse_dt
from ......repository.user_status_repository import (
    fetch_today_access,
    fetch_vip_purchases,
)


def is_vip_active(vip_expired: datetime | None, now: datetime) -> bool:
    return vip_expired is not None and vip_expired > now


def get_status_data(user_id: int, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)

    vip_data = get_active_vip(user_id) or {}
    vip_start = parse_dt(vip_data.get("start_date"))
    vip_expired = parse_dt(vip_data.get("end_date"))

    access_today = 0
    last_access = None
    purchases = 0

    try:
        access_today, last_access_raw = fetch_today_access(user_id)
        last_access = parse_dt(last_access_raw)
        purchases = fetch_vip_purchases(user_id)

    except Exception as e:
        log.warning(
            "[STATUS] gagal ambil status user_id=%s: %s",
            user_id,
            e,
            exc_info=True,
        )

    return {
        "vip_start": vip_start,
        "vip_expired": vip_expired,
        "is_vip": is_vip_active(vip_expired, now),
        "access_today": access_today,
        "last_access": last_access,
        "purchases": purchases,
    }
