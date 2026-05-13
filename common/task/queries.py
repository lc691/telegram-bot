import asyncio
from configs.logging_setup import log
from .constants import STAGE_NAME


BATCH_LIMIT = 50


async def run_retention(app, pool):
    """
    Kirim retention message ke heavy users
    berdasarkan median gap personal + adaptive offset.
    """

    async with pool.acquire() as conn:

        rows = await conn.fetch(
            """
            WITH purchases AS (
                SELECT
                    target_user_id,
                    "timestamp",
                    LAG("timestamp") OVER (
                        PARTITION BY target_user_id
                        ORDER BY "timestamp"
                    ) AS prev_ts
                FROM vip_logs
                WHERE is_test = false
                AND is_extend = false
            ),
            gaps AS (
                SELECT
                    target_user_id,
                    EXTRACT(EPOCH FROM ("timestamp" - prev_ts)) / 86400 AS gap_days
                FROM purchases
                WHERE prev_ts IS NOT NULL
            ),
            median_gap AS (
                SELECT
                    target_user_id,
                    percentile_cont(0.5)
                    WITHIN GROUP (ORDER BY gap_days) AS median_gap_days
                FROM gaps
                GROUP BY target_user_id
            ),
            user_stats AS (
                SELECT
                    v.target_user_id,
                    COUNT(*) AS total_transactions,
                    SUM(durasi_hari) AS total_days,
                    MAX("timestamp") AS last_buy
                FROM vip_logs v
                WHERE v.is_test = false
                AND v.is_extend = false
                GROUP BY v.target_user_id
                HAVING COUNT(*) >= 5
            )
            SELECT
                u.target_user_id,
                u.total_transactions,
                u.total_days,
                ROUND(m.median_gap_days)::int AS median_gap_days,
                EXTRACT(DAY FROM (NOW() - u.last_buy))::int AS gap_now
            FROM user_stats u
            JOIN median_gap m
                ON u.target_user_id = m.target_user_id
            LEFT JOIN retention_adaptive a
                ON u.target_user_id = a.user_id
            LEFT JOIN retention_log r
                ON r.user_id = u.target_user_id
                AND r.stage = $1
            WHERE
                NOW() - u.last_buy >=
                    ((m.median_gap_days + COALESCE(a.offset_days,0)) || ' days')::interval
            AND
                NOW() - u.last_buy <=
                    ((m.median_gap_days + COALESCE(a.offset_days,0) + 2) || ' days')::interval
            AND r.user_id IS NULL
            ORDER BY u.last_buy ASC
            LIMIT $2;
            """,
            STAGE_NAME,
            BATCH_LIMIT,
        )

        if not rows:
            return

        log.info("Retention: %d user eligible", len(rows))

        for row in rows:
            user_id = row["target_user_id"]
            total_tx = row["total_transactions"]
            total_days = row["total_days"]
            median_gap = row["median_gap_days"]
            gap_now = row["gap_now"]

            message = (
                f"🔥 Biasanya kamu lanjut tiap sekitar {median_gap} hari.\n\n"
                f"Sekarang sudah {gap_now} hari sejak terakhir aktif.\n\n"
                f"Total kamu sudah {total_tx}x beli "
                f"({total_days} hari akses).\n\n"
                "Mau lanjut lagi hari ini?"
            )

            try:
                await app.send_message(
                    chat_id=user_id,
                    text=message,
                )

                await conn.execute(
                    """
                    INSERT INTO retention_log (user_id, stage)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING;
                    """,
                    user_id,
                    STAGE_NAME,
                )

                # throttle ringan untuk hindari flood
                await asyncio.sleep(0.4)

            except Exception:
                log.warning(
                    "Retention send failed for %s",
                    user_id,
                    exc_info=True,
                )
