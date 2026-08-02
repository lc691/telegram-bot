from pyrogram import Client
from pyrogram.types import Message


async def resolve_info_target(
    client: Client,
    message: Message,
):
    """
    Tentukan user target:
    - /info            → diri sendiri
    - /info USER_ID    → admin-only di grup
    - /info @username  → admin-only di grup
    """
    args = message.text.split(maxsplit=1)

    if len(args) == 1:
        return message.from_user

    target = args[1].strip()
    user = None

    if target.isdigit():
        user = await client.get_users(int(target))
    else:
        if target.startswith("@"):
            target = target[1:]
        user = await client.get_users(target)

    return user
