from configs.logging_setup import log

from ...services.channel_repository import load_required_channels
from .checks import check_required_channels
from .messages import send_join_instructions


async def check_channel_join(
    app,
    user_id: int,
    access_hash: str,
    message,
) -> bool:
    """
    Validates whether user has joined all required channels.
    Returns True if all joined, False otherwise.
    """

    try:
        # 🔹 FIX: wajib await + kirim app
        required_channels = await load_required_channels(app)

        if not required_channels:
            log.warning(
                "[JOIN_CHECK] no required channels configured bot=%s",
                app.me.username,
            )
            return True  # fail-open

        not_joined = await check_required_channels(
            app,
            user_id,
            required_channels,
        )

        if not isinstance(not_joined, (list, tuple, set)):
            log.error(
                "[JOIN_CHECK] invalid return type user_id=%s type=%s",
                user_id,
                type(not_joined),
            )
            return True  # fail-open

        if not_joined:
            log.info(
                "[JOIN_CHECK] user_id=%s not joined count=%s bot=%s",
                user_id,
                len(not_joined),
                app.me.username,
            )

            await send_join_instructions(
                app,
                message,
                not_joined,
                access_hash,
            )
            return False

        return True

    except Exception:
        log.exception(
            "[JOIN_CHECK] unexpected error user_id=%s bot=%s",
            user_id,
            getattr(app.me, "username", None),
        )
        raise
