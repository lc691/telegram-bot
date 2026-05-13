from pyrogram import Client

from bots.base_handler_registry import BaseHandlerRegistry
from configs.logging_setup import log


HANDLER_NAMESPACE = "caridrama_bot"


def register_cari_drama_handlers(app: Client, admin_cache) -> None:
    """
    Register semua handler bot Caridrama.

    Kontrak penting:
    - WAJIB cepat
    - TIDAK BOLEH blocking
    - TIDAK BOLEH ada IO berat (DB / ML / Network)
    """

    # Kontrak BotManager (tidak dipakai langsung di sini)
    _ = admin_cache

    registry = BaseHandlerRegistry(HANDLER_NAMESPACE)

    # --------------------------------------------------
    # Lazy imports (anti heavy startup)
    # --------------------------------------------------
    from ..callbacks.request_show_callback import (
        register_request_show_callback,
    )

    from ..delivery.telegram.image_match.image_match_callback_handler import (
        register_image_match_callback_handler,
    )
    from ..delivery.telegram.image_match.image_match_handler import (
        register_image_match_handler,
    )

    from ..delivery.telegram.inline_search.inline_search_handler import (
        register_inline_search,
    )
    from ..delivery.telegram.group_search.group_search_handler import (
        register_response_handler,
    )
    from ..delivery.telegram.user.start_handler import (
        register_start_handler,
    )
    from ..delivery.telegram.user.welcome_handler import (
        register_welcome_handler,
    )

    # --------------------------------------------------
    # Register handlers (user flow order)
    # --------------------------------------------------
    registry.add("start", register_start_handler)
    registry.add("welcome", register_welcome_handler)

    registry.add("inline_search", register_inline_search)
    registry.add("response", register_response_handler)

    registry.add("image_match", register_image_match_handler)
    registry.add(
        "image_match_callback",
        register_image_match_callback_handler,
    )

    registry.add("request", register_request_show_callback)

    # --------------------------------------------------
    # Finalize registration
    # --------------------------------------------------
    registry.register_all(app)

    log.info(
        "[%s] Semua handler berhasil didaftarkan",
        HANDLER_NAMESPACE,
    )
