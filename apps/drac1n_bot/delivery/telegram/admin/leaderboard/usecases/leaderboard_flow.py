from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import MessageNotModified

from configs.logging_setup import log

from apps.drac1n_bot.delivery.telegram.admin.leaderboard.presenters.leaderboard_presenter import (
    build_leaderboard_text,
    build_leaderboard_keyboard,
)
from apps.drac1n_bot.delivery.telegram.admin.leaderboard.repository.leaderboard_repository import (
    fetch_vip_leaderboard,
    fetch_vip_total,
)

from apps.drac1n_bot.delivery.telegram.user.common.display_name import get_display_name
from apps.drac1n_bot.delivery.telegram.user.common.konstanta import PAGE_SIZE, MAX_PAGE
from apps.drac1n_bot.delivery.telegram.admin.leaderboard.utils.timezone import today_wib


VALID_PERIODS = {"daily", "weekly", "monthly", "all"}


async def show_leaderboard(
    *,
    client: Client,  # tetap diterima untuk konsistensi handler
    event: Message | CallbackQuery,
    period: str,
    page: int,
    date: str | None = None,
):
    """
    Entry point leaderboard VIP.

    Guarantees:
    - WIB correct
    - minimal I/O
    - predictable logging
    """

    # ===============================
    # STEP 1 — VALIDASI USER
    # ===============================
    user = event.from_user
    if not user:
        return

    username = get_display_name(user)

    # ===============================
    # STEP 2 — VALIDASI & NORMALISASI INPUT
    # ===============================
    if period not in VALID_PERIODS:
        log.warning(
            "[LEADERBOARD] invalid_period user=%s period=%s",
            username,
            period,
        )
        return

    if page < 1:
        page = 1
    elif page > MAX_PAGE:
        page = MAX_PAGE

    if period == "daily" and not date:
        date = today_wib().isoformat()

    offset = (page - 1) * PAGE_SIZE

    log.debug(
        "[LEADERBOARD] request user=%s period=%s date=%s page=%s offset=%s",
        username,
        period,
        date,
        page,
        offset,
    )

    try:
        # ===============================
        # STEP 3 — FETCH DATA
        # ===============================
        data = fetch_vip_leaderboard(
            limit=PAGE_SIZE,
            offset=offset,
            period=period,
            date=date,
        )

        # total hanya dibutuhkan untuk info, bukan paging logic
        total = fetch_vip_total(
            period=period,
            date=date,
        )

        # ===============================
        # STEP 4 — BUILD UI
        # ===============================
        text = build_leaderboard_text(
            data=data,
            period=period,
            page=page,
            total=total,
            date=date,
        )

        keyboard = build_leaderboard_keyboard(
            period=period,
            page=page,
            date=date,
        )

        # ===============================
        # STEP 5 — RENDER RESPONSE
        # ===============================
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
            await event.answer()
        else:
            await event.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )

        # ===============================
        # STEP 6 — SUCCESS LOG
        # ===============================
        log.info(
            "[LEADERBOARD] success user=%s period=%s date=%s page=%s rows=%s total=%s",
            username,
            period,
            date,
            page,
            len(data),
            total,
        )

    except MessageNotModified:
        # Normal & expected case
        if isinstance(event, CallbackQuery):
            await event.answer()

        log.debug(
            "[LEADERBOARD] not_modified user=%s period=%s date=%s page=%s",
            username,
            period,
            date,
            page,
        )

    except Exception:
        log.exception(
            "[LEADERBOARD] failed user=%s period=%s date=%s page=%s",
            username,
            period,
            date,
            page,
        )

        if isinstance(event, CallbackQuery):
            await event.answer(
                "⚠️ Gagal memuat leaderboard",
                show_alert=True,
            )
        else:
            await event.reply_text("⚠️ Gagal memuat leaderboard")
