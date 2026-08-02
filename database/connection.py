import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor

from config import PGDATABASE, PGHOST, PGPASSWORD, PGPORT, PGUSER
from configs.logging_setup import log


# ============================================================
# FUNGSI KONEKSI DASAR
# ============================================================

def _connect_with_retry(retries=3, delay=2):
    """
    Mencoba koneksi ke database dengan mekanisme retry otomatis.

    Args:
        retries (int): Jumlah percobaan maksimal
        delay (int): Waktu tunggu antar percobaan (detik)

    Returns:
        psycopg2.connection: Objek koneksi database

    Raises:
        psycopg2.Error: Jika semua percobaan gagal
    """
    last_err = None

    for attempt in range(1, retries + 1):
        try:
            # Prioritaskan DATABASE_URL jika tersedia
            database_url = os.getenv("DATABASE_URL")

            if database_url:
                conn = psycopg2.connect(database_url, sslmode="require")
            else:
                conn = psycopg2.connect(
                    host=PGHOST,
                    port=PGPORT,
                    dbname=PGDATABASE,
                    user=PGUSER,
                    password=PGPASSWORD,
                    sslmode="require",
                )

            return conn

        except psycopg2.Error as e:
            last_err = e
            log.warning(f"[DB] ⚠️ Gagal koneksi attempt {attempt}/{retries}: {e}")
            time.sleep(delay)

    raise last_err


# ============================================================
# CONTEXT MANAGER KONEKSI
# ============================================================

@contextmanager
def get_db_connection():
    """
    Context manager untuk koneksi database.

    Yields:
        psycopg2.connection: Objek koneksi database

    Raises:
        psycopg2.Error: Jika gagal membuat koneksi
    """
    conn = None

    try:
        conn = _connect_with_retry()
        log.debug(f"[DB] ✅ Koneksi dibuka ke {PGHOST}:{PGPORT}/{PGDATABASE}")
        yield conn

    except psycopg2.Error:
        log.error(
            f"[DB] ❌ Gagal koneksi ke database {PGDATABASE} di {PGHOST}:{PGPORT}",
            exc_info=True,
        )
        raise

    finally:
        if conn:
            conn.close()
            log.debug("[DB] 🔌 Koneksi database ditutup.")


# ============================================================
# CONTEXT MANAGER CURSOR
# ============================================================

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager untuk cursor database standar.

    Args:
        commit (bool): Auto-commit setelah operasi selesai

    Yields:
        tuple: (cursor, connection)
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                yield cursor, conn

                if commit:
                    conn.commit()
                    log.debug("[DB] ✅ Commit otomatis berhasil.")

            except Exception:
                conn.rollback()
                log.warning("[DB] ↩️ Rollback karena error di get_db_cursor.")
                raise


@contextmanager
def get_dict_cursor(commit=False):
    """
    Context manager untuk cursor dictionary (hasil query sebagai dict).

    Args:
        commit (bool): Auto-commit setelah operasi selesai

    Yields:
        tuple: (DictCursor, connection)
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            try:
                yield cursor, conn

                if commit:
                    conn.commit()
                    log.debug("[DB] ✅ Commit otomatis (dict cursor) berhasil.")

            except Exception:
                conn.rollback()
                log.warning("[DB] ↩️ Rollback karena error di get_dict_cursor.")
                raise


@contextmanager
def get_autocommit_cursor():
    """
    Context manager untuk cursor dengan mode autocommit.

    Yields:
        psycopg2.cursor: Cursor dengan autocommit aktif
    """
    with get_db_connection() as conn:
        conn.autocommit = True

        with conn.cursor() as cursor:
            yield cursor

        log.debug("[DB] ⚡ Autocommit cursor selesai.")


@contextmanager
def get_simple_cursor(commit=False):
    """
    Context manager sederhana untuk cursor (tanpa return connection).

    Args:
        commit (bool): Auto-commit setelah operasi selesai

    Yields:
        psycopg2.cursor: Cursor database
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                yield cursor

                if commit:
                    conn.commit()
                    log.debug("[DB] ✅ Commit otomatis (simple cursor) berhasil.")

            except Exception:
                conn.rollback()
                log.warning("[DB] ↩️ Rollback karena error di get_simple_cursor.")
                raise
