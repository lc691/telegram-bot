from pyrogram.enums import ParseMode

from configs.logging_setup import log

from .referral_abuse import check_and_flag_referral_abuse
from .referral_assignment import assign_referral_once
from .referral_limits import (
    increment_referral_rate,
    is_referral_rate_limited,
)
from .referral_logs import log_referral_event
from .referral_validation import validate_referral_code


# ============================================================
# FINAL REFERRAL HANDLER
# - SINGLE SOURCE OF TRUTH
# - IMMUTABLE (ONE TIME ONLY)
# ============================================================
async def handle_referral_assignment(
    *,
    new_user_id: int,
    referral_code: str,
    message=None,
) -> bool:
    """
    Referral rules (INVARIANTS):
    1. Referral hanya boleh dilakukan SATU KALI.
    2. Referral tidak boleh diubah / di-override.
    3. Referral hanya berlaku untuk user baru (time window).
    4. Referral wajib lolos anti-abuse & rate limit.
    5. Semua assignment melalui fungsi ini.
    """

    try:
        # --------------------------------------------------
        # 1️⃣ Validate referral code & resolve referrer
        # --------------------------------------------------
        referrer_user_id = validate_referral_code(
            new_user_id=new_user_id,
            referral_code=referral_code,
        )

        if not referrer_user_id:
            log_referral_event(
                referrer_user_id=None,
                new_user_id=new_user_id,
                event_type="invalid_code",
            )

            if message:
                await message.reply_text(
                    "❗ Kode referral tidak valid atau sudah tidak aktif.",
                    parse_mode=ParseMode.HTML,
                )
            return False

        # --------------------------------------------------
        # 2️⃣ Anti-abuse (HARD BLOCK)
        # --------------------------------------------------
        if check_and_flag_referral_abuse(new_user_id, referrer_user_id):
            log.warning(
                "[REFERRAL] Abuse blocked new_user=%s referrer=%s",
                new_user_id,
                referrer_user_id,
            )

            log_referral_event(
                referrer_user_id=referrer_user_id,
                new_user_id=new_user_id,
                event_type="abuse_blocked",
            )

            if message:
                await message.reply_text(
                    "⚠️ Aktivitas referral terdeteksi mencurigakan.",
                    parse_mode=ParseMode.HTML,
                )
            return False

        # --------------------------------------------------
        # 3️⃣ Rate limit (per-referrer)
        # --------------------------------------------------
        if is_referral_rate_limited(referrer_user_id):
            log.warning(
                "[REFERRAL] Rate limited referrer=%s",
                referrer_user_id,
            )

            log_referral_event(
                referrer_user_id=referrer_user_id,
                new_user_id=new_user_id,
                event_type="rate_limited",
            )

            if message:
                await message.reply_text(
                    "⚠️ Referral sedang dibatasi. Silakan coba lagi nanti.",
                    parse_mode=ParseMode.HTML,
                )
            return False

        # --------------------------------------------------
        # 4️⃣ Assign referral (DB-LOCKED, ONE TIME)
        # --------------------------------------------------
        assigned = assign_referral_once(
            new_user_id=new_user_id,
            referrer_user_id=referrer_user_id,
        )

        if not assigned:
            log_referral_event(
                referrer_user_id=referrer_user_id,
                new_user_id=new_user_id,
                event_type="already_assigned",
            )

            if message:
                await message.reply_text(
                    "ℹ️ Referral sudah pernah ditetapkan sebelumnya.",
                    parse_mode=ParseMode.HTML,
                )
            return False

        # --------------------------------------------------
        # 5️⃣ Metrics & logs (AFTER SUCCESS)
        # --------------------------------------------------
        increment_referral_rate(referrer_user_id)

        log_referral_event(
            referrer_user_id=referrer_user_id,
            new_user_id=new_user_id,
            event_type="assigned",
        )

        # --------------------------------------------------
        # 6️⃣ User notification
        # --------------------------------------------------
        if message:
            await message.reply_text(
                (
                    "🎉 <b>Referral berhasil!</b>\n"
                    "Terima kasih telah bergabung melalui link referral."
                ),
                parse_mode=ParseMode.HTML,
            )

        return True

    except Exception:
        log.exception(
            "[REFERRAL] Fatal error new_user=%s referral_code=%s",
            new_user_id,
            referral_code,
        )
        return False
