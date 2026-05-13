import json

from common.bot_utils import get_clean_bot_key
from common.utils.state_manager import (
    clear_admin_temp_state,
    get_admin_temp_state,
    set_admin_temp_state,
)
from configs.logging_setup import log


class VipStateManager:
    def __init__(self, user_id: int, source_bot: str = "drac1n"):
        self.user_id = user_id
        try:
            # Step 1: safely parse if JSON string
            if isinstance(source_bot, str) and source_bot.startswith('"'):
                source_bot = json.loads(source_bot)
        except Exception:
            pass  # fallback ke raw string jika parsing gagal

        self.source_bot = get_clean_bot_key(source_bot)
        self._prefix = f"{self.source_bot}_vip"
        self._keys = {
            "add": f"{self._prefix}_add_step",
            "extend": f"{self._prefix}_extend_step",
            "delete": f"{self._prefix}_delete_step",
            "reset": f"{self._prefix}_reset_step",
            "temp": f"{self._prefix}_temp_data",
        }

    # ========== Step Management ==========
    def _set_exclusive_step(self, active_key: str, step: str):
        for key in ["add", "extend", "delete", "reset"]:
            set_admin_temp_state(
                self.user_id, self._keys[key], step if key == active_key else None
            )

    def set_vip_add_step(self, step: str):
        log.info(f"[FSM DEBUG] set_vip_add_step: user_id={self.user_id}, step={step}")
        self._set_exclusive_step("add", step)

    def set_vip_extend_step(self, step: str):
        log.info(
            f"[FSM DEBUG] set_vip_extend_step: user_id={self.user_id}, step={step}"
        )
        self._set_exclusive_step("extend", step)

    def set_vip_delete_step(self, step: str):
        self._set_exclusive_step("delete", step)
        log.info(
            f"[FSM DEBUG] set_vip_delete_step: user_id={self.user_id}, step={step}"
        )
        # Verifikasi langsung
        check = get_admin_temp_state(self.user_id, self._keys["delete"])
        log.debug(
            f"[FSM DEBUG] Verifikasi penyimpanan delete_step: {check} (expected: {step})"
        )

    def set_vip_reset_step(self, step: str):
        self._set_exclusive_step("reset", step)

    def get_vip_add_step(self):
        step = get_admin_temp_state(self.user_id, self._keys["add"])
        log.info(f"[FSM DEBUG] get_vip_add_step: user_id={self.user_id}, step={step}")
        return step

    def get_vip_extend_step(self):
        step = get_admin_temp_state(self.user_id, self._keys["extend"])
        log.info(
            f"[FSM DEBUG] get_vip_extend_step: user_id={self.user_id}, step={step}"
        )
        return step

    def get_vip_delete_step(self):
        return get_admin_temp_state(self.user_id, self._keys["delete"])

    def get_vip_reset_step(self):
        return get_admin_temp_state(self.user_id, self._keys["reset"])

    def is_active(self):
        return any(
            [
                self.get_vip_add_step(),
                self.get_vip_extend_step(),
                self.get_vip_delete_step(),
                self.get_vip_reset_step(),
            ]
        )

    def has_conflict(self) -> bool:
        return self.is_active()

    def clear(self):
        clear_admin_temp_state(self.user_id, prefix=self._prefix)

    def clear_temp(self, key: str):
        full_key = f"{self._keys['temp']}:{key}"
        clear_admin_temp_state(self.user_id, prefix=full_key)

    def get_bot_client(self):
        try:
            from bots import get_bot

            return get_bot(self.source_bot)
        except Exception as e:
            log.warning(f"[VipStateManager] Gagal ambil bot '{self.source_bot}': {e}")
            return None

    # ========== Temp Data ==========
    def set_temp(self, key: str, value):
        full_key = f"{self._keys['temp']}:{key}"
        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError) as e:
            log.warning(f"Failed to serialize temp data for key '{key}': {e}")
            json_value = str(value)
        set_admin_temp_state(self.user_id, full_key, json_value)

    def get_temp(self, key: str):
        full_key = f"{self._keys['temp']}:{key}"
        val = get_admin_temp_state(self.user_id, full_key)
        if val is None or val == "null":
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val

    def remove_temp(self, key: str):
        full_key = f"{self._keys['temp']}:{key}"
        clear_admin_temp_state(self.user_id, prefix=full_key)

    def get_source_bot(self):
        return self.source_bot

    def print_status(self):
        print(f"📍 FSM Status user_id={self.user_id} (bot={self.source_bot}):")
        for label in ["add", "extend", "delete", "reset"]:
            step = get_admin_temp_state(self.user_id, self._keys[label])
            if step:
                print(f"  STEP {label.upper()}: {step}")
        print("  Temp Data:")
        try:
            from common.utils.state_manager import get_all_admin_temp_states

            temp_data = get_all_admin_temp_states(
                self.user_id, prefix=self._keys["temp"] + ":"
            )
            if temp_data:
                for k, v in temp_data.items():
                    key_short = k[len(self._keys["temp"]) + 1 :]
                    print(f"    {key_short}: {v}")
            else:
                print("    (no temp data)")
        except ImportError:
            print("    (Cannot list temp data: helper not implemented)")
