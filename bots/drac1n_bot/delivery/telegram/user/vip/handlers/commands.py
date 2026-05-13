import asyncio
import time

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, RPCError

from configs.logging_setup import log
from config import BOT_USERNAME

from ..usecases.show_entry import show_vip_entry

DRAC1N_USER_GROUP = 1
VIP_TIMEOUT_SECONDS = 10


def register_vip_commands(app: Client) -> None:

    # =====================================================
    # 🧾 /vip di PRIVATE CHAT (FINAL)
    # =====================================================
    @app.on_message(filters.command("vip") & filters.private, group=DRAC1N_USER_GROUP)
    async def vip_command(client: Client, message: Message):
        start = time.perf_counter()

        user = message.from_user
        if not user:
            log.warning("[VIP][CMD] /vip ignored (no from_user)")
            return

        user_id = user.id
        log.info("[VIP][CMD] /vip start user_id=%s", user_id)

        try:
            # 🔒 WATCHDOG: cegah handler macet
            await asyncio.wait_for(
                show_vip_entry(
                    event=message,
                    display_name=message.from_user.username
                    or message.from_user.first_name,
                ),
                timeout=VIP_TIMEOUT_SECONDS,
            )

            log.info(
                "[VIP][CMD] /vip success user_id=%s elapsed=%.1fms",
                user_id,
                (time.perf_counter() - start) * 1000,
            )

        except asyncio.TimeoutError:
            log.error(
                "[VIP][CMD] /vip timeout user_id=%s timeout=%ss",
                user_id,
                VIP_TIMEOUT_SECONDS,
            )
            await message.reply_text(
                "⚠️ Sistem sedang sibuk.\nSilakan coba lagi sebentar.",
                quote=True,
            )

        except FloodWait as e:
            log.warning(
                "[VIP][CMD] FloodWait user_id=%s wait=%ss",
                user_id,
                e.value,
            )
            await asyncio.sleep(e.value)

        except RPCError as e:
            log.error(
                "[VIP][CMD] Telegram RPC error user_id=%s err=%s",
                user_id,
                e,
            )

        except Exception:
            log.exception("[VIP][CMD] /vip fatal error user_id=%s", user_id)
            await message.reply_text(
                "⚠️ Terjadi kesalahan internal.\nSilakan coba lagi.",
                quote=True,
            )

    # =====================================================
    # 👥 /vip di GROUP → redirect ke PM (SAFE)
    # =====================================================
    @app.on_message(filters.command("vip") & filters.group, group=DRAC1N_USER_GROUP)
    async def vip_group_redirect(_: Client, message: Message):
        try:
            log.info(
                "[VIP][CMD] /vip redirect group user_id=%s chat_id=%s",
                message.from_user.id if message.from_user else None,
                message.chat.id,
            )

            await message.reply_text(
                "⚠️ Untuk membuka menu VIP, silakan chat langsung di PM.\n\n"
                f'👉 <a href="https://t.me/{BOT_USERNAME}?start=vip">Klik di sini</a>',
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
            )

        except FloodWait as e:
            log.warning("[VIP][CMD] group FloodWait wait=%ss", e.value)
            await asyncio.sleep(e.value)

        except Exception:
            log.exception("[VIP][CMD] group redirect error")
