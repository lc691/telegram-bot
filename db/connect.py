import os
import time

from contextlib import contextmanager

import psycopg2

from psycopg2.extras import DictCursor

from config import PGDATABASE, PGHOST, PGPASSWORD, PGPORT, PGUSER
from configs.logging_setup import log


def _connect_with_retry(retries=3, delay=2):
    """
    Mencoba koneksi ke DB dengan retry otomatis.
    """
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            # Gunakan DATABASE_URL kalau tersedia
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


@contextmanager
def get_db_connection():
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


@contextmanager
def get_db_cursor(commit=False):
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
    with get_db_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            yield cursor
        log.debug("[DB] ⚡ Autocommit cursor selesai.")


@contextmanager
def get_simple_cursor(commit=False):
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
