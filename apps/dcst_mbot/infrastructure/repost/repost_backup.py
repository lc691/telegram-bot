from typing import Union, List
from pyrogram import Client
from configs.logging_setup import log


async def backup_message(
    client: Client,
    *,
    from_chat_id: int,
    message_id: int,
    backup_channel: Union[str, int, List[Union[str, int]]],
):
    """
    Menyalin pesan ke satu atau beberapa channel backup.

    Args:
        client (Client): Instance Pyrogram Client.
        from_chat_id (int): ID chat sumber.
        message_id (int): ID pesan yang akan disalin.
        backup_channel (str | int | list): Username atau ID channel tujuan.
    """

    # Normalisasi menjadi list
    if not backup_channel:
        log.warning("[REPOST] Tidak ada backup channel yang dikonfigurasi.")
        return

    if not isinstance(backup_channel, (list, tuple, set)):
        backup_channels = [backup_channel]
    else:
        backup_channels = backup_channel

    # Proses setiap channel
    for channel in backup_channels:
        try:
            # Bersihkan format channel
            if isinstance(channel, str):
                channel = channel.strip()
                if channel.lstrip("-").isdigit():
                    channel = int(channel)

            await client.copy_message(
                chat_id=channel,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )

            log.info(f"[REPOST] Backup sukses ke {channel}")

        except Exception as e:
            log.error(f"[REPOST] Gagal backup ke {channel}: {e}")
