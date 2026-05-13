from ....config.settings import ALLOWED_CHAT_IDS
from ..middlewares.rate_limit import is_rate_limited
from ....infrastructure.telegram.permissions import is_admin
from configs.logging_setup import log


async def allow_image_match(client, message) -> bool:
    """
    Guard image match.

    True  → boleh lanjut image match
    False → stop flow
    """

    chat_id = message.chat.id
    user = message.from_user

    # ==================================================
    # 1️⃣ ALLOWED CHAT CHECK
    # ==================================================
    if chat_id not in ALLOWED_CHAT_IDS:
        log.info(
            "[IMG_MATCH][GUARD] blocked_chat chat=%s",
            chat_id,
        )
        return False

    # ==================================================
    # 2️⃣ USER EXISTENCE CHECK
    # ==================================================
    if not user:
        log.info(
            "[IMG_MATCH][GUARD] no_user chat=%s",
            chat_id,
        )
        return False

    user_id = user.id

    # ==================================================
    # 3️⃣ ADMIN BLOCK
    # ==================================================
    if await is_admin(client, chat_id, user_id):
        log.info(
            "[IMG_MATCH][GUARD] admin_block user=%s chat=%s",
            user_id,
            chat_id,
        )
        return False

    # ==================================================
    # 4️⃣ RATE LIMIT
    # ==================================================
    if is_rate_limited(user_id):
        log.info(
            "[IMG_MATCH][GUARD] rate_limited user=%s",
            user_id,
        )
        await message.reply("⚠️ Terlalu banyak request. Tunggu sebentar ⏳")
        return False

    log.info(
        "[IMG_MATCH][GUARD] allowed user=%s chat=%s",
        user_id,
        chat_id,
    )
    return True
