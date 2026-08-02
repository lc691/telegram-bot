# app/usecases/vip/payment.py
from urllib.parse import urlencode

from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from shared.utils.message_utils import safe_send_or_edit
from infrastructure.webhook.utils.trakteer_transactions import get_unit_price_from_db
from database.vip_users.vip_db_utils import get_vip_package_info

TRAKTEER_BASE_URL = "https://trakteer.id/mischelia/tip?step=1"


def gen_vip_link(
    base_url: str,
    kode_base: str,
    username: str,
    paket: str,
    price: int,
) -> str:
    unit_price = get_unit_price_from_db(default=1000)
    quantity = price // unit_price

    params = {
        "quantity": quantity,
        "display_name": username,
        "supporter_message": f"{kode_base}_{paket}",
    }

    return f"{base_url}&{urlencode(params)}"


async def send_payment_link(
    client: Client,
    callback_query: CallbackQuery,
    paket: str,
):
    user = callback_query.from_user
    user_id = user.id

    paket_info = get_vip_package_info(paket)
    price = paket_info["price"]

    url = gen_vip_link(
        TRAKTEER_BASE_URL,
        f"daftar_short_{user_id}",
        user.username,
        paket,
        price,
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Bayar via Trakteer", url=url)],
        [InlineKeyboardButton("↩️ Kembali", callback_data="vip_menu")],
    ])

    await safe_send_or_edit(
        client=client,
        user_id=user_id,
        text="🔗 Klik tombol di bawah untuk lanjut pembayaran:",
        markup=markup,
        event=callback_query,
    )
