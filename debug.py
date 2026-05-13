import asyncio
from typing import List, Union
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

from config import (
    API_ID,
    API_HASH,
    POSTING_CHANNEL,
    BACKUP_CHANNEL,
    TARGET_CHANNELS,
)

SESSION_NAME = "user-session"


def normalize_channels(*channels: Union[str, List[str]]) -> List[str]:
    """Menggabungkan dan menormalkan daftar channel."""
    result = []
    for ch in channels:
        if not ch:
            continue
        if isinstance(ch, list):
            result.extend(ch)
        else:
            result.append(ch)

    normalized = []
    for channel in result:
        channel = str(channel).strip()
        if not channel:
            continue
        if not channel.startswith("@") and not channel.startswith("-100"):
            channel = f"@{channel}"
        normalized.append(channel)

    # Hapus duplikasi
    return list(dict.fromkeys(normalized))


async def delete_messages_from_channel(app: Client, chat_id: str):
    """Menghapus semua pesan dari sebuah channel."""
    print(f"\n🗑️ Menghapus pesan dari: {chat_id}")
    deleted_count = 0

    try:
        async for message in app.get_chat_history(chat_id):
            try:
                await app.delete_messages(chat_id, message.id)
                deleted_count += 1

                if deleted_count % 50 == 0:
                    print(f"✅ {deleted_count} pesan dihapus dari {chat_id}")

                await asyncio.sleep(0.3)

            except FloodWait as e:
                print(f"⏳ FloodWait {e.value} detik...")
                await asyncio.sleep(e.value)

            except RPCError as e:
                print(f"⚠️ Gagal menghapus pesan {message.id}: {e}")

    except Exception as e:
        print(f"❌ Error pada {chat_id}: {e}")

    print(f"🎉 Selesai! Total {deleted_count} pesan dihapus dari {chat_id}")


async def main():
    async with Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    ) as app:

        me = await app.get_me()
        print(f"👤 Login sebagai: {me.first_name} (@{me.username or 'N/A'})")

        channels = normalize_channels(
            POSTING_CHANNEL,
            BACKUP_CHANNEL,
            TARGET_CHANNELS,
        )

        print("\n📋 Daftar Channel yang akan dibersihkan:")
        for ch in channels:
            print(f" - {ch}")

        for channel in channels:
            await delete_messages_from_channel(app, channel)


if __name__ == "__main__":
    asyncio.run(main())
