import asyncio
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from pyrogram.errors import FloodWait, RPCError

from configs.logging_setup import log

from ..services.click_lock import is_click_locked
from ...common.display_name import get_display_name

from ..ui.keyboards import upsell_keyboard
from ..usecases.show_entry import show_vip_entry
from ..usecases.vip_ui import send_vip_menu
from ..usecases.payment import show_vip_payment_menu
from ..upsell.upsell import build_upsell

from common.utils_new.menu_utils import edit_menu
from common.utils.ui_session_upssell import (
    get_upsell_context,
    set_upsell_context,
)


def register_vip_callbacks(app: Client):

    # =====================================================
    # BELI VIP → MENU PAKET
    # =====================================================
    @app.on_callback_query(filters.regex("^vip_buy:entry$"), group=1)
    async def vip_buy_entry(_, cq: CallbackQuery):
        if not cq.from_user:
            return

        try:
            await cq.answer()

            log.info(
                "[VIP][CB] buy entry user_id=%s",
                cq.from_user.id,
            )

            await send_vip_menu(
                event=cq,
                display_name=get_display_name(cq.from_user),
            )

        except FloodWait as e:
            log.warning(
                "[VIP][CB] entry FloodWait user_id=%s wait=%ss",
                cq.from_user.id,
                e.value,
            )
            await asyncio.sleep(e.value)

        except Exception:
            log.exception(
                "[VIP][CB] buy entry error user_id=%s",
                cq.from_user.id,
            )

    # =====================================================
    # PILIH PAKET → UPSELL / PAYMENT
    # =====================================================
    @app.on_callback_query(filters.regex(r"^vip_buy:"), group=2)
    async def vip_buy_paket(_, cq: CallbackQuery):
        if not cq.from_user:
            return

        user_id = cq.from_user.id

        try:
            await cq.answer()

            paket = cq.data.split(":", 1)[1]
            if paket == "entry":
                return

            if is_click_locked(user_id):
                await cq.answer("⏳ Tunggu sebentar...")
                return

            offers = build_upsell(paket)

            # ===============================
            # LANGSUNG KE PAYMENT
            # ===============================
            if not offers or get_upsell_context(user_id):
                await show_vip_payment_menu(
                    event=cq,
                    paket=paket,
                )
                return

            # ===============================
            # UPSELL = MENU (EDIT ONLY)
            # ===============================
            offer = offers[0]
            set_upsell_context(user_id, paket, offer.target_paket)

            await edit_menu(
                event=cq,
                text=offer.message,
                markup=upsell_keyboard(paket, offer.target_paket),
            )

        except FloodWait as e:
            log.warning(
                "[VIP][CB] paket FloodWait user_id=%s wait=%ss",
                user_id,
                e.value,
            )
            await asyncio.sleep(e.value)

        except Exception:
            log.exception(
                "[VIP][CB] paket error user_id=%s",
                user_id,
            )

    # =====================================================
    # PAYMENT LANGSUNG
    # =====================================================
    @app.on_callback_query(filters.regex(r"^vip_pay:"), group=3)
    async def vip_pay(_, cq: CallbackQuery):
        if not cq.from_user:
            return

        try:
            await cq.answer()

            paket = cq.data.split(":", 1)[1]

            log.info(
                "[VIP][CB] pay user_id=%s paket=%s",
                cq.from_user.id,
                paket,
            )

            await show_vip_payment_menu(
                event=cq,
                paket=paket,
            )

        except Exception:
            log.exception(
                "[VIP][CB] pay error user_id=%s",
                cq.from_user.id,
            )

    # =====================================================
    # NANTI DULU → KEMBALI KE ENTRY
    # =====================================================
    @app.on_callback_query(filters.regex("^vip_later$"), group=4)
    async def vip_later(_, cq: CallbackQuery):
        if not cq.from_user:
            return

        try:
            await cq.answer()

            log.info(
                "[VIP][CB] later user_id=%s",
                cq.from_user.id,
            )

            await show_vip_entry(
                event=cq,
            )

        except Exception:
            log.exception(
                "[VIP][CB] later error user_id=%s",
                cq.from_user.id,
            )
