from datetime import datetime, timezone

from pyrogram import Client
from pyrogram.enums import ParseMode

from configs.logging_setup import log
from configs.trace import set_trace_id, reset_trace_id
from db.affiliate_db import ensure_user_has_affiliate_code

from ...refferral.handlers.register import referral_menu_entrypoint
from ..check_join.channel_verification import check_channel_join
from ......services.referral.referral_handler import handle_referral_assignment
from ...services.reminder import remind_vip_if_needed
from ...services.repository import add_user_if_not_exists

from ...file.usecases.access_file_flow import access_file_flow
from ...vip.usecases.show_entry import show_vip_entry
from ...status.handlers.status_entry_handler import handle_status_entry

from .start_ui import show_main_menu


# ============================================================
# PARSE /start ARGUMENTS
# ============================================================
def parse_start_args(text: str):
    """
    Return:
        access_hash: str
        quick_route: str | None
        referral_code: str | None
    """
    try:
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "", None, None

        arg = parts[1].strip().lower()

        if arg in {
            "vip",
            "vip_status",
            "search",
            "referral",
            "referral_menu",
            "affiliate",
        }:
            return "", arg, None

        if arg.startswith("ref_"):
            return "", None, arg.replace("ref_", "", 1)

        return arg, None, None

    except Exception:
        log.exception("[START] parse args failed")
        return "", None, None


# ============================================================
# QUICK ROUTE DISPATCHER (NO SIDE EFFECT)
# ============================================================
async def dispatch_quick_route(*, route, client, message, user, admin_cache):
    if route == "vip":
        return await show_vip_entry(
            event=message,
            display_name=user.username or user.first_name,
        )

    if route == "vip_status":
        return await handle_status_entry(
            client,
            message,
            admin_cache,
        )

    if route in {"referral", "referral_menu", "affiliate"}:
        return await referral_menu_entrypoint(client, message)


# ============================================================
# FINAL START HANDLER
# ============================================================
async def handle_start_command(
    client: Client,
    message,
    admin_cache,
):
    # ==================================================
    # 0️⃣ USER VALIDATION
    # ==================================================
    user = message.from_user
    if not user:
        return await message.reply_text(
            "❗ Tidak dapat mengenali pengguna.",
            parse_mode=ParseMode.HTML,
        )

    user_id = user.id

    # ==================================================
    # ✅ TRACE SETUP (ENTRYPOINT)
    # ==================================================
    now_utc = datetime.now(timezone.utc)

    trace_id = (
        f"S-{user_id}-"
        f"{now_utc.strftime('%Y%m%d%H%M%S')}"
        f"{int(now_utc.microsecond / 1000):03d}"
    )

    token = set_trace_id(trace_id)

    username = user.username or ""
    first_name = user.first_name or ""
    display_name = username or first_name or "Teman"
    is_admin = admin_cache.is_admin(user_id)
    now = datetime.now(timezone.utc)

    try:
        log.info(
            "[START] user=%s admin=%s has_args=%s",
            user_id,
            is_admin,
            bool(message.text and " " in message.text),
        )

        # ==================================================
        # 1️⃣ PARSE /start ARGUMENTS
        # ==================================================
        access_hash, quick_route, referral_code = parse_start_args(message.text)

        # ==================================================
        # 2️⃣ REGISTER USER (REQUIRED FOR REFERRAL)
        # ==================================================
        try:
            add_user_if_not_exists(user_id, first_name, username)
            ensure_user_has_affiliate_code(user_id)
        except Exception:
            log.exception("[START] register user failed")

        # ==================================================
        # 3️⃣ REFERRAL ASSIGNMENT (IMMUTABLE, ONCE)
        #    - admin di-skip
        #    - dilakukan sebelum quick route
        # ==================================================
        if referral_code and not is_admin:
            try:
                await handle_referral_assignment(
                    new_user_id=user_id,
                    referral_code=referral_code,
                    message=message,
                )
            except Exception:
                log.exception("[START] referral assignment failed")

        # ==================================================
        # 4️⃣ CHANNEL JOIN CHECK (NON-ADMIN)
        # ==================================================
        if not is_admin:
            try:
                joined = await check_channel_join(
                    client,
                    user_id,
                    access_hash,
                    message,
                )
                if not joined:
                    return
            except Exception:
                log.exception(
                    "[START] channel check error bot=%s user=%s",
                    getattr(client.me, "username", None),
                    user_id,
                )

        # ==================================================
        # 5️⃣ QUICK ROUTE (NO SIDE EFFECT)
        # ==================================================
        if quick_route:
            log.info(
                "[START] quick_route=%s user=%s",
                quick_route,
                user_id,
            )
            return await dispatch_quick_route(
                route=quick_route,
                client=client,
                message=message,
                user=user,
                admin_cache=admin_cache,
            )

        # ==================================================
        # 6️⃣ VIP REMINDER
        # ==================================================
        try:
            await remind_vip_if_needed(user_id, now, message)
        except Exception:
            log.exception("[START] vip reminder failed")

        # ==================================================
        # 7️⃣ NO HASH → MAIN MENU
        # ==================================================
        if not access_hash:
            return await show_main_menu(
                event=message,
                display_name=display_name,
            )

        # ==================================================
        # 8️⃣ FILE ACCESS FLOW
        # ==================================================
        await access_file_flow(
            client=client,
            message=message,
            user_id=user_id,
            access_hash=access_hash,
            is_admin=is_admin,
            edit=False,  # reply
        )

    finally:
        reset_trace_id(token)
