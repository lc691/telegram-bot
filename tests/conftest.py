from datetime import datetime

import pytest

from configs.timezone import JAKARTA_TZ


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.storage = {
            "users": set(),
            "vip_users": {},
            "vip_logs": [],
        }
        self.active_vip = None
        self.return_next = None

    def execute(self, q, params=None):
        self.return_next = None   # 🔥 WAJIB RESET
        self.queries.append((q, params))

        # === USERS ===
        if "FROM users WHERE user_id" in q:
            self.return_next = (1,) if params[0] in self.storage["users"] else None

        if "INSERT INTO users" in q:
            self.storage["users"].add(params[0])
            self.return_next = None

        # === VIP USERS (select active) ===
        if "FROM vip_users" in q:
            now = datetime.now(JAKARTA_TZ)

            # tidak ada vip sama sekali
            if not self.active_vip:
                self.return_next = None
                return

            # kalau expired → anggap tidak aktif
            if self.active_vip["end_date"] <= now:
                self.return_next = None
                return

            # hanya kalau masih aktif → return
            self.return_next = self.active_vip
            return

        # === VIP UPSERT ===
        if "INSERT INTO vip_users" in q:
            self.storage["vip_users"][params[0]] = params
            self.return_next = None

        # === VIP LOGS ===
        if "INSERT INTO vip_logs" in q:
            self.storage["vip_logs"].append(1)
            self.return_next = {"id": 1}

        if "SELECT COUNT(*) FROM vip_logs" in q:
            self.return_next = {"count": len(self.storage["vip_logs"])}

    def fetchone(self):
        return self.return_next


class FakeConn:
    def commit(self):
        return True


@pytest.fixture
def fake_db(monkeypatch):
    cur = FakeCursor()
    conn = FakeConn()

    class Ctx:
        def __enter__(self):
            return cur, conn
        def __exit__(self, exc_type, exc, tb):
            pass

    from database.vip_users import vip_activation
    monkeypatch.setattr(vip_activation, "get_dict_cursor", lambda: Ctx())

    return cur
