import json
import time
from typing import Optional, Dict, Any
from configs.logging_setup import log

from .state_manager import (
    clear_admin_temp_state,
    clear_state,
    get_admin_temp_state,
    set_admin_temp_state,
)

# =====================================================
# FSM TRANSITION MAP
# =====================================================
FEEDBACK_FSM: Dict[Optional[str], list[str]] = {
    None: ["request_drama", "report", "feature", "rating"],
    "request_drama": [],
    "report": [],
    "feature": [],
    "rating": [],
}


def can_transition(current: Optional[str], next_state: str) -> bool:
    """
    Allow:
    - first entry (None → state)
    - idempotent (state → same state)
    - valid transitions from map
    """
    if current == next_state:
        return True

    allowed = FEEDBACK_FSM.get(current, [])
    return next_state in allowed


# =====================================================
# STATE MANAGER
# =====================================================
class AdminStateManager:
    """
    FSM-aware state wrapper:
    - deterministic state transition
    - no hidden mutation
    - strict step handling
    """

    # STEP TYPES
    REGULAR_STEP = "regular_step"
    VIP_ADD_STEP = "vip_add_step"
    VIP_DELETE_STEP = "vip_delete_step"
    FEEDBACK_STEP = "feedback_step"

    # FEEDBACK STATES
    FEEDBACK_REQUEST_DRAMA = "request_drama"
    FEEDBACK_REPORT = "report"
    FEEDBACK_FEATURE = "feature"
    FEEDBACK_RATING = "rating"

    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    # =====================================================
    # KEY HANDLING (SINGLE SOURCE OF TRUTH)
    # =====================================================
    def _key(self, key: str) -> str:
        return key

    # =====================================================
    # RAW GET/SET
    # =====================================================
    def get_temp(self, key: str, default=None):
        value = get_admin_temp_state(self.admin_id, self._key(key))

        if value in (None, "", "null"):
            return default

        return value

    def set_temp(self, key: str, value: Any):
        set_admin_temp_state(self.admin_id, self._key(key), value)

        log.info(
            "[STATE] user=%s key=%s value=%s",
            self.admin_id,
            key,
            value,
        )

    # =====================================================
    # STEP FSM API
    # =====================================================
    def set_step(self, step_type: str, value: str) -> bool:
        current = self.get_step(step_type)

        if not can_transition(current, value):
            log.warning(
                "[FSM BLOCKED] admin=%s step=%s -> %s",
                self.admin_id,
                current,
                value,
            )
            return False

        self.set_temp(step_type, value)
        return True

    def get_step(self, step_type: str):
        return self.get_temp(step_type)

    def get_step_strict(self, step_type: str):
        value = self.get_temp(step_type)

        if isinstance(value, (tuple, list)):
            value = value[0]

        return str(value) if value else None

    # =====================================================
    # CLEAR STATE
    # =====================================================
    def clear(self, scope: Optional[str] = None):
        if scope:
            clear_admin_temp_state(self.admin_id, prefix=scope)
        else:
            clear_state(self.admin_id)

        log.info("[STATE] cleared user=%s scope=%s", self.admin_id, scope)

    # =====================================================
    # EXPIRY CONTROL
    # =====================================================
    def mark_expiry(self, seconds: int = 300):
        self.set_temp("expires_at", str(int(time.time()) + seconds))

    def is_expired(self) -> bool:
        val = self.get_temp("expires_at")

        if not val:
            return False

        try:
            return time.time() > int(val)
        except (ValueError, TypeError):
            return False

    # =====================================================
    # INSPECTION
    # =====================================================
    def current_step(self):
        return {
            "regular": self.get_temp(self.REGULAR_STEP),
            "vip_add": self.get_temp(self.VIP_ADD_STEP),
            "vip_delete": self.get_temp(self.VIP_DELETE_STEP),
            "feedback": self.get_temp(self.FEEDBACK_STEP),
        }

    def has_active_step(self) -> bool:
        return any(
            self.get_step(step) is not None
            for step in [
                self.REGULAR_STEP,
                self.VIP_ADD_STEP,
                self.VIP_DELETE_STEP,
                self.FEEDBACK_STEP,
            ]
        )

    # =====================================================
    # JSON HELPERS
    # =====================================================
    def set_temp_json(self, key: str, value: dict):
        self.set_temp(key, json.dumps(value, ensure_ascii=False))

    def get_temp_json(self, key: str, default=None):
        raw = self.get_temp(key)

        if raw in (None, "", "null"):
            return default

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return default