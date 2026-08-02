from typing import Optional

from configs.logging_setup import log
from database.affiliate_db import get_user_by_referral_code


def validate_referral_code(new_user_id: int, code: str) -> Optional[int]:
    if not code:
        return None

    ref = get_user_by_referral_code(code)
    if not ref or not ref.get("is_active", True):
        return None

    if ref["user_id"] == new_user_id:
        log.warning("[REFERRAL] Self referral blocked")
        return None

    return ref["user_id"]
