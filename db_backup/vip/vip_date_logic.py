from datetime import timedelta


def calculate_dates(now, row, durasi_hari: int):
    """
    Rules:
    1️⃣ Tidak ada VIP → Baru
    2️⃣ VIP masih aktif → Extend
    3️⃣ VIP expired → Reset jadi Baru
    """

    # 1️⃣ Tidak ada VIP sama sekali
    if not row:
        start = now
        end = now + timedelta(days=durasi_hari)

        return {
            "start": start,
            "end": end,
            "is_extend": False,
            "expired_lama": None
        }

    expired_at = row["end_date"]

    # 2️⃣ VIP MASIH AKTIF → EXTEND
    if expired_at and expired_at > now:
        start = row["start_date"]
        end = expired_at + timedelta(days=durasi_hari)

        return {
            "start": start,
            "end": end,
            "is_extend": True,
            "expired_lama": expired_at,
        }

    # 3️⃣ VIP EXPIRED → RESET BARU
    start = now
    end = now + timedelta(days=durasi_hari)

    return {
        "start": start,
        "end": end,
        "is_extend": False,
        "expired_lama": expired_at,
    }
