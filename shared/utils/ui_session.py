import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from enum import Enum

from configs.logging_setup import log

# ============================================================
# ⚙️ Konfigurasi
# ============================================================

LOCK_TIMEOUT = timedelta(seconds=90)
CLEAN_INTERVAL = 60
BENCHMARK_INTERVAL = 60


# ============================================================
# 🧠 UI MODE (INI KUNCI)
# ============================================================

class UIMode(str, Enum):
    IDLE = "idle"
    STATUS = "status"
    REFERRAL = "referral"
    VIP = "vip"
    PAYMENT = "payment"


# user_id -> (mode, timestamp)
_active_ui_users: Dict[int, Tuple[UIMode, datetime]] = {}
_cleanup_task: Optional[asyncio.Task] = None


# ============================================================
# 🔒 Core UI State
# ============================================================

def mark_ui_active(user_id: int, mode: UIMode) -> None:
    _active_ui_users[user_id] = (mode, datetime.now())
    log.debug("[UI] Mark active user=%s mode=%s", user_id, mode)


def clear_ui_lock(user_id: int) -> None:
    if _active_ui_users.pop(user_id, None) is not None:
        log.debug("[UI] Clear lock user=%s", user_id)


def get_ui_mode(user_id: int) -> UIMode:
    data = _active_ui_users.get(user_id)
    if not data:
        return UIMode.IDLE

    mode, ts = data
    if datetime.now() - ts > LOCK_TIMEOUT:
        _active_ui_users.pop(user_id, None)
        log.debug("[UI] Auto-expire lock user=%s", user_id)
        return UIMode.IDLE

    return mode


def refresh_ui_activity(user_id: int) -> None:
    data = _active_ui_users.get(user_id)
    if data:
        mode, _ = data
        _active_ui_users[user_id] = (mode, datetime.now())
        log.debug("[UI] Refresh lock user=%s mode=%s", user_id, mode)


# ============================================================
# 🚧 Guard Logic (ANTI BENGONG)
# ============================================================

def block_if_active(user_id: int, incoming: UIMode) -> Optional[str]:
    """
    Tentukan apakah UI baru boleh dibuka.
    """
    current = get_ui_mode(user_id)

    # Tidak ada UI aktif
    if current == UIMode.IDLE:
        return None

    # STATUS & REFERRAL TIDAK PERNAH MEMBLOKIR
    if current in (UIMode.STATUS, UIMode.REFERRAL):
        return None

    # VIP aktif → hanya blok VIP & PAYMENT
    if current == UIMode.VIP:
        if incoming in (UIMode.VIP, UIMode.PAYMENT):
            return "⚠️ Selesaikan proses VIP dulu."
        return None

    # PAYMENT aktif → blok VIP
    if current == UIMode.PAYMENT:
        if incoming == UIMode.VIP:
            return "⚠️ Selesaikan pembayaran dulu."
        return None

    return None


# ============================================================
# 🔐 Wrapper yang dipakai handler
# ============================================================

async def with_ui_lock(
    user_id: int,
    coro_factory,
    *,
    mode: UIMode,
):
    """
    Jalankan coroutine dengan UI state-aware lock.

    - STATUS / REFERRAL: bebas
    - VIP: modal (tidak boleh dobel)
    - PAYMENT: modal (blok VIP)
    """
    if msg := block_if_active(user_id, mode):
        return msg

    mark_ui_active(user_id, mode)
    try:
        return await coro_factory()
    finally:
        # UI non-modal langsung dilepas
        if mode in (UIMode.STATUS, UIMode.REFERRAL):
            clear_ui_lock(user_id)


# ============================================================
# 🧹 Cleanup Loop
# ============================================================

async def _cleanup_loop() -> None:
    last_benchmark = datetime.now()

    try:
        while True:
            await asyncio.sleep(CLEAN_INTERVAL)
            now = datetime.now()

            expired = [
                uid for uid, (_, ts) in list(_active_ui_users.items())
                if now - ts > LOCK_TIMEOUT
            ]

            for uid in expired:
                _active_ui_users.pop(uid, None)
                log.debug("[UI] Auto-clear expired lock user=%s", uid)

            if (now - last_benchmark).total_seconds() >= BENCHMARK_INTERVAL:
                log.debug(
                    "[UI][BENCH] active=%s expired_cleared=%s",
                    len(_active_ui_users),
                    len(expired),
                )
                last_benchmark = now

    except asyncio.CancelledError:
        log.info("[UI] Cleanup loop cancelled")
        raise


def start_ui_cleanup_loop() -> None:
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        return
    _cleanup_task = asyncio.create_task(_cleanup_loop())
    log.info("[UI] Cleanup loop started")


def stop_ui_cleanup_loop() -> None:
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        _cleanup_task = None
        log.info("[UI] Cleanup loop stopped")
