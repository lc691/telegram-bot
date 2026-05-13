from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from configs.logging_setup import log

from ..usecases.request.save_show_request import save_show_request


def register_request_show_callback(app: Client) -> None:
    """
    Callback handler untuk request drama / show oleh user.
    """

    @app.on_callback_query(filters.regex(r"^request:(search|main):(\d+)$"))
    async def request_show_entrypoint(
        client: Client,
        callback: CallbackQuery,
    ):
        try:
            if not callback.matches:
                await callback.answer(
                    "⚠️ Data request tidak valid",
                    show_alert=True,
                )
                return

            user = callback.from_user
            if not user:
                await callback.answer(
                    "❌ User tidak dikenali",
                    show_alert=True,
                )
                return

            source = callback.matches[0].group(1)   # search | main
            show_id = int(callback.matches[0].group(2))

            # 🔒 optional: block search request tanpa show_id valid
            if source == "search" and show_id == 0:
                await callback.answer(
                    "⚠️ Silakan pilih judul dari hasil pencarian.",
                    show_alert=True,
                )
                return

            saved = save_show_request(
                user_id=user.id,
                show_id=show_id,
                username=user.username,
                fullname=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                source=source,  # 👈 kalau mau disimpan/log
            )

            if not saved:
                await callback.answer(
                    "⚠️ Kamu sudah pernah request judul ini.",
                    show_alert=True,
                )
                return

            # log.info(
            #     "[REQUEST] ✅ source=%s | user=%s | show_id=%s",
            #     source,
            #     user.id,
            #     show_id,
            # )

            await callback.answer(
                "✅ Request berhasil dicatat!\n"
                "Admin akan update secepatnya 🙏",
                show_alert=True,
            )

            # UX: hanya hapus tombol untuk MAIN request
            if source == "main":
                try:
                    await callback.message.edit_reply_markup(None)
                except Exception:
                    pass

        except Exception:
            log.exception("[REQUEST] ❌ ERROR")
            await callback.answer(
                "❌ Terjadi kesalahan saat menyimpan request.",
                show_alert=True,
            )

