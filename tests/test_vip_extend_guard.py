from datetime import datetime, timedelta

from configs.timezone import JAKARTA_TZ
from database.vip_users.vip_service import safe_insert_vip_user


def test_new_vip(fake_db):
    result = safe_insert_vip_user(
        user_id=1,
        username="test",
        paket="basic",
        durasi_hari=3
    )

    assert result["success"] is True
    assert result["is_new"] is True
    assert result["is_extend"] is False
    assert result["mode"] == "baru"
    assert result["durasi_hari"] == 3
    assert result["user_id"] == 1


def test_extend_vip(fake_db):
    now = datetime.now(JAKARTA_TZ)

    fake_db.active_vip = {
        "start_date": now - timedelta(days=2),
        "end_date": now + timedelta(days=5)
    }

    result = safe_insert_vip_user(
        user_id=2,
        username="tester",
        paket="pro",
        durasi_hari=7
    )

    assert result["success"] is True
    assert result["is_extend"] is True
    assert result["mode"] == "extend"
    assert result["expired_at"] > result["expired_lama"]



def test_reset_expired_vip(fake_db):
    now = datetime.now(JAKARTA_TZ)

    # Simulasikan VIP sudah expired
    fake_db.active_vip = {
        "start_date": now - timedelta(days=10),
        "end_date": now - timedelta(days=1)
    }

    result = safe_insert_vip_user(
        user_id=3,
        username="reset",
        paket="premium",
        durasi_hari=5
    )

    assert result["success"] is True
    assert result["is_extend"] is False
    assert result["mode"] == "baru"
    assert result["expired_at"] > now
