from configs.logging_setup import log
from .constants import STAGE_NAME


CONVERSION_WINDOW_DAYS = 3


async def check_conversions(pool):
    """
    Tandai reminder sebagai converted jika user membeli
    dalam 3 hari setelah reminder.

    Juga:
    - Simpan revenue_days
    - Simpan revenue_amount
    - Reset adaptive offset
    """

    async with pool.acquire() as conn:

        rows = await conn.fetch(
            """
            SELECT r.id, r.user_id, r.sent_at
            FROM retention_log r
            WHERE r.stage = $1
            AND r.converted = FALSE
            AND r.sent_at >= NOW() - INTERVAL '14 days';
            """,
            STAGE_NAME,
        )

        if not rows:
            return

        converted_count = 0
        total_revenue = 0

        for row in rows:

            purchase_data = await conn.fetchrow(
                """
                SELECT 
                    COALESCE(SUM(v.durasi_hari),0) AS total_days,
                    COALESCE(SUM(p.price),0) AS total_amount
                FROM vip_logs v
                JOIN vip_packages p
                    ON v.paket = p.paket_name
                WHERE v.target_user_id = $1
                AND v.is_test = false
                AND v.is_extend = false
                AND v."timestamp" > $2
                AND v."timestamp" <= $2 + ($3 * INTERVAL '1 day');
                """,
                row["user_id"],
                row["sent_at"],
                CONVERSION_WINDOW_DAYS,
            )

            if purchase_data and purchase_data["total_days"] > 0:

                await conn.execute(
                    """
                    UPDATE retention_log
                    SET converted = TRUE,
                        converted_at = NOW(),
                        revenue_days = $2,
                        revenue_amount = $3
                    WHERE id = $1;
                    """,
                    row["id"],
                    purchase_data["total_days"],
                    purchase_data["total_amount"],
                )

                # Reset adaptive offset
                await conn.execute(
                    """
                    DELETE FROM retention_adaptive
                    WHERE user_id = $1;
                    """,
                    row["user_id"],
                )

                converted_count += 1
                total_revenue += purchase_data["total_amount"]

        if converted_count > 0:
            log.info(
                "Retention conversions detected: %d | revenue=%s",
                converted_count,
                total_revenue,
            )


async def retention_summary(pool):
    """
    Log summary conversion + revenue all-time.
    """

    async with pool.acquire() as conn:

        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE converted = TRUE) AS converted,
                COALESCE(SUM(revenue_days),0) AS total_days,
                COALESCE(SUM(revenue_amount),0) AS total_revenue
            FROM retention_log
            WHERE stage = $1;
            """,
            STAGE_NAME,
        )

        total = stats["total"]

        if not total:
            return

        converted = stats["converted"]
        total_days = stats["total_days"]
        total_revenue = stats["total_revenue"]

        rate = (converted / total) * 100

        log.info(
            "Retention summary | total=%d converted=%d rate=%.2f%% days=%d revenue=%s",
            total,
            converted,
            rate,
            total_days,
            total_revenue,
        )
