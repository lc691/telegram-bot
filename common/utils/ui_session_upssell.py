# common/utils/ui_session.py
import time

from configs.logging_setup import log

_active_ui_users: dict[int, float] = {}
_UPSELL_SHOWN: dict[tuple[int, str], float] = {}
_UPSELL_CONTEXT: dict[int, tuple[str, str]] = {}
_UPSELL_TTL = 300  # 5 menit



# ---------- UPSELL SESSION ----------
def set_upsell_context(user_id: int, source: str, target: str):
    _UPSELL_CONTEXT[user_id] = (source, target)

def get_upsell_context(user_id: int):
    return _UPSELL_CONTEXT.get(user_id)

def pop_upsell_context(user_id: int):
    return _UPSELL_CONTEXT.pop(user_id, None)

def mark_upsell_shown(user_id: int, paket: str):
    _UPSELL_SHOWN[(user_id, paket)] = time.time()

def has_shown_upsell(user_id: int, paket: str) -> bool:
    ts = _UPSELL_SHOWN.get((user_id, paket))
    if not ts:
        return False
    if time.time() - ts > _UPSELL_TTL:
        _UPSELL_SHOWN.pop((user_id, paket), None)
        return False
    return True


# ---------- CLEANUP ----------
def clear_user_session(user_id: int):
    ui_cleared = _active_ui_users.pop(user_id, None) is not None
    ctx_cleared = _UPSELL_CONTEXT.pop(user_id, None) is not None

    upsell_removed = 0
    for key in list(_UPSELL_SHOWN):
        if key[0] == user_id:
            _UPSELL_SHOWN.pop(key, None)
            upsell_removed += 1

    if ui_cleared or ctx_cleared or upsell_removed:
        log.debug(
            "[UI] Clear user session: user_id=%s ui=%s ctx=%s upsell_removed=%s",
            user_id, ui_cleared, ctx_cleared, upsell_removed
        )
