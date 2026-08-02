import json

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery

from apps.drac1n_bot.services.vip_stats_service import get_vip_stats_message
from shared.utils.callback_helpers import safe_answer, safe_edit_text
from configs.logging_setup import log


def markup_to_str(markup):
    try:
        # Mengubah struktur keyboard ke bentuk string agar bisa dibandingkan
        return (
            json.dumps(
                [
                    [button.callback_data or button.text for button in row]
                    for row in markup.inline_keyboard
                ]
            )
            if markup
            else ""
        )
    except Exception as e:
        log.warning(f"[markup_to_str] Gagal serialisasi markup: {e}")
        return ""


async def handle_vip_stats(client: Client, callback_query: CallbackQuery):
    try:
        log.info(f"[VIP STATS] Callback diterima: {callback_query.data}")

        # 🔍 Parse data callback
        parts = callback_query.data.split(":")
        if len(parts) != 4:
            raise ValueError("Format callback tidak valid.")
        _, source, jenis, page_str = parts
        page = int(page_str)

        # 🔄 Ambil data dan keyboard
        new_text, keyboard = get_vip_stats_message(source, jenis, page)

        # 🧠 Cek apakah benar-benar ada perubahan
        current_text = (callback_query.message.text or "").strip()
        new_text = new_text.strip()

        current_markup_str = markup_to_str(callback_query.message.reply_markup)
        new_markup_str = markup_to_str(keyboard)

        if new_text != current_text or new_markup_str != current_markup_str:
            await safe_edit_text(
                callback_query.message,
                new_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        else:
            await safe_answer(callback_query, "✅ Sudah di halaman ini.")

    except Exception as e:
        log.exception(f"[VIP STATS] ❌ Error saat proses statistik: {e}")
        await safe_answer(callback_query, "❌ Gagal memuat statistik.", show_alert=True)


def register_vip_stats_handler():
    return (
        r"^vip_stats:(drac1n|utbk|vip|donation):(vip|donation):\d+$",
        handle_vip_stats,
    )


from apps.drac1n_bot.utils.vip_donation_chart import render_donation_chart
from database.repositories.stats.donation_aggregates import get_vip_donation_per_day


async def send_donation_chart(bot, chat_id: int, days: int = 7):
    data = get_vip_donation_per_day(days)
    if not data:
        await bot.send_message(chat_id, "📭 Belum ada donasi VIP pada periode ini.")
        return

    image = render_donation_chart(data, title=f"📊 Donasi VIP {days} Hari Terakhir")
    await bot.send_photo(
        chat_id=chat_id,
        photo=image,
        caption=f"📊 Statistik donasi {days} hari terakhir.",
    )
