import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

WELCOME_THREAD_ID = 1

MIN_ACCOUNT_AGE_DAYS = 7  # akun < 7 hari → kick
JOIN_FLOOD_LIMIT = 5  # max 5 user
JOIN_FLOOD_WINDOW = 10  # dalam 10 detik

join_tracker = {}


def register_welcome_handler(app: Client):

    @app.on_message(filters.group & filters.new_chat_members)
    async def welcome_new_member(client: Client, message: Message):

        group_id = message.chat.id
        group_name = message.chat.title or "grup ini"
        now = time.time()

        # ===== Anti flood join =====
        join_tracker.setdefault(group_id, [])
        join_tracker[group_id] = [
            t for t in join_tracker[group_id] if now - t < JOIN_FLOOD_WINDOW
        ]
        join_tracker[group_id].append(now)

        if len(join_tracker[group_id]) > JOIN_FLOOD_LIMIT:
            # terlalu banyak join → skip welcome
            return

        for user in message.new_chat_members:

            # ===== Anti bot =====
            if user.is_bot:
                await client.ban_chat_member(group_id, user.id)
                continue

            # ===== Delay check =====
            await asyncio.sleep(2)

            # ===== Anti akun baru =====
            if user.date:
                account_age_days = (time.time() - user.date.timestamp()) / 86400
                if account_age_days < MIN_ACCOUNT_AGE_DAYS:
                    await client.ban_chat_member(group_id, user.id)
                    continue

            # ===== Welcome message =====
            user_name = user.first_name or "kak"

            welcome_text = (
                f"Hi {user_name}, selamat bergabung di {group_name} 🔥🔥\n\n"
                f"📌 Wajib baca <b>PINNED MESSAGE</b>\n"
                f"agar langsung paham cara mulai & dapat hasil 🚀"
            )

            await client.send_message(
                chat_id=group_id,
                text=welcome_text,
                parse_mode=ParseMode.HTML,
                message_thread_id=WELCOME_THREAD_ID,
            )
