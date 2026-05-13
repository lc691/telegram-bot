from pyrogram.types import BotCommand


def get_dcst_commands() -> list[BotCommand]:
    return [
        BotCommand("start", "Mulai bot DCST"),
        BotCommand("commands", "Lihat semua perintah bot"),
    ]
