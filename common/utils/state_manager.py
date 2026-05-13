import json

from configs.logging_setup import log
from db.connect import get_db_cursor

# Set ini menyimpan user yang sedang dalam proses input channel
adding_channel_users = set()
search_prompts = {}

# ============================================ #
# === STATE: ADD, DELETE, UPDATE, VIEW ADMIN === #
# ============================================ #


def set_state(admin_id: int, value: dict) -> None:
    val_str = json.dumps(value)
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO admin_state(admin_id, step)
                VALUES (%s, %s)
                ON CONFLICT (admin_id) DO UPDATE
                SET step = EXCLUDED.step
                """,
                (admin_id, val_str),
            )
            conn.commit()
            log.info(f"[STATE] set_state berhasil untuk admin_id={admin_id}")
    except Exception as e:
        log.error(f"Gagal set_state untuk admin_id {admin_id}: {e}", exc_info=True)
        raise


def get_state(admin_id: int) -> dict | None:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT step FROM admin_state WHERE admin_id = %s", (admin_id,)
            )
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    log.error(f"Data state JSON rusak untuk admin_id {admin_id}")
                    return None
            return None
    except Exception as e:
        log.error(f"Gagal get_state untuk admin_id {admin_id}: {e}", exc_info=True)
        return None


def clear_state(admin_id: int) -> None:
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute("DELETE FROM admin_state WHERE admin_id = %s", (admin_id,))
            conn.commit()
            log.info(f"[STATE] clear_state berhasil untuk admin_id={admin_id}")
    except Exception as e:
        log.error(f"Gagal clear_state untuk admin_id {admin_id}: {e}", exc_info=True)
        raise


def has_state(admin_id: int) -> bool:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("SELECT 1 FROM admin_state WHERE admin_id = %s", (admin_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        log.error(f"Gagal has_state untuk admin_id {admin_id}: {e}", exc_info=True)
        return False


# ========================================== #
# === TEMP STATE: ADD, DELETE VIP USER ===== #
# ========================================== #


def get_all_admin_temp_states(admin_id: int) -> dict:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                "SELECT key, value FROM admin_temp_state WHERE admin_id = %s",
                (admin_id,),
            )
            rows = cursor.fetchall()
            return {key: value for key, value in rows} if rows else {}
    except Exception as e:
        log.error(
            f"[STATE] Gagal ambil semua temp state untuk admin_id={admin_id}: {e}",
            exc_info=True,
        )
        return {}


def set_admin_temp_state(admin_id: int, key: str, value) -> None:
    try:
        # Pastikan value adalah string, jika dict atau tipe lain, konversi ke JSON
        if not isinstance(value, str):
            try:
                value = json.dumps(value)
            except Exception as e:
                log.error(f"[STATE] Gagal JSON encode value={value}: {e}")
                return

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

            log.info(
                f"[STATE] Set temp state sukses: admin_id={admin_id}, key={key}, value={value}"
            )

            # Debug tambahan
            cursor.execute(
                "SELECT value FROM admin_temp_state WHERE admin_id = %s AND key = %s",
                (admin_id, key),
            )
            val = cursor.fetchone()
            log.info(f"[STATE] Setelah commit, nilai tersimpan: {val}")
    except Exception as e:
        log.error(
            f"[STATE] Gagal set temp state (admin_id={admin_id}, key={key}): {e}",
            exc_info=True,
        )


def get_admin_temp_state(admin_id: int, key: str, default=None):
    log.debug(f"[STATE] Mengambil temp state (admin_id={admin_id}, key={key})")
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT value FROM admin_temp_state
                WHERE admin_id = %s AND key = %s
                """,
                (admin_id, key),
            )
            result = cursor.fetchone()
            if result:
                raw_val = result[0]
                log.debug(f"[STATE] Ditemukan value: {raw_val}")

                # Perlakuan khusus untuk nilai kosong atau 'null'
                if raw_val in [None, "", "null", "None"]:
                    return default

                return raw_val
            log.debug(f"[STATE] Tidak ditemukan value. Kembalikan default.")
            return default
    except Exception as e:
        log.error(
            f"[STATE] Gagal ambil temp state (admin_id={admin_id}, key={key}): {e}",
            exc_info=True,
        )
        return default


def clear_admin_temp_state(admin_id: int, prefix: str = None) -> None:
    try:
        with get_db_cursor() as (cursor, conn):
            if prefix:
                # Hapus hanya yang dimulai dengan prefix (misal: 'utbk_')
                cursor.execute(
                    """
                    DELETE FROM admin_temp_state
                    WHERE admin_id = %s AND key LIKE %s
                    """,
                    (admin_id, f"{prefix}%"),
                )
                log.info(
                    f"[STATE] clear_admin_temp_state dengan prefix '{prefix}' untuk admin_id={admin_id}"
                )
            else:
                # Hapus semua state admin (fallback lama)
                cursor.execute(
                    "DELETE FROM admin_temp_state WHERE admin_id = %s", (admin_id,)
                )
                log.info(
                    f"[STATE] clear_admin_temp_state (semua key) untuk admin_id={admin_id}"
                )
            conn.commit()
    except Exception as e:
        log.error(
            f"[STATE] Gagal hapus temp state admin_id={admin_id} (prefix={prefix}): {e}",
            exc_info=True,
        )


def clear_admin_state_all_bots(admin_id: int):
    return clear_admin_temp_state(admin_id, prefix=None)


# ========================================== #
# === UTILITAS PENDUKUNG =================== #
# ========================================== #


def get_current_admin_steps(user_id: int) -> dict:
    state = get_state(user_id) or {}
    return {
        "regular_step": state.get("regular_step"),
        "vip_add_step": state.get("vip_add_step"),
        "vip_delete_step": state.get("vip_delete_step"),
    }


def get_json_temp_state(admin_id: int, key: str, default=None):
    val = get_admin_temp_state(admin_id, key)
    if val is None:
        return default
    try:
        return json.loads(val)
    except Exception as e:
        log.error(
            f"[STATE] Gagal decode JSON dari key={key} untuk admin_id={admin_id}: {e}"
        )
        return default


def is_state_expired(state_value) -> bool:
    # Implementasi TTL jika diperlukan
    # Contoh:
    # import time
    # return time.time() > state_value.get("expires_at", 0)
    return False  # Placeholder


def print_admin_states(admin_id: int, prefix_filter: str | None = None):
    """
    Cetak semua state admin_id tertentu.
    Jika prefix_filter diberikan (misal 'drac1n_', 'utbk_'), hanya tampilkan key yang sesuai.
    """
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

            print(f"\n🧠 State untuk admin_id={admin_id}:")
            for key, value in rows:
                try:
                    parsed = json.loads(value)
                except Exception:
                    parsed = value
                print(f"🔑 {key}: {parsed}")

    except Exception as e:
        log.error(
            f"[DEBUG] Gagal print_admin_states admin_id={admin_id}: {e}", exc_info=True
        )
