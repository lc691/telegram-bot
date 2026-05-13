# setup_db.py

from db.models import ensure_all_tables

if __name__ == "__main__":
    ensure_all_tables()
    print("✅ Semua tabel berhasil dicek/dibuat.")
