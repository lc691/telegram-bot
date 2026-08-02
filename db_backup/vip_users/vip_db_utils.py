from db.connect import get_db_cursor


def get_vip_package_info(paket_name: str) -> dict | None:
    """
    Ambil info paket VIP dari DB berdasarkan nama paket atau alias (case-insensitive).
    """
    paket_name = paket_name.lower().strip()

    with get_db_cursor() as (cur, _):
        cur.execute(
            """
            SELECT paket_name, basic_days, total_days, is_promo_once, price, is_active
            FROM vip_packages
            WHERE is_active = TRUE AND (LOWER(paket_name) = %s OR LOWER(alias) = %s)
            LIMIT 1
            """,
            (paket_name, paket_name),
        )
        row = cur.fetchone()

    if not row:
        return None

    paket, basic_days, total_days, is_promo_once, price, is_active = row
    bonus_days = max(total_days - basic_days, 0)

    return {
        "paket": paket,
        "basic_days": basic_days,
        "total_days": total_days,
        "bonus_days": bonus_days,
        "is_promo_once": is_promo_once,
        "price": price,
        "is_active": is_active,
    }


def get_vip_basic_days(paket_name: str) -> int:
    info = get_vip_package_info(paket_name)
    return info["basic_days"] if info else 0


def get_vip_bonus_days(paket_name: str) -> int:
    info = get_vip_package_info(paket_name)
    return info["bonus_days"] if info else 0


def resolve_paket_alias(paket_name: str) -> str:
    info = get_vip_package_info(paket_name)
    return info["paket"] if info else paket_name.lower()


def get_all_vip_prices() -> set[int]:
    """
    Ambil semua harga paket VIP aktif dari DB.
    Return dalam bentuk set of int.
    """
    with get_db_cursor() as (cur, _):
        cur.execute(
            """
            SELECT price
            FROM vip_packages
            WHERE is_active = TRUE
            """
        )
        rows = cur.fetchall()

    return {row[0] for row in rows if row and row[0]}


def get_vip_package_by_price(price: int) -> dict | None:
    """
    Ambil info paket VIP berdasarkan harga (price).
    """
    with get_db_cursor() as (cur, _):
        cur.execute(
            """
            SELECT paket_name, basic_days, total_days, is_promo_once, price, is_active
            FROM vip_packages
            WHERE is_active = TRUE AND price = %s
            LIMIT 1
            """,
            (price,),
        )
        row = cur.fetchone()

    if not row:
        return None

    paket, basic_days, total_days, is_promo_once, price, is_active = row
    bonus_days = max(total_days - basic_days, 0)

    return {
        "paket": paket,
        "basic_days": basic_days,
        "total_days": total_days,
        "bonus_days": bonus_days,
        "is_promo_once": is_promo_once,
        "price": price,
        "is_active": is_active,
    }
