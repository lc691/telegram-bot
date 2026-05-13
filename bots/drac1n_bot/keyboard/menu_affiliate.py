import asyncio

from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..handlers.user.referral.referral_link import referral_link_handler
from ..handlers.user.referral.referral_stats import referral_stats_handler

# =====================================================
# MENYIMPAN PESAN REFERRAL PER USER AGAR SELALU EDIT
# =====================================================
referral_message_store = {}


# =====================================================
# HELPER: KIRIM ATAU EDIT PESAN REFERRAL
# =====================================================
async def send_or_edit_referral_menu(client, message, text, keyboard):
    chat_id = message.chat.id
    user_id = message.from_user.id
    key = f"{chat_id}:{user_id}"

    # Jika pesan referral sudah ada → edit
    if key in referral_message_store:
        msg = referral_message_store[key]
        try:
            await msg.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            return msg
        except Exception:
            pass  # Jika gagal edit, lanjut bikin pesan baru

    # Jika belum ada → kirim pesan baru
    sent = await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

    referral_message_store[key] = sent
    return sent


# =====================================================
# MENU REFERRAL (MAIN MENU)
# =====================================================
async def referral_menu_handler(client: Client, message):

    text = (
        "🎯 <b>PROGRAM AFFILIATE VIP DCSTV</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💰 <b>Dapatkan KOMISI hingga 20% dari setiap pembelian VIP!</b>\n\n"
        "Ajak teman kamu untuk bergabung menggunakan link referral milikmu.\n"
        "Setiap mereka membeli VIP, kamu langsung mendapat komisi otomatis.\n\n"
        "🚀 <b>Keuntungan Join Affiliate:</b>\n"
        "✅ Komisi besar tanpa batas\n"
        "✅ Tanpa modal, 100% gratis\n"
        "✅ Bisa dicairkan ke OVO, DANA, GOPAY, dan BANK\n"
        "✅ Statistik real-time & transparan\n\n"
        "🛡️ <b>Aman & Terpercaya</b>\n"
        "Sistem otomatis melacak semua referral kamu.\n"
        "Anti fraud & self-referral.\n\n"
        "👇 <b>Pilih menu di bawah untuk mulai menghasilkan:</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Referral Link", callback_data="ref_link")],
        [
            InlineKeyboardButton("📊 Referral Stats", callback_data="ref_stats"),
            InlineKeyboardButton("💵 Withdraw", callback_data="ref_withdraw"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="ref_close")],
    ])

    await send_or_edit_referral_menu(client, message, text, keyboard)


# =====================================================
# WITHDRAW INSTRUCTION (EDIT PESAN)
# =====================================================
async def show_withdraw_instructions(client, callback_query):

    msg = callback_query.message

    text = (
        "💵 <b>WITHDRAW AFFILIATE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Gunakan format berikut:\n"
        "<code>/r_wd &lt;metode&gt; &lt;jumlah&gt; &lt;tujuan&gt;</code>\n\n"
        "Contoh:\n"
        "<code>/r_wd ovo 100000 081234567890</code>\n\n"
        "Metode tersedia:\n"
        "• OVO\n"
        "• DANA\n"
        "• GOPAY\n"
        "• BANK"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Referral Link", callback_data="ref_link"),
            InlineKeyboardButton("📊 Referral Stats", callback_data="ref_stats"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="ref_close")],
    ])

    await msg.edit_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

    await callback_query.answer()


# =====================================================
# AUTO DELETE 10 DETIK
# =====================================================
async def auto_delete_message(message, delay=10):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


# =====================================================
# CALLBACK HANDLER
# =====================================================
async def referral_callback_handler(client: Client, callback_query):

    if not callback_query.message:
        await callback_query.answer("⛔ Menu sudah ditutup", show_alert=True)
        return

    data = callback_query.data
    msg = callback_query.message
    user_id = callback_query.from_user.id
    chat_id = msg.chat.id
    key = f"{chat_id}:{user_id}"

    if data == "ref_link":
        await referral_link_handler(client, msg)

    elif data == "ref_stats":
        await referral_stats_handler(client, msg)

    elif data == "ref_withdraw":
        await show_withdraw_instructions(client, callback_query)
    
    elif data == "ref_menu":
        await referral_menu_handler(client, msg)

    elif data == "ref_close":
        # Edit menjadi pesan penutup
        await msg.edit_text(
            "✅ Menu ditutup.\n"
            "🧹 Pesan ini akan terhapus otomatis dalam 10 detik...",
            parse_mode=ParseMode.HTML
        )

        # Hapus dari store
        referral_message_store.pop(key, None)

        # Auto delete
        asyncio.create_task(auto_delete_message(msg, 10))

        await callback_query.answer()
        return

    await callback_query.answer()


# =====================================================
# ENTRYPOINT (GROUP REDIRECT → PRIVATE)
# =====================================================
async def referral_menu_entrypoint(client: Client, message):

    # Jika di grup → redirect ke private
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):

        try:
            await message.reply(
                "⚠️ <b>Menu Referral hanya bisa dibuka di Private Chat.</b>\n\n"
                "👉 <a href='https://t.me/drac1n_bot?start=referral_menu'>Klik di sini untuk membuka</a>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception:
            await message.reply(
                "❗ Tidak bisa mengarahkan ke private.\n"
                "Silakan buka bot dan kirim: /referral",
                parse_mode=ParseMode.HTML
            )
        return

    # Jika private → tampilkan menu
    await referral_menu_handler(client, message)


# =====================================================
# REGISTER HANDLER
# =====================================================
def register_referral(app: Client):

    app.add_handler(
        MessageHandler(
            referral_menu_entrypoint,
            filters.command(["referral", "r_menu", "r_link"])
        ),
        group=1,
    )

    app.add_handler(
        CallbackQueryHandler(referral_callback_handler, filters.regex(r"^ref_")),
        group=1,
    )
