from typing import List

from pyrogram import Client
from pyrogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

from bots.caridrama_bot.commands.cari_commands import get_cari_commands
from bots.dcst_mbot.commands.dcst_commands import get_dcst_commands
from bots.drac1n_bot.commands.drac1n_commands import get_drac1n_commands
from bots.dramaglow_bot.commands.glow_commands import get_glow_commands
from configs.logging_setup import log


def get_commands_by_bot_name(bot_name: str) -> List[BotCommand]:
    match bot_name.lower():
        case "drac1n_bot":
            return get_drac1n_commands()
        case "dramaglow_bot":
            return get_glow_commands()
        case "kelolain_bot":
            return get_dcst_commands()
        case "caridrama_bot":
            return get_cari_commands()
        case _:
            return []


async def apply_bot_commands(app: Client, admin_ids: List[int]):
    commands = get_commands_by_bot_name(app.name)
    if commands:
        try:
            # Hanya private chat, tidak muncul di grup
            await app.set_bot_commands(commands, scope=BotCommandScopeAllPrivateChats())
            log.info(f"✅ Command private untuk {app.name} berhasil diset.")
        except Exception:
            log.error(f"❌ Gagal menyetel command private: {app.name}", exc_info=True)
    else:
        log.warning(f"⚠️ Tidak ada command ditemukan untuk {app.name}")

    if not admin_ids:
        log.warning("⚠️ Tidak ada admin ID untuk disetel.")
        return

    admin_cmd = [
        BotCommand("dashboard", "Dashboard Admin"),
        BotCommand("commands", "Inspect Command"),
    ]

    for admin_id in admin_ids:
        try:
            await app.set_bot_commands(admin_cmd, scope=BotCommandScopeChat(admin_id))
            log.info(f"✅ Command admin diset untuk {admin_id}")
        except Exception:
            log.error(
                f"❌ Gagal menyetel command admin untuk {admin_id}", exc_info=True
            )


# Optional: checker command untuk bot (via /commands)
def register_command_checker(app: Client, admin_ids: List[int]):
    from pyrogram import filters
    from pyrogram.enums import ParseMode
    from pyrogram.types import (
        BotCommandScopeAllGroupChats,
        BotCommandScopeAllPrivateChats,
        Message,
    )

    log.info(f"🧩 Handler command checker didaftarkan dengan admin_ids={admin_ids}")

    @app.on_message(filters.command("commands") & filters.private)
    async def commands_handler(client: Client, message: Message):
        user_id = message.from_user.id

        async def format_scope(scope, scope_name):
            try:
                commands = await client.get_bot_commands(scope=scope)
                if commands:
                    lines = "\n".join(
                        f"/{cmd.command} - {cmd.description}" for cmd in commands
                    )
                    return f"**{scope_name}**\n{lines}\n"
                else:
                    return f"**{scope_name}**\n_(tidak ada command)_\n"
            except Exception as e:
                return f"⚠️ Gagal ambil {scope_name}: {e}"

        is_admin = user_id in admin_ids
        text = ""
        text += await format_scope(BotCommandScopeAllPrivateChats(), "👤 Private")
        if is_admin:
            text += await format_scope(
                BotCommandScopeChat(chat_id=user_id), f"🛡️ Admin ({user_id})"
            )

        await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
