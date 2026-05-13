from configs.logging_setup import log


def calculate_total_duration(durasi_hari, basic_days, bonus_days):
    if durasi_hari is None:
        durasi_hari = basic_days + bonus_days

    if durasi_hari <= 0:
        log.warning(f"[VIP] Durasi tidak valid: {durasi_hari}")

    return durasi_hari
