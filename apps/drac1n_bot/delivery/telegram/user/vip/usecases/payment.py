from urllib.parse import urlencode

from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

from configs.logging_setup import log
from shared.utils.menu_utils import edit_menu

from database.vip_users.vip_db_utils import get_vip_package_info
from infrastructure.webhook.utils.trakteer_transactions import get_unit_price_from_db


TRAKTEER_BASE_URL = "https://trakteer.id/mischelia/tip?step=1"


def gen_vip_link(base_url, kode_base, username, paket, price):
    unit_price = get_unit_price_from_db(default=1000)
    quantity = price // unit_price

    params = {
        "quantity": quantity,
        "display_name": username,
        "supporter_message": f"{kode_base}_{paket}",
    }

    return f"{base_url}&{urlencode(params)}"


async def show_vip_payment_menu(*, event: CallbackQuery, paket: str):
    """
    VIP PAYMENT MENU
    - MENU (EDIT)
    - single-message UI
    """

    cq = event
    user = cq.from_user
    if not user:
        return

    user_id = user.id
    username = user.username or user.first_name or "User"

    await cq.answer()

    try:
        paket_info = get_vip_package_info(paket)
        price = paket_info["price"]

        url = gen_vip_link(
            TRAKTEER_BASE_URL,
            f"daftar_short_{user_id}",
            username,
            paket,
            price,
        )

        text = (
            "💳 <b>Langkah Terakhir — Aktivasi VIP</b>\n\n"
            "═══════✦✧✦═══════\n"
            "⚡ VIP aktif otomatis setelah pembayaran\n\n"
            "📌 Saat checkout di Trakteer:\n"
            "├─ ⚠️Jangan centang <b>Bayar anonim/privat</b>\n"
            "└─ ⚠️Simpan screenshot pembayaran sebagai cadangan\n"
            "═══════✦✧✦═══════\n\n"
            "👇 <b>Klik tombol di bawah untuk bayar & aktifkan VIP</b>"
        )

        markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🚀 AKTIFKAN VIP SEKARANG", url=url)],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="vip_later")],
            ]
        )

        await edit_menu(
            event=cq,
            text=text,
            markup=markup,
            parse_mode=ParseMode.HTML,
        )

        log.info(
            "[VIP][PAYMENT][MENU] rendered user_id=%s paket=%s",
            user_id,
            paket,
        )

    except FloodWait as e:
        log.warning(
            "[VIP][PAYMENT][MENU] FloodWait user_id=%s wait=%ss",
            user_id,
            e.value,
        )

    except Exception:
        log.exception(
            "[VIP][PAYMENT][MENU] fatal error user_id=%s paket=%s",
            user_id,
            paket,
        )
        await edit_menu(
            event=cq,
            text="❌ Terjadi kesalahan sistem.\nSilakan coba lagi.",
            parse_mode=ParseMode.HTML,
        )
