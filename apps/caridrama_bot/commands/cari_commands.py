from pyrogram.types import BotCommand


def get_cari_commands() -> list[BotCommand]:
    return [
        BotCommand("start", "Mulai bot CARI"),
        BotCommand("cari", "Cari Drama"),
    ]
