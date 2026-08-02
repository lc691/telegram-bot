from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from configs.logging_setup import log


def escape_markdown(text: str) -> str:
    if not text:
        return "-"
    return (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("-", "\\-")
    )


async def show_admin_detail_callback(
    client, callback_query: CallbackQuery, admin_id: int
):
    from shared.utils.admin_cache import admin_cache  # Hindari circular import

    if not admin_cache.is_admin(callback_query.from_user.id):
        log.warning(f"[ADMIN_DETAIL] User {callback_query.from_user.id} bukan admin.")
        await callback_query.answer("❌ Kamu bukan admin.", show_alert=True)
        return

    try:
        # STEP 1: Ambil info Telegram user
        user = await client.get_users(admin_id)
        name = escape_markdown(user.first_name or "Tanpa Nama")
        username = f"@{user.username}" if user.username else "Tidak ada"
        is_bot = "✅ Ya" if user.is_bot else "❌ Bukan"

        text = (
            f"👤 **Detail Admin:**\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"📛 Nama: {name}\n"
            f"🔗 Username: {username}\n"
            f"🤖 Bot: {is_bot}"
        )

        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Kembali", callback_data="admin_list_start")]]
        )

        await callback_query.message.edit_text(
            text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN
        )
        await callback_query.answer()
        log.info(f"[ADMIN_DETAIL] Detail admin {admin_id} ditampilkan.")

    except Exception as e:
        log.exception(f"[ADMIN_DETAIL] Gagal tampilkan detail admin {admin_id}: {e}")
        try:
            await callback_query.answer(
                "❌ Gagal menampilkan detail admin.", show_alert=True
            )
        except Exception as fallback:
            log.warning(f"[ADMIN_DETAIL] Gagal kirim fallback alert: {fallback}")


async def start_admin_detail_callback(client, callback_query: CallbackQuery, _):
    """
    Dipicu oleh callback_data seperti `admin_detail_123456`.
    """
    try:
        admin_id = int(callback_query.data.split("_")[-1])
        await show_admin_detail_callback(client, callback_query, admin_id)

    except ValueError:
        log.warning(f"[ADMIN_DETAIL] Callback data tidak valid: {callback_query.data}")
        await callback_query.answer("❌ ID admin tidak valid.", show_alert=True)

    except Exception as e:
        log.exception(f"[ADMIN_DETAIL] Error tak terduga: {e}")
        try:
            await callback_query.answer("❌ Terjadi kesalahan.", show_alert=True)
        except Exception:
            pass
