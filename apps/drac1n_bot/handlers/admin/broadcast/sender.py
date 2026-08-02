import asyncio

from psycopg2.errors import UndefinedColumn
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from configs.logging_setup import log
from database.user_management import deactivate_user, iterate_all_users

from .content import BROADCAST_BUTTONS


async def run_broadcast(client: Client, source_message: Message, broadcast_text: str):
    total_sent = 0
    total_failed = 0
    batch_index = 1

    async def log_batch(batch_num, sent, failed):
        log.info(f"[BROADCAST] Batch #{batch_num} → ✅ {sent} | ❌ {failed}")

    # Loop per batch user (100 per batch agar efisien)
    for batch in iterate_all_users(source="drac1n", batch_size=100):
        sent_this_batch = 0
        failed_this_batch = 0

        for row in batch:
            user_id = row[0]
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=broadcast_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=BROADCAST_BUTTONS,  # aktifkan jika ingin tombol di bawah pesan
                )
                total_sent += 1
                sent_this_batch += 1

                # jeda agar tidak kena limit spam
                await asyncio.sleep(0.2)

            except FloodWait as e:
                log.warning(f"[BROADCAST] ⏳ FloodWait {e.value}s. Tidur sebentar...")
                await asyncio.sleep(e.value)
                continue

            except RPCError as e:
                error_msg = str(e)
                log.warning(f"[BROADCAST] ❌ Gagal ke {user_id}: {error_msg}")
                total_failed += 1
                failed_this_batch += 1

                # tandai user tidak aktif kalau sudah block bot
                if "USER_IS_BLOCKED" in error_msg or "PEER_ID_INVALID" in error_msg:
                    deactivate_user(user_id)

            except Exception as e:
                log.error(f"[BROADCAST] ❌ Error tak terduga ke {user_id}: {e}")
                total_failed += 1
                failed_this_batch += 1

        await log_batch(batch_index, sent_this_batch, failed_this_batch)
        batch_index += 1

        # jeda tambahan antar batch biar makin aman
        await asyncio.sleep(2)

    await source_message.reply(
        f"📣 <b>Broadcast selesai!</b>\n\n"
        f"✅ <b>Terkirim:</b> {total_sent}\n"
        f"❌ <b>Gagal:</b> {total_failed}\n"
        f"🧾 <b>Total user:</b> {total_sent + total_failed}",
        parse_mode=ParseMode.HTML,
    )
