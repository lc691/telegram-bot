from typing import List

from pyrogram import Client
from pyrogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

from bots.caridrama_bot.commands.cari_commands import get_cari_commands
from bots.dcst_mbot.commands.dcst_commands import get_dcst_commands
from bots.drac1n_bot.commands.drac1n_commands import get_drac1n_commands
from bots.dramaglow_bot.commands.glow_commands import get_glow_commands
from configs.logging_setup import log


# ==============================
# Mapping Command per Bot + Scope
# ==============================
def get_commands_by_bot_name(bot_name: str, scope: str) -> List[BotCommand]:
    name = bot_name.lower()

    # --- Default (semua user, semua chat)
    if scope == "default":
        return [
            BotCommand("menu", "Menu utama"),
            BotCommand("help", "Bantuan penggunaan bot"),
        ]

    # --- Private chat
    if scope == "private":
        if name == "drac1n_bot":
            return get_drac1n_commands()
        elif name in "dramaglow_bot":
            return get_glow_commands()
        elif name in ["kelolain_bot", "kelolain_bot"]:  # <-- perbaikan
            return get_dcst_commands()
        elif name == "caridrama_bot":
            return get_cari_commands()

    # --- Group chat (dibedakan per bot)
    if scope == "group":
        if name == "drac1n_bot":
            # log.info("➡️ Setting group commands khusus drac1n_bot")
            return [
                BotCommand("info", "Cek status"),
                BotCommand("vip", "Beli/perpanjang VIP"),
                BotCommand("referral", "Komisi 20%"),
            ]
        elif name == "dramaglow_bot":
            # log.info("➡️ Setting group commands khusus dramaglow_bot")
            return [
                BotCommand("info", "Cek status"),
                BotCommand("vip", "Beli/perpanjang VIP"),
                BotCommand("referral", "Komisi 20%"),
            ]
        elif name == "caridrama_bot":
            # log.info("➡️ Setting group commands khusus caridrama_bot")
            return [
                BotCommand("cari", "Cari Drama"),
            ]
        else:
            # log.info(f"➡️ Tidak ada group commands untuk {name}")
            return []

    # --- Admin scope (per user ID)
    if scope == "admin":
        return [
            BotCommand("dashboard", "Dashboard Admin"),
            BotCommand("vip", "Menu VIP"),
            BotCommand("status", "Cek status"),
            BotCommand("topvip", "Leaderboar VIP"),
            BotCommand("commands", "Inspect semua command"),
        ]

    return []


# ==============================
# Apply Commands ke Bot
# ==============================
async def apply_bot_commands(app: Client, admin_ids: list[int]):
    try:
        # Default commands
        default_cmds = get_commands_by_bot_name(app.name, "default")
        if default_cmds:
            await app.set_bot_commands(default_cmds, scope=BotCommandScopeDefault())
            log.info(f"✅ Default command diset untuk {app.name}")

        # Private commands
        private_cmds = get_commands_by_bot_name(app.name, "private")
        if private_cmds:
            await app.set_bot_commands(
                private_cmds, scope=BotCommandScopeAllPrivateChats()
            )
            log.info(f"✅ Private command diset untuk {app.name}")

        # Group commands
        group_cmds = get_commands_by_bot_name(app.name, "group")

        # selalu set, meski kosong → agar clear command lama
        await app.set_bot_commands(group_cmds, scope=BotCommandScopeAllGroupChats())

        if group_cmds:
            log.info(f"✅ Group command diset untuk {app.name}")
        else:
            log.info(f"🚫 Group command dikosongkan untuk {app.name}")

        # Admin commands
        if admin_ids:
            admin_cmds = get_commands_by_bot_name(app.name, "admin")
            for admin_id in admin_ids:
                await app.set_bot_commands(
                    admin_cmds, scope=BotCommandScopeChat(admin_id)
                )
                log.info(f"✅ Admin command diset untuk {admin_id}")

    except Exception:
        log.error(f"❌ Gagal menyetel commands untuk {app.name}", exc_info=True)


# ==============================
# Command Checker (/commands)
# ==============================
def register_command_checker(app: Client, admin_ids: list[int]):
    from pyrogram import filters
    from pyrogram.enums import ParseMode
    from pyrogram.types import Message

    # log.info(f"🧩 Handler command checker didaftarkan (admin_ids={admin_ids})")

    @app.on_message(filters.command("commands"))
    async def commands_handler(client: Client, message: Message):
        user_id = message.from_user.id

        async def format_scope(scope, scope_name):
            try:
                commands = await client.get_bot_commands(scope=scope)
                if commands:
                    lines = "\n".join(
                        f"/{c.command} - {c.description}" for c in commands
                    )
                    return f"**{scope_name}**\n{lines}\n"
                return f"**{scope_name}**\n_(tidak ada command)_\n"
            except Exception as e:
                return f"⚠️ Gagal ambil {scope_name}: {e}"

        text = ""
        text += await format_scope(BotCommandScopeDefault(), "🌍 Default")
        text += await format_scope(BotCommandScopeAllPrivateChats(), "👤 Private")
        text += await format_scope(BotCommandScopeAllGroupChats(), "👥 Group")

        if user_id in admin_ids:
            text += await format_scope(
                BotCommandScopeChat(chat_id=user_id), f"🛡️ Admin ({user_id})"
            )

        await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
