from datetime import datetime, timezone
from typing import Optional, Union

from dateutil.parser import parse as parse_dateutil


def parse_dt(value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Normalize datetime input ke UTC-aware datetime.

    - None           → None
    - str            → parsed datetime
    - naive datetime → assumed UTC
    - aware datetime → converted to UTC
    """
    if value is None:
        return None

    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            dt = parse_dateutil(value)
        elif isinstance(value, datetime):
            dt = value
        else:
            return None
    except Exception:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)
