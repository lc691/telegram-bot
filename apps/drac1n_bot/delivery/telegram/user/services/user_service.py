from datetime import datetime, timezone
from typing import Tuple, Optional

from shared.utils.parse_date import ensure_aware
from configs.logging_setup import log
from config import DAILY_FREE_LIMIT, UNLIMITED
from database.user.user_repository import (
    get_user_by_id,
    insert_default_user,
    reset_vip_status,
    update_quota,
    atomic_consume_free_quota,
)


class UserAccessService:
    """
    FINAL USER ACCESS SERVICE

    Prinsip:
    - check_access  → READ + normalize state
    - consume_quota → ATOMIC WRITE (NO RACE)
    """

    # ==================================================
    # CHECK ACCESS (NO SIDE EFFECT)
    # ==================================================
    @staticmethod
    async def check_access(
        user_id: int,
        is_admin: bool = False,
    ) -> Tuple[bool, bool, int]:
        """
        Return:
            allowed: bool
            is_vip: bool
            free_remaining: int
        """
        now = datetime.now(timezone.utc)

        log.debug(
            "[ACCESS] check_access user=%s admin=%s",
            user_id,
            is_admin,
        )

        # --------------------------------------------------
        # 1️⃣ ADMIN SHORTCUT
        # --------------------------------------------------
        if is_admin:
            return True, True, UNLIMITED

        # --------------------------------------------------
        # 2️⃣ LOAD USER
        # --------------------------------------------------
        user = get_user_by_id(user_id)

        # --------------------------------------------------
        # 3️⃣ INIT USER
        # --------------------------------------------------
        if not user:
            insert_default_user(
                user_id,
                DAILY_FREE_LIMIT,
                now,
            )
            log.info("[ACCESS] new user created user=%s", user_id)
            return True, False, DAILY_FREE_LIMIT

        is_vip = user["is_vip"]
        vip_expired = user["vip_expired"]
        quota = user["free_access_count"]
        last_access = user["last_free_access"]

        # --------------------------------------------------
        # 4️⃣ VIP EXPIRATION
        # --------------------------------------------------
        if is_vip and vip_expired and ensure_aware(vip_expired) <= now:
            log.info("[ACCESS] vip expired user=%s", user_id)

            is_vip = False
            quota = DAILY_FREE_LIMIT

            reset_vip_status(
                user_id,
                quota,
                now,
            )

        # --------------------------------------------------
        # 5️⃣ DAILY RESET (NON-VIP)
        # --------------------------------------------------
        if not is_vip:
            today = now.date()

            if not last_access or ensure_aware(last_access).date() < today:
                quota = DAILY_FREE_LIMIT
                update_quota(
                    user_id,
                    quota,
                    now,
                )

        # --------------------------------------------------
        # 6️⃣ FINAL DECISION
        # --------------------------------------------------
        allowed = is_vip or quota > 0
        free_remaining = UNLIMITED if is_vip else quota

        log.debug(
            "[ACCESS] result user=%s allowed=%s vip=%s quota=%s",
            user_id,
            allowed,
            is_vip,
            free_remaining,
        )

        return allowed, is_vip, free_remaining

    # ==================================================
    # ATOMIC CONSUME (THE ONLY PLACE THAT MUTATES QUOTA)
    # ==================================================
    @staticmethod
    async def consume_free_quota_atomic(user_id: int) -> Optional[int]:
        """
        Atomic consume (single source of mutation):
        - quota > 0  → decrement & return remaining
        - quota <= 0 → return None
        """
        return atomic_consume_free_quota(user_id)
