from pyrogram.types import Message

async def safe_edit(msg: Message, *args, **kwargs):
    try:
        return await msg.edit(*args, **kwargs)
    except Exception:
        return None
