from pyrogram import Client
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied
from pyrogram.types import Message


async def resolve_info_target(
    client: Client,
    message: Message,
):
    """
    Resolve target user untuk command /info

    Support:
    - /info
    - /info @username
    - /info USER_ID
    - reply + /info
    """

    # ==========================================
    # Reply target
    # ==========================================
    if (
        message.reply_to_message
        and message.reply_to_message.from_user
    ):
        return message.reply_to_message.from_user

    # ==========================================
    # Command text
    # ==========================================
    text = message.text or ""

    args = text.split(maxsplit=1)

    # ==========================================
    # /info → diri sendiri
    # ==========================================
    if len(args) == 1:
        return message.from_user

    target = args[1].strip()

    if not target:
        return message.from_user

    try:

        # ==========================================
        # USER_ID
        # ==========================================
        if target.isdigit():
            return await client.get_users(
                int(target)
            )

        # ==========================================
        # USERNAME
        # ==========================================
        username = target.lstrip("@")

        return await client.get_users(username)

    except (
        PeerIdInvalid,
        UsernameNotOccupied,
        ValueError,
    ):
        return None

    except Exception:
        return None