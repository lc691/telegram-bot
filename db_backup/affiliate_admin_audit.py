from configs.logging_setup import log
from db.connect import get_db_cursor


def log_admin_action(
    admin_id: int,
    action: str,
    target_type: str,
    target_id: int,
    notes: str | None = None,
):
    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("""
                INSERT INTO affiliate_admin_audit_logs
                    (admin_id, action, target_type, target_id, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (admin_id, action, target_type, target_id, notes))
    except Exception as e:
        log.error(f"[ADMIN-AUDIT] Failed log: {e}", exc_info=True)
