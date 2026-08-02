import json

from shared.utils.state_manager import (
    clear_admin_temp_state,
    get_admin_temp_state,
    set_admin_temp_state,
)
from configs.logging_setup import log


class UserRequestStateManager:
    def __init__(self, user_id: int, source_bot: str = "drac1n"):
        self.user_id = user_id
        self.prefix = f"{source_bot}_request"
        self._step_key = f"{self.prefix}_step"
        self._data_key = f"{self.prefix}_data"

    # Step FSM
    def set_step(self, step: str):
        set_admin_temp_state(self.user_id, self._step_key, step)
        log.debug(f"[UserFSM] Set step={step} untuk user_id={self.user_id}")

    def get_step(self) -> str | None:
        return get_admin_temp_state(self.user_id, self._step_key)

    def clear_step(self):
        clear_admin_temp_state(self.user_id, prefix=self._step_key)

    # Temp Data
    def set_data(self, data: dict):
        try:
            set_admin_temp_state(self.user_id, self._data_key, json.dumps(data))
        except Exception as e:
            log.error(f"[UserFSM] Gagal menyimpan data: {e}")

    def get_data(self) -> dict:
        raw = get_admin_temp_state(self.user_id, self._data_key)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}
        return {}

    def clear_data(self):
        clear_admin_temp_state(self.user_id, prefix=self._data_key)

    def clear_all(self):
        self.clear_step()
        self.clear_data()

    def is_active(self) -> bool:
        return self.get_step() is not None
