from datetime import datetime
from pytz import timezone
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from common.utils.request_state_manager import UserRequestStateManager
from configs.logging_setup import log
from config import ADMIN_IDS, POSTING_CHANNEL

from .redeem_parser import parse_redeem_command
from .redeem_voucher import redeem_voucher

TZ_WIB = timezone("Asia/Jakarta")


async def handle_redeem_command(client: Client, message: Message):
    now = datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S")
    sender = message.from_user
    sender_id = sender.id
    is_admin = sender_id in ADMIN_IDS

    # reset FSM
    UserRequestStateManager(sender_id).clear_all()

    parsed = parse_redeem_command(
        text=message.text,
        sender_id=sender_id,
        is_admin=is_admin,
    )

    if not parsed:
        await message.reply(
            "❗ Format salah!\n\n"
            "User: <code>/redeem KODE</code>\n"
            "Admin: <code>/redeem USER_ID KODE</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        username = sender.username or f"user{sender_id}"

        if parsed.mode == "admin":
            user_obj = await client.get_users(parsed.target_user_id)
            username = user_obj.username or f"user{parsed.target_user_id}"

        log.info(
            "[%s] [REDEEM] mode=%s user_id=%s code=%s",
            now,
            parsed.mode,
            parsed.target_user_id,
            parsed.voucher_code,
        )

        result = await redeem_voucher(
            app=client,
            user_id=parsed.target_user_id,
            username=username,
            code=parsed.voucher_code,
            vip_group_id=POSTING_CHANNEL,
        )

    except Exception:
        log.exception("[REDEEM] ERROR user=%s", sender_id)
        result = "🚨 Terjadi kesalahan saat memproses voucher."

    await message.reply(
        result,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
