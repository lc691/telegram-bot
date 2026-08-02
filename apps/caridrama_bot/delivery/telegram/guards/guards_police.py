from ....config.settings import ALLOWED_CHAT_IDS
from ..middlewares.rate_limit import is_rate_limited
from ....infrastructure.telegram.permissions import is_admin

async def allow_groups_chats(client, message) -> bool:
    if message.chat.id not in ALLOWED_CHAT_IDS:
        return False

    if not message.from_user:
        return False

    if await is_admin(client, message.chat.id, message.from_user.id):
        return False

    if is_rate_limited(message.from_user.id):
        await message.reply("⚠️ Terlalu banyak request. Tunggu sebentar ⏳")
        return False

    return True
