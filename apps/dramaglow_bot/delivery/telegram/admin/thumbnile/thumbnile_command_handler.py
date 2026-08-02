import os
import html

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from configs.logging_setup import log
from .....usecases.admin.thumbnile.update_thumbnail_flow import (
    update_thumbnail_flow,
)


def register_thumbnail_handler(app: Client):

    @app.on_message(
        (filters.photo | filters.document) & filters.private,
        group=12,
    )
    async def auto_update_thumbnail(client: Client, message: Message):

        file_path: str | None = None

        try:
            result, file_path = await update_thumbnail_flow(
                client=client,
                message=message,
            )

            # =====================================================
            # Defensive Extraction
            # =====================================================
            title = html.escape(str(result.get("title", "-")))
            series_no = html.escape(str(result.get("series_no", "-")))
            source_label = html.escape(str(result.get("source_label", "-")))
            url = result.get("url")
            mode = result.get("mode", "telegram_only")

            caption_info = (
                f"<b>{title}</b>\n"
                f"Series: <code>{series_no}</code>\n"
                f"Platform: <b>{source_label}</b>"
            )

            # =====================================================
            # Success Response
            # =====================================================
            if mode == "full" and url:
                reply_text = (
                    "✅ <b>Thumbnail berhasil diperbarui</b>\n\n"
                    f"{caption_info}\n"
                    f"🌐 {html.escape(url)}"
                )
            else:
                reply_text = (
                    "⚠️ <b>Thumbnail disimpan (Telegram only)</b>\n\n" f"{caption_info}"
                )

            await message.reply(
                reply_text,
                parse_mode=ParseMode.HTML,
            )

        # =====================================================
        # Validation Error
        # =====================================================
        except ValueError as e:
            await message.reply(
                f"⚠️ {html.escape(str(e))}",
                parse_mode=ParseMode.HTML,
            )

        # =====================================================
        # Unexpected Error
        # =====================================================
        except Exception as e:
            log.exception("[THUMBNAIL] FAILED: %s", e)
            await message.reply(
                "❌ Gagal update thumbnail",
                parse_mode=ParseMode.HTML,
            )

        # =====================================================
        # Cleanup
        # =====================================================
        finally:
            if file_path and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    log.warning(
                        "[THUMBNAIL] cleanup failed: %s",
                        e,
                    )

            try:
                await message.delete()
            except Exception:
                log.debug("[THUMBNAIL] message delete skipped")
