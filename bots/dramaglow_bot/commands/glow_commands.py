from pyrogram.types import BotCommand


def get_glow_commands() -> list[BotCommand]:
    return [
        BotCommand("start", "Muat ulang Bot"),
        BotCommand("status", "Cek status akun kamu"),
        BotCommand("referral", "Komisi 20%"),
        BotCommand("redeem", "Redeem voucher VIP"),
    ]
