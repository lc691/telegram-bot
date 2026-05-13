# app/repositories/vip/vip_packages_repo.py
from configs.logging_setup import log
from db.connect import get_db_cursor


async def get_vip_packages_from_db() -> list[dict]:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT paket_name, display_label, price, is_promo_once, basic_days, total_days
                FROM vip_packages
                WHERE is_active IS TRUE
                ORDER BY is_promo_once DESC, price ASC
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "paket": row[0],
                    "label": row[1] or row[0],
                    "price": row[2] or 0,
                    "is_promo_once": row[3],
                    "basic_days": row[4] or 0,
                    "total_days": row[5] or 0,
                }
                for row in rows
            ]
    except Exception as e:
        log.error("[VIP_REPO] Gagal ambil paket VIP: %s", e, exc_info=True)
        return []


async def has_used_promo(user_id: int) -> bool:
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute(
                """
                SELECT 1
                FROM vip_users
                JOIN vip_packages
                  ON vip_users.paket = vip_packages.paket_name
                WHERE user_id = %s
                  AND vip_packages.is_promo_once IS TRUE
                  AND vip_users.status = 'active'
                  AND vip_users.end_date > now()
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone() is not None
    except Exception as e:
        log.error("[VIP_REPO] Gagal cek promo user=%s: %s", user_id, e, exc_info=True)
        return False


def format_manual_packages(packages: list[dict]) -> str:
    allowed_days = {15, 30}

    manual_packages = [
        p for p in packages
        if not p.get("is_promo_once")
        and p.get("basic_days") in allowed_days
    ]

    if not manual_packages:
        return "🔥 **Manual (Opsional)**\n└─ Tidak tersedia saat ini"

    lines = ["🔥 **Manual (Opsional)**"]

    for p in manual_packages:
        price = p.get("price", 0)
        basic_days = p.get("basic_days", 0)
        total_days = p.get("total_days", 0)
        bonus_days = max(total_days - basic_days, 0)

        price_text = f"Rp{price/1000:.1f}K".replace(".0", "")
        line = f"└─ {price_text} → {basic_days} Hari"

        if bonus_days > 0:
            line += f" 🎁 Bonus {bonus_days} Hari"

        lines.append(line)

    return "\n".join(lines)
