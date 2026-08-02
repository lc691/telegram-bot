from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import SOURCE_CHANNEL_MAP
from database.connection import get_dict_cursor


# =========================
# DB FUNCTION (SYNC)
# =========================
def get_request_sources():
    query = """
        SELECT code, label
        FROM request_sources
        ORDER BY label ASC
    """

    with get_dict_cursor() as (cur, conn):
        cur.execute(query)
        return cur.fetchall()


# =========================
# UI BUILDER
# =========================
def build_main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📚 Platform Drama",
                    callback_data="show_platforms"
                ),
                InlineKeyboardButton(
                    "🔍 Cari Drama",
                    switch_inline_query_current_chat=""
                )
            ]
        ]
    )


def build_platform_keyboard(sources):
    buttons = []
    row = []

    for source in sources:
        code = source["code"]
        label = source["label"]

        channel_username = SOURCE_CHANNEL_MAP.get(code, [None])[0]

        if not channel_username:
            continue

        row.append(
            InlineKeyboardButton(
                label,
                url=f"https://t.me/{channel_username}"
            )
        )

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Kembali",
                callback_data="back_start"
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


# =========================
# HANDLER REGISTRATION
# =========================
def register_start_handler(app: Client):

    @app.on_message(filters.command(["start", "cari"]))
    async def start_handler(client, message):
        text = (
            "🎬 <b>Selamat datang di CariDrama Bot!</b>\n\n"
            "🔎 Cari drama favorit dari:\n"
            "🇰🇷 Korea • 🇨🇳 China • 🇯🇵 Jepang • 🇹🇭 Thailand\n\n"
            "📺 Pilih platform atau mulai mencari drama 👇"
        )

        await message.reply_text(
            text,
            reply_markup=build_main_keyboard(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    # =========================
    # SHOW PLATFORMS
    # =========================
    @app.on_callback_query(filters.regex("^show_platforms$"))
    async def show_platforms(client, callback_query: CallbackQuery):

        try:
            sources = get_request_sources()  # FIX: TIDAK PAKAI AWAIT

            keyboard = build_platform_keyboard(sources)

            text = (
                "📚 <b>Daftar Platform Drama</b>\n\n"
                "Pilih platform untuk membuka channel Telegram."
            )

            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            await callback_query.answer(
                "❌ Gagal memuat platform",
                show_alert=True
            )
            print(f"[ERROR show_platforms] {e}")

    # =========================
    # BACK
    # =========================
    @app.on_callback_query(filters.regex("^back_start$"))
    async def back_start(client, callback_query: CallbackQuery):

        await callback_query.message.edit_text(
            (
                "🎬 <b>Selamat datang di CariDrama Bot!</b>\n\n"
                "🔎 Cari drama favorit dari:\n"
                "🇰🇷 Korea • 🇨🇳 China • 🇯🇵 Jepang • 🇹🇭 Thailand\n\n"
                "📺 Pilih platform atau mulai mencari drama 👇"
            ),
            reply_markup=build_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
