# handlers/user/image_match_callback_handler.py

import asyncio
import html

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from configs.logging_setup import log

from ....usecases.image_match.confirm_match_usecase import confirm_match_usecase
from ....usecases.image_match.request_show_usecase import request_show_usecase
from ....utils.callback_guard import is_double_click
from ....utils.telegram import build_message_url


# =====================================================
# Helpers
# =====================================================

def _parse_cb(data: str) -> list[str]:
    return data.split(":")


async def _fast_answer(cb: CallbackQuery, text: str | None = None):
    """
    Aman dipanggil berkali-kali (Telegram akan ignore duplikat).
    """
    try:
        await cb.answer(text or "")
    except Exception:
        pass


# =====================================================
# Handler registration
# =====================================================

def register_image_match_callback_handler(app: Client) -> None:
    if getattr(app, "_image_match_callback_registered", False):
        return
    app._image_match_callback_registered = True

    @app.on_callback_query()
    async def image_match_callback_entrypoint(_: Client, cb: CallbackQuery):
        data = cb.data
        user = cb.from_user

        if not data or not user:
            await _fast_answer(cb)
            return

        parts = _parse_cb(data)
        action = parts[0]
        user_id = user.id

        log.info(
            "[IMG_MATCH][CB] received action=%s user=%s data=%s",
            action,
            user_id,
            data,
        )

        try:
            # ==================================================
            # 1️⃣ VALIDATE USER OWNERSHIP
            # ==================================================
            if action in {"confirm", "confirm_ocr", "request"}:
                target_user_id = int(parts[-1])
                if user_id != target_user_id:
                    await cb.answer("❌ Tombol ini bukan untuk kamu", show_alert=True)
                    return

            if action == "approve_request":
                admin_id = int(parts[-1])
                if user_id != admin_id:
                    await cb.answer("❌ Khusus admin", show_alert=True)
                    return

            # ==================================================
            # 2️⃣ ANTI DOUBLE CLICK (TTL)
            # ==================================================
            key = f"{user_id}:{data}"
            if is_double_click(key):
                await cb.answer("⏳ Tunggu sebentar...", show_alert=False)
                return

            # ==================================================
            # 3️⃣ FAST ANSWER (UX)
            # ==================================================
            await _fast_answer(cb)

            # ==================================================
            # 4️⃣ DISPATCH ACTION
            # ==================================================

            # 🔹 Confirm match (embedding / OCR)
            if action in {"confirm", "confirm_ocr"}:
                show_id = int(parts[1])

                log.info(
                    "[IMG_MATCH][CB] confirm start user=%s show=%s",
                    user_id,
                    show_id,
                )

                show = await asyncio.to_thread(
                    confirm_match_usecase,
                    show_id,
                )

                if not show:
                    await cb.answer("⚠️ File belum tersedia", show_alert=True)
                    return

                url = build_message_url(
                    show.get("channel_username"),
                    show.get("file_message_id")
                )

                text = (
                    f"🎬 <b>{html.escape(show['title'])}</b>\n"
                    f"🔗 {url}"
                )

                try:
                    await cb.message.edit(text, parse_mode=ParseMode.HTML)
                except Exception:
                    await cb.message.reply(text, parse_mode=ParseMode.HTML)

                log.info(
                    "[IMG_MATCH][CB] confirm done user=%s show=%s",
                    user_id,
                    show_id,
                )
                return

            # 🔹 User request show
            if action == "request":
                show_id = int(parts[1])

                log.info(
                    "[IMG_MATCH][CB] request start user=%s show=%s",
                    user_id,
                    show_id,
                )

                await asyncio.to_thread(
                    request_show_usecase,
                    user_id,
                    f"manual_{show_id}",
                )

                await cb.answer("📩 Permintaan dikirim ke admin")

                # UX polish: disable keyboard
                try:
                    await cb.message.edit_reply_markup(None)
                except Exception:
                    pass

                log.info(
                    "[IMG_MATCH][CB] request done user=%s show=%s",
                    user_id,
                    show_id,
                )
                return

            # ==================================================
            # UNKNOWN ACTION
            # ==================================================
            log.warning(
                "[IMG_MATCH][CB] unknown action=%s user=%s",
                action,
                user_id,
            )
            await cb.answer("⚠️ Aksi tidak dikenali", show_alert=True)

        except Exception:
            log.exception("[IMG_MATCH][CB] ERROR data=%s", data)
            await cb.answer("⚠️ Terjadi kesalahan", show_alert=True)
