from configs.logging_setup import log
from database import get_dict_cursor


def add_affiliate_commission(
    buyer_user_id: int,
    package_name: str,
    price: int,
    commission_percent: float = 0.20
):
    """
    Menambahkan komisi ke upline ketika buyer membeli VIP.
    - buyer_user_id : user yang membeli VIP
    - package_name  : nama paket dari vip_packages
    - price         : harga paket VIP
    - commission_percent : default 20%
    """

    commission = int(price * commission_percent)

    try:
        with get_dict_cursor(commit=True) as (cur, conn):
            # STEP 1: Ambil referrer user_id
            cur.execute("""
                SELECT referrer_user_id
                FROM users
                WHERE user_id = %s
                LIMIT 1
            """, (buyer_user_id,))
            row = cur.fetchone()

            if not row or not row["referrer_user_id"]:
                log.info(f"[AFFILIATE] Buyer {buyer_user_id} tidak punya upline.")
                return False

            upline_user_id = row["referrer_user_id"]

            # STEP 2: Berikan komisi ke upline
            cur.execute("""
                UPDATE users
                SET
                    affiliate_balance = affiliate_balance + %s,
                    affiliate_total_earned = affiliate_total_earned + %s
                WHERE user_id = %s
            """, (commission, commission, upline_user_id))

            # STEP 3: Update purchase info buyer
            cur.execute("""
                UPDATE users
                SET
                    first_purchase_at = COALESCE(first_purchase_at, NOW()),
                    last_purchase_at = NOW()
                WHERE user_id = %s
            """, (buyer_user_id,))

            log.info(
                f"[AFFILIATE] 👍 Komisi {commission} diberikan ke {upline_user_id} "
                f"dari pembelian buyer {buyer_user_id} (paket={package_name})"
            )

            return {
                "upline_user_id": upline_user_id,
                "commission": commission,
            }

    except Exception as e:
        log.error(f"[AFFILIATE] ❌ Error saat pemberian komisi: {e}", exc_info=True)
        return False
