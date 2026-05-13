from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def vip_home_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💎 BELI VIP SEKARANG",
                    callback_data="vip_buy:entry",
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ Nanti Dulu",
                    callback_data="vip_later",
                )
            ],
        ]
    )


def upsell_keyboard(source: str, target: str):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"🚀 Upgrade ke VIP {target.upper()}",
                    callback_data=f"vip_pay:{target}",
                )
            ],
            [
                InlineKeyboardButton(
                    f"➡️ Lanjutkan VIP {source.upper()}",
                    callback_data=f"vip_pay:{source}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ Nanti Dulu",
                    callback_data="vip_later",
                )
            ],
        ]
    )
