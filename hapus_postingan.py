import asyncio
from typing import Union, List
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

from config import API_ID, API_HASH, POSTING_CHANNEL, TARGET_CHANNELS, BACKUP_CHANNEL

SESSION_NAME = "delete-all-posts"


def normalize_channels(channels: Union[str, int, List[Union[str, int]]]):
    """Mengubah input channel menjadi list yang seragam."""
    if not channels:
        return []

    if isinstance(channels, (str, int)):
        channels = [channels]

    normalized = []
    for ch in channels:
        if (
            isinstance(ch, str)
            and not ch.startswith("@")
            and not str(ch).startswith("-100")
        ):
            normalized.append(f"@{ch}")
        else:
            normalized.append(ch)

    return normalized


async def delete_messages_from_channel(app: Client, chat_id):
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
    async with Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH) as app:

        all_channels = []

        # Tambahkan POSTING_CHANNEL
        if POSTING_CHANNEL:
            all_channels.extend(normalize_channels(POSTING_CHANNEL))

        # # Tambahkan TARGET_CHANNELS
        # if TARGET_CHANNELS:
        #     all_channels.extend(normalize_channels(TARGET_CHANNELS))

        # # Tambahkan BACKUP_CHANNEL
        # if BACKUP_CHANNEL:
        #     all_channels.extend(normalize_channels(BACKUP_CHANNEL))

        # Hapus duplikasi
        unique_channels = list(dict.fromkeys(all_channels))

        print("📋 Daftar Channel yang akan dibersihkan:")
        for ch in unique_channels:
            print(f" - {ch}")

        # Proses penghapusan
        for channel in unique_channels:
            await delete_messages_from_channel(app, channel)


if __name__ == "__main__":
    asyncio.run(main())
