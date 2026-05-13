import json

from common.utils.state_manager import (
    clear_admin_temp_state,
    get_admin_temp_state,
    set_admin_temp_state,
)
from configs.logging_setup import log


class UserSearchStateManager:
    def __init__(self, user_id: int, source_bot: str = "drac1n"):
        self.user_id = user_id
        self.prefix = f"{source_bot}_search"
        self._step_key = f"{self.prefix}_step"
        self._data_key = f"{self.prefix}_data"

    # FSM Step
    def set_step(self, step: str):
        set_admin_temp_state(self.user_id, self._step_key, step)
        log.debug(f"[SearchFSM] Set step={step} untuk user_id={self.user_id}")

    def get_step(self) -> str | None:
        return get_admin_temp_state(self.user_id, self._step_key)

    def clear_step(self):
        clear_admin_temp_state(self.user_id, prefix=self._step_key)

    # Data sementara
    def set_data(self, key: str, value):
        data = self.get_data()
        data[key] = value
        try:
            set_admin_temp_state(self.user_id, self._data_key, json.dumps(data))
        except Exception as e:
            log.error(f"[SearchFSM] Gagal simpan data: {e}", exc_info=True)

    def get_data(self, key: str = None):
        raw = get_admin_temp_state(self.user_id, self._data_key)
        if raw:
            try:
                data = json.loads(raw)
                return data if key is None else data.get(key)
            except json.JSONDecodeError:
                log.warning("[SearchFSM] Data tidak bisa di-decode.")
                return {} if key is None else None
        return {} if key is None else None

    def clear_data(self):
        clear_admin_temp_state(self.user_id, prefix=self._data_key)

    def clear_all(self):
        self.clear_step()
        self.clear_data()

    def is_active(self) -> bool:
        return self.get_step() is not None
