from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# from ..guards.allow_button_only import allow_button_only
from ..guards.allow_image_match import allow_image_match
from ....presenters.image_match_presenter import ImageMatchPresenter
from ....usecases.image_match.match_image_usecase import match_image_usecase
from ....utils.telegram_safe import safe_edit
from ....utils.telegram_send_photo_safe import send_photo_safe

from configs.logging_setup import log


def register_image_match_handler(app: Client):
    @app.on_message(filters.group & (filters.photo | filters.document), group=-1)
    async def image_match_handler(client: Client, message: Message):

        # ==================================================
        # 0️⃣ AUTO POSTING / ANON ADMIN / CHANNEL POST
        #     → TAMPILKAN TOMBOL SAJA
        # ==================================================
        if message.sender_chat and not message.from_user:
            log.info(
                "[IMG_MATCH] auto_post detected chat=%s sender_chat=%s",
                message.chat.id,
                message.sender_chat.id,
            )

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔍 Cari Drama", switch_inline_query_current_chat=""
                        )
                    ]
                ]
            )

            await message.reply_text(
                "📺 Mau cari drama? Klik tombol di bawah ini:",
                reply_markup=keyboard,
            )
            return

        # ==================================================
        # 1️⃣ USER MESSAGE REQUIRED
        # ==================================================
        user = message.from_user
        if not user:
            log.info(
                "[IMG_MATCH] skip message without user chat=%s",
                message.chat.id,
            )
            return

        user_id = user.id
        log.info("[IMG_MATCH] start user=%s", user_id)

        # ==================================================
        # 2️⃣ IMAGE MATCH GUARD
        # ==================================================
        if not await allow_image_match(client, message):
            log.info("[IMG_MATCH] guard_blocked user=%s", user_id)
            return

        # ==================================================
        # 3️⃣ PROCESSING FEEDBACK
        # ==================================================
        processing = await message.reply("⏳ Sedang mencocokkan gambar…")

        # ==================================================
        # 4️⃣ DOWNLOAD IMAGE
        # ==================================================
        file_path = await message.download()
        if not file_path:
            log.warning("[IMG_MATCH] download_failed user=%s", user_id)
            await safe_edit(processing, "⚠️ Gagal mengunduh gambar.")
            return

        log.info("[IMG_MATCH] downloaded user=%s file=%s", user_id, file_path)

        # ==================================================
        # 5️⃣ RUN IMAGE MATCH USECASE
        # ==================================================
        try:
            result = await match_image_usecase(
                user_id=user_id,
                image_path=file_path,
            )
        except Exception:
            log.exception("[IMG_MATCH] usecase_error user=%s", user_id)
            await safe_edit(
                processing,
                "⚠️ Terjadi kesalahan saat memproses gambar.",
            )
            return

        log.info(
            "[IMG_MATCH] result user=%s status=%s",
            user_id,
            result.status,
        )

        # ==================================================
        # 6️⃣ PRESENT RESULT
        # ==================================================
        payload = ImageMatchPresenter.build(result, user_id)

        # 1️⃣ PHOTO RESULT
        if "photo" in payload:

            await processing.delete()

            photo = payload["photo"]

            try:

                # ==========================================
                # URL → SAFE DOWNLOAD
                # ==========================================

                if isinstance(photo, str) and photo.startswith("http"):

                    await send_photo_safe(
                        client=client,
                        chat_id=message.chat.id,
                        photo_url=photo,
                        caption=payload.get("caption"),
                        parse_mode=ParseMode.HTML,
                        reply_markup=payload.get("reply_markup"),
                    )

                # ==========================================
                # FILE_ID / LOCAL FILE / BYTES
                # ==========================================

                else:

                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=photo,
                        caption=payload.get("caption"),
                        parse_mode=ParseMode.HTML,
                        reply_markup=payload.get("reply_markup"),
                    )

            except Exception:

                log.exception(
                    "[IMG_MATCH] send_photo_failed user=%s",
                    user_id,
                )

                # fallback text only
                await client.send_message(
                    chat_id=message.chat.id,
                    text=payload.get("caption")
                    or payload.get("text")
                    or "⚠️ Gagal menampilkan gambar.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=payload.get("reply_markup"),
                )

            return

        # 2️⃣ THUMB_URL → SAFE PHOTO SEND
        if "thumb_url" in payload:

            await processing.delete()

            try:

                await send_photo_safe(
                    client=client,
                    chat_id=message.chat.id,
                    photo_url=payload["thumb_url"],
                    caption=payload["text"],
                    parse_mode=ParseMode.HTML,
                    reply_markup=payload.get("reply_markup"),
                )

            except Exception:

                log.exception(
                    "[IMG_MATCH] send_photo_safe_failed user=%s",
                    user_id,
                )

                # fallback text only
                await client.send_message(
                    chat_id=message.chat.id,
                    text=payload["text"],
                    parse_mode=ParseMode.HTML,
                    reply_markup=payload.get("reply_markup"),
                )

            return

        # 3️⃣ TEKS SAJA
        await safe_edit(
            processing,
            payload["text"],
            parse_mode=ParseMode.HTML,
            reply_markup=payload.get("reply_markup"),
        )
