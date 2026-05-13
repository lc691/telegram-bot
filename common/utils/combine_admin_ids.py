from config import get_env
from configs.logging_setup import log
from db.admin.admin_utils import load_admin_ids
from db.models import ensure_admins_table


def load_admin_ids_from_env():
    try:
        env_admins = get_env("ADMIN_IDS")
        parsed = [int(x.strip()) for x in env_admins.split(",") if x.strip().isdigit()]
        log.info(f"✅ Admin IDs dari ENV: {parsed}")
        return set(parsed)
    except Exception as e:
        log.warning(f"⚠️ Gagal parsing ADMIN_IDS dari ENV: {e}")
        return set()


def combine_admin_ids():
    ensure_admins_table()
    db_admins = load_admin_ids()  # harusnya set(int)
    env_admins = load_admin_ids_from_env()
    combined = db_admins.union(env_admins)
    log.info(f"Gabungan ADMIN_IDS dari DB dan ENV: {combined}")
    for admin_id in combined:
        log.info(f"Tipe admin_id: {admin_id} -> {type(admin_id)}")
    return combined
