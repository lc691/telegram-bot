from typing import Dict, Optional

from pyrogram import Client

from configs.logging_setup import log

# Registry internal
_bot_registry: Dict[str, Client] = {}


def register_bot(bot_key: str, client: Client):
    """
    Daftarkan bot dengan kunci unik.
    """
    if not bot_key:
        raise ValueError("bot_key tidak boleh kosong.")
    if not isinstance(client, Client):
        raise TypeError(f"client bukan instance pyrogram.Client: {type(client)}")

    if bot_key in _bot_registry:
        log.warning(f"[BOT-REGISTRY] ⚠️ Bot '{bot_key}' sudah terdaftar. Menimpa.")

    _bot_registry[bot_key] = client
    # log.info(f"[BOT-REGISTRY] ✅ Bot '{bot_key}' terdaftar: {client!r}")


def get_bot(bot_key: str) -> Optional[Client]:
    """
    Ambil bot dari registry.
    """
    bot = _bot_registry.get(bot_key)
    if not bot:
        log.debug(f"[BOT-REGISTRY] ❌ Bot '{bot_key}' tidak ditemukan.")
    return bot


def unregister_bot(bot_key: str) -> bool:
    """
    Lepas bot dari registry.
    """
    return _bot_registry.pop(bot_key, None) is not None


def all_registered_bots() -> Dict[str, Client]:
    """
    Kembalikan salinan seluruh bot terdaftar.
    """
    return dict(_bot_registry)


def get_main_bot() -> Optional[Client]:
    """
    Ambil bot utama (default 'drac1n')
    """
    return _bot_registry.get("drac1n")
