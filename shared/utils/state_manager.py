import json
from typing import Any, Optional
from configs.logging_setup import log
from database.connection import get_db_cursor

# =====================================================
# IN-MEMORY STATE (HATI-HATI: BELUM DI-LOCK)
# =====================================================
adding_channel_users: set[int] = set()
search_prompts: dict[int, Any] = {}

# =====================================================
# STEP KEYS (FSM DOMAIN)
# =====================================================
STEP_KEYS = {
    "regular_step",
    "vip_add_step",
    "vip_delete_step",
    "feedback_step",
}

# =====================================================
# NORMALIZATION
# =====================================================
def normalize_step(value: Any) -> Optional[str]:
    if isinstance(value, (tuple, list)):
        value = value[0] if value else None
    return str(value) if value is not None else None


def normalize_raw_value(value: Any, key: str | None = None) -> Any:
    if isinstance(value, (tuple, list)):
        value = value[0] if value else None

    if value in (None, "", "null", "None"):
        return None

    # STEP DOMAIN
    if key in STEP_KEYS:
        return str(value)

    # DATA DOMAIN
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value

    return value


# =====================================================
# MAIN STATE (HARD PERSISTED FSM STORAGE)
# =====================================================
def set_admin_temp_state(admin_id: int, key: str, value: Any) -> None:
    try:
        # STEP DOMAIN
        if key in STEP_KEYS:
            value = normalize_step(value)

        # DATA DOMAIN
        else:
            if isinstance(value, (tuple, list)):
                value = value[0] if value else None

            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)

        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO admin_temp_state (admin_id, key, value)
                VALUES (%s, %s, %s)
                ON CONFLICT (admin_id, key) DO UPDATE
                SET value = EXCLUDED.value
                """,
                (admin_id, key, value),
            )
            conn.commit()

        log.info("[STATE] SET admin=%s key=%s value=%s", admin_id, key, value)

    except Exception as e:
        log.error(
            "[STATE] SET FAIL admin=%s key=%s err=%s",
            admin_id,
            key,
            e,
            exc_info=True,
        )


def get_admin_temp_state(admin_id: int, key: str, default=None):
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT value FROM admin_temp_state
                WHERE admin_id = %s AND key = %s
                """,
                (admin_id, key),
            )

            row = cursor.fetchone()
            if not row:
                return default

            raw_val = row[0]
            val = normalize_raw_value(raw_val, key)

            if val is None:
                return default

            return val

    except Exception as e:
        log.error(
            "[STATE] GET FAIL admin=%s key=%s err=%s",
            admin_id,
            key,
            e,
            exc_info=True,
        )
        return default


# =====================================================
# CLEAR STATE
# =====================================================
def clear_admin_temp_state(admin_id: int, prefix: str | None = None) -> None:
    try:
        with get_db_cursor() as (cursor, conn):
            if prefix:
                cursor.execute(
                    """
                    DELETE FROM admin_temp_state
                    WHERE admin_id = %s AND key LIKE %s
                    """,
                    (admin_id, f"{prefix}%"),
                )
            else:
                cursor.execute(
                    "DELETE FROM admin_temp_state WHERE admin_id = %s",
                    (admin_id,),
                )

            conn.commit()

        log.info("[STATE] CLEAR admin=%s prefix=%s", admin_id, prefix)

    except Exception as e:
        log.error(
            "[STATE] CLEAR FAIL admin=%s prefix=%s err=%s",
            admin_id,
            prefix,
            e,
            exc_info=True,
        )


def clear_state(admin_id: int) -> None:
    clear_admin_temp_state(admin_id)


# =====================================================
# BULK STATE INSPECTION
# =====================================================
def get_all_admin_temp_states(admin_id: int) -> dict:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT key, value FROM admin_temp_state WHERE admin_id = %s",
                (admin_id,),
            )
            rows = cursor.fetchall()

        return {k: v for k, v in rows} if rows else {}

    except Exception as e:
        log.error("[STATE] BULK GET FAIL admin=%s err=%s", admin_id, e)
        return {}


# =====================================================
# DEBUG DUMP
# =====================================================
def print_admin_states(admin_id: int, prefix_filter: str | None = None):
    try:
        with get_db_cursor() as (cursor, _):
            if prefix_filter:
                cursor.execute(
                    """
                    SELECT key, value FROM admin_temp_state
                    WHERE admin_id = %s AND key LIKE %s
                    ORDER BY key
                    """,
                    (admin_id, f"{prefix_filter}%"),
                )
            else:
                cursor.execute(
                    """
                    SELECT key, value FROM admin_temp_state
                    WHERE admin_id = %s
                    ORDER BY key
                    """,
                    (admin_id,),
                )

            rows = cursor.fetchall()

        if not rows:
            print(f"Tidak ada state untuk admin_id={admin_id}")
            return

        print(f"\n🧠 STATE DUMP admin_id={admin_id}")

        for k, v in rows:
            try:
                v = json.loads(v)
            except Exception:
                pass
            print(f"{k}: {v}")

    except Exception as e:
        log.error("[DEBUG STATE DUMP FAIL] admin=%s err=%s", admin_id, e)
