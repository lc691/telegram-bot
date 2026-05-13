import asyncio

from dotenv import load_dotenv
from pyrogram.enums import ParseMode

from bots.bot_initializer import create_utbk_app
from bots.bots_registry import register_bot
from common.bot_utils import resolve_bot
from common.messaging.success_message import build_success_message
from common.utils.get_user import safe_get_user
from configs.logging_setup import log
from db.vip_users.vip_status import get_latest_vip_info

# Setup
load_dotenv()

TARGET_USER_ID = 667088227
source_bot_KEY = "utbk"


async def main():
    # 🔧 Manual registrasi bot
    bot_instance = await create_utbk_app()
    if not bot_instance:
        log.critical(f"❌ Gagal membuat bot instance '{source_bot_KEY}'")
        return
    register_bot("utbk", bot_instance)

    # 🔍 Ambil bot
    bot = resolve_bot(source_bot_KEY)
    if not bot:
        log.error(f"❌ Bot '{source_bot_KEY}' tidak ditemukan.")
        return

    user = await safe_get_user(bot, TARGET_USER_ID)
    if not user:
        log.warning(f"⚠️ Gagal ambil data user: {TARGET_USER_ID}")
        return

    vip_info = get_latest_vip_info(TARGET_USER_ID, source_bot_KEY)
    if not vip_info:
        log.warning(f"⚠️ Tidak ada data VIP untuk user: {TARGET_USER_ID}")
        return

    msg = build_success_message(user, None, TARGET_USER_ID, vip_info, source_bot_KEY)
    try:
        await bot.send_message(
            chat_id=TARGET_USER_ID, text=msg, parse_mode=ParseMode.MARKDOWN
        )
        log.info(f"✅ Notifikasi VIP dikirim ke {TARGET_USER_ID}")
    except Exception as e:
        log.error(f"❌ Gagal kirim notifikasi: {e}")


if __name__ == "__main__":
    log.warning("⚠️ Data VIP tidak lengkap, tidak bisa kirim notifikasi.")
    asyncio.run(main())
