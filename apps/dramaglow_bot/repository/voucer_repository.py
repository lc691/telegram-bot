import random
import string

from datetime import datetime, timedelta
from uuid import uuid4

from database.connection import get_db_cursor


def generate_voucher_code(length=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_bulk_vouchers(
    jumlah: int, durasi: int, expires_in: int = 30, created_by: str = "admin"
):
    """
    Generate a batch of unique voucher codes and store them in the database.

    :param jumlah: Jumlah voucher yang ingin dibuat
    :param durasi: Durasi VIP dalam hari
    :param expires_in: Berapa hari sebelum voucher kadaluarsa
    :param created_by: Username atau ID pembuat voucher
    :return: Tuple of (list of codes, batch_id)
    """
    batch_id = str(uuid4())
    codes = set()

    with get_db_cursor(commit=True) as (cur, _):
        for _ in range(jumlah):
            # Hindari duplikat
            for _ in range(10):  # Maks 10 kali coba generate unik
                code = f"VIP{durasi}D-" + generate_voucher_code()
                cur.execute("SELECT 1 FROM vip_vouchers WHERE code = %s", (code,))
                if not cur.fetchone() and code not in codes:
                    break
            else:
                raise Exception("❌ Gagal membuat kode unik setelah 10 percobaan.")

            expires_at = datetime.utcnow() + timedelta(days=expires_in)

            cur.execute(
                """
                INSERT INTO vip_vouchers (code, duration_days, expires_at, created_by, batch_uuid)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (code, durasi, expires_at, created_by, batch_id),
            )

            codes.add(code)

    return list(codes), batch_id
