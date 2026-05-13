import json
import time

from common.utils.state_manager import (
    clear_admin_temp_state,
    clear_state,
    get_admin_temp_state,
    set_admin_temp_state,
)
from configs.logging_setup import log


class AdminStateManager:
    def __init__(self, admin_id: int, source_bot: str = "drac1n"):
        self.admin_id = admin_id
        self.source_bot = source_bot
        self._temp = {}

    def _prefixed(self, key: str) -> str:
        return f"{self.source_bot}_{key}"

    def log(self, msg: str, level="info"):
        logging_method = getattr(log, level, log.info)
        logging_method(
            f"[ADMIN_STATE][{level.upper()}][{self.admin_id}@{self.source_bot}] {msg}"
        )

    def load(self):
        try:
            self._temp = {
                "regular_step": get_admin_temp_state(
                    self.admin_id, self._prefixed("regular_step")
                ),
                "vip_add_step": get_admin_temp_state(
                    self.admin_id, self._prefixed("vip_add_step")
                ),
                "vip_delete_step": get_admin_temp_state(
                    self.admin_id, self._prefixed("vip_delete_step")
                ),
                "expires_at": get_admin_temp_state(
                    self.admin_id, self._prefixed("expires_at")
                ),
                "new_admin": get_admin_temp_state(
                    self.admin_id, self._prefixed("new_admin")
                ),
            }
            self.log(f"Berhasil memuat state: {self._temp}")
        except Exception as e:
            self.log(f"Gagal load state: {e}", level="error")

    def get_temp(self, key: str, default=None):
        if key in self._temp:
            return self._temp[key]
        try:
            value = get_admin_temp_state(self.admin_id, self._prefixed(key))
            self._temp[key] = value
            return value if value is not None else default
        except Exception:
            return default

    def set_temp(self, key: str, value: str):
        try:
            full_key = self._prefixed(key)
            set_admin_temp_state(self.admin_id, full_key, value)
            self._temp[key] = value
            self.log(f"Temp set: {key} = {value}")
        except Exception as e:
            self.log(f"Gagal set_temp {key}: {e}", level="error")

    def mark_expiry(self, seconds: int = 300):
        ttl = str(int(time.time()) + seconds)
        self.set_temp("expires_at", ttl)
        self.log(f"Menandai expiry dalam {seconds} detik (timestamp: {ttl})")

    def is_expired(self):
        try:
            self.load()
            expiry_str = self.get_temp("expires_at")
            if not expiry_str:
                return False
            expiry_ts = int(expiry_str)
            expired = time.time() > expiry_ts
            self.log(
                f"Cek expired: now={int(time.time())}, expiry={expiry_ts}, result={expired}"
            )
            return expired
        except Exception as e:
            self.log(f"Gagal cek expired: {e}", level="error")
            return False

    def current_step(self):
        self.load()
        self.log(f"Langkah saat ini: {self._temp}")
        return {
            "regular": self.get_temp("regular_step"),
            "vip_add": self.get_temp("vip_add_step"),
            "vip_delete": self.get_temp("vip_delete_step"),
        }

    def clear(self):
        try:
            clear_state(self.admin_id)
            clear_admin_temp_state(self.admin_id, prefix=f"{self.source_bot}_")
            self._temp = {}
            self.log("Semua state berhasil dihapus.")
        except Exception as e:
            self.log(f"Gagal menghapus state: {e}", level="error")

    def set_step(self, step_type: str, value: str):
        self.set_temp(step_type, value)

    def get_step(self, step_type: str) -> str | None:
        return self.get_temp(step_type)

    def has_active_step(self) -> bool:
        self.load()
        return any(
            [
                self.get_temp("regular_step"),
                self.get_temp("vip_add_step"),
                self.get_temp("vip_delete_step"),
            ]
        )

    def set_temp_json(self, key: str, value: dict):
        try:
            self.set_temp(key, json.dumps(value))
        except Exception as e:
            self.log(f"Gagal set_temp_json {key}: {e}", level="error")

    def get_temp_json(self, key: str, default=None):
        raw = self.get_temp(key)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            self.log(f"Gagal decode JSON dari temp key '{key}': {e}", level="warning")
            return default
