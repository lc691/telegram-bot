from typing import List

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    Message,
)

from apps.caridrama_bot.commands.cari_commands import (
    get_cari_commands,
)
from apps.dcst_mbot.commands.dcst_commands import (
    get_dcst_commands,
)
from apps.drac1n_bot.commands.drac1n_commands import (
    get_drac1n_commands,
)
from apps.dramaglow_bot.commands.glow_commands import (
    get_glow_commands,
)
from configs.logging_setup import log


# =====================================================
# COMMAND MAPPING
# =====================================================

GROUP_COMMON_COMMANDS = [
    BotCommand("info", "Cek status"),
    BotCommand("vip", "Beli/perpanjang VIP"),
    BotCommand("referral", "Komisi 20%"),
]

ADMIN_COMMANDS = [
    BotCommand("dashboard", "Dashboard Admin"),
    BotCommand("vip", "Menu VIP"),
    BotCommand("status", "Cek status"),
    BotCommand("topvip", "Leaderboard VIP"),
    BotCommand("restart", "Restart service"),
    BotCommand("logs", "Service logs"),
    BotCommand("commands", "Inspect commands"),
]


def get_commands_by_bot_name(
    bot_name: str,
    scope: str,
) -> List[BotCommand]:

    name = bot_name.lower()

    # =================================================
    # DEFAULT
    # =================================================

    if scope == "default":
        return [
            BotCommand("menu", "Menu utama"),
            BotCommand("help", "Bantuan penggunaan bot"),
        ]

    # =================================================
    # PRIVATE
    # =================================================

    if scope == "private":

        if name == "drac1n_bot":
            return get_drac1n_commands()

        if name == "dramaglow_bot":
            return get_glow_commands()

        if name == "kelolain_bot":
            return get_dcst_commands()

        if name == "caridrama_bot":
            return get_cari_commands()

        return []

    # =================================================
    # GROUP
    # =================================================

    if scope == "group":

        if name in {
            "drac1n_bot",
            "dramaglow_bot",
        }:
            return GROUP_COMMON_COMMANDS

        if name == "caridrama_bot":
            return [
                BotCommand("cari", "Cari Drama"),
            ]

        return []

    # =================================================
    # ADMIN
    # =================================================

    if scope == "admin":
        return ADMIN_COMMANDS

    return []


# =====================================================
# APPLY COMMANDS
# =====================================================

async def apply_bot_commands(
    app: Client,
    admin_ids: list[int],
):

    try:

        # =============================================
        # DEFAULT
        # =============================================

        default_cmds = get_commands_by_bot_name(
            app.name,
            "default",
        )

        if default_cmds:
            await app.set_bot_commands(
                default_cmds,
                scope=BotCommandScopeDefault(),
            )

        # =============================================
        # PRIVATE
        # =============================================

        private_cmds = get_commands_by_bot_name(
            app.name,
            "private",
        )

        if private_cmds:
            await app.set_bot_commands(
                private_cmds,
                scope=BotCommandScopeAllPrivateChats(),
            )

        # =============================================
        # GROUP
        # =============================================

        group_cmds = get_commands_by_bot_name(
            app.name,
            "group",
        )

        await app.set_bot_commands(
            group_cmds,
            scope=BotCommandScopeAllGroupChats(),
        )

        # =============================================
        # ADMIN
        # =============================================

        if admin_ids:

            admin_cmds = get_commands_by_bot_name(
                app.name,
                "admin",
            )

            for admin_id in admin_ids:

                await app.set_bot_commands(
                    admin_cmds,
                    scope=BotCommandScopeChat(admin_id),
                )

        log.info(
            "[%s] commands configured",
            app.name,
        )

    except Exception:

        log.exception(
            "[%s] failed configuring commands",
            app.name,
        )


# =====================================================
# /COMMANDS INSPECTOR
# =====================================================

def register_command_checker(
    app: Client,
    admin_ids: list[int],
):

    from pyrogram import filters

    @app.on_message(filters.command("commands"))
    async def commands_handler(
        client: Client,
        message: Message,
    ):

        user_id = message.from_user.id

        async def format_scope(
            scope,
            title: str,
        ) -> str:

            try:

                commands = await client.get_bot_commands(
                    scope=scope
                )

                if not commands:
                    return (
                        f"**{title}**\n"
                        "_(tidak ada command)_\n\n"
                    )

                lines = "\n".join(
                    f"/{c.command} - {c.description}"
                    for c in commands
                )

                return f"**{title}**\n{lines}\n\n"

            except Exception as e:

                return (
                    f"⚠️ Gagal ambil {title}: {e}\n\n"
                )

        sections = [
            await format_scope(
                BotCommandScopeDefault(),
                "🌍 Default",
            ),
            await format_scope(
                BotCommandScopeAllPrivateChats(),
                "👤 Private",
            ),
            await format_scope(
                BotCommandScopeAllGroupChats(),
                "👥 Group",
            ),
        ]

        if user_id in admin_ids:

            sections.append(
                await format_scope(
                    BotCommandScopeChat(chat_id=user_id),
                    f"🛡️ Admin ({user_id})",
                )
            )

        await message.reply_text(
            "".join(sections),
            parse_mode=ParseMode.MARKDOWN,
        )
