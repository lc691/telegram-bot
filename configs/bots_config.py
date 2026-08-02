from typing import Any, Callable, Dict, TypedDict

from apps.caridrama_bot.register.register_cari import (
    register_cari_drama_handlers,
)
from apps.dcst_mbot.register.register_dcst import register_dcst_handlers
from apps.drac1n_bot.register.register_drac1n import register_drac1n_handlers
from apps.dramaglow_bot.register.register_glow import register_glow_handlers
from infrastructure.bootstrap.bots.factory import (
    create_app,
    create_app_glow,
    create_caridrama_app,
    create_dcst_app,
)


# =====================================================
# === BOT CONFIG SCHEMA ===============================
# =====================================================
class BotConfigEntry(TypedDict):
    bot_key: str
    factory: Callable[[Any], Any]  # menerima db pool
    register_handlers: Callable[..., None]
    description: str


# =====================================================
# === BOT CONFIG REGISTRY =============================
# =====================================================
BOT_CONFIG: Dict[str, BotConfigEntry] = {
    "drac1n_bot": {
        "bot_key": "drac1n",
        "factory": lambda pool: create_app(pool),
        "register_handlers": register_drac1n_handlers,
        "description": "Bot utama drac1n — donasi, VIP, user tools",
    },
    "dramaglow_bot": {
        "bot_key": "glow",
        "factory": lambda pool: create_app_glow(pool),
        "register_handlers": register_glow_handlers,
        "description": "Bot utama glow — donasi, VIP, user tools",
    },
    "dcst_bot": {
        "bot_key": "kelolain",
        "factory": lambda pool: create_dcst_app(pool),
        "register_handlers": register_dcst_handlers,
        "description": "Bot kelola posting — repost, forward, dashboard",
    },
    "caridrama_bot": {
        "bot_key": "caridrama",
        "factory": lambda pool: create_caridrama_app(pool),
        "register_handlers": register_cari_drama_handlers,
        "description": "Bot cari drama — search inline query shows",
    },
}


# =====================================================
# === CONFIG VALIDATOR ================================
# =====================================================
def validate_bot_config() -> None:
    required_keys = {
        "bot_key",
        "factory",
        "register_handlers",
        "description",
    }

    for bot_name, config in BOT_CONFIG.items():
        missing = required_keys - config.keys()
        if missing:
            raise ValueError(
                f"❌ BOT_CONFIG '{bot_name}' kekurangan kunci: "
                f"{', '.join(sorted(missing))}"
            )

        if not callable(config["factory"]):
            raise TypeError(f"❌ factory untuk '{bot_name}' harus callable.")

        if not callable(config["register_handlers"]):
            raise TypeError(f"❌ register_handlers untuk '{bot_name}' harus callable.")


# Validasi saat modul diload
validate_bot_config()
