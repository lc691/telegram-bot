from configs.logging_setup import log
from .constants import STAGE_NAME, ALERT_STAGE
from common.utils.admin_cache import admin_cache


MIN_SAMPLE_SIZE = 20
MIN_CONVERSION_RATE = 5.0
ALERT_COOLDOWN_HOURS = 24
ANALYSIS_WINDOW_DAYS = 14


async def retention_summary(pool):
    """
    Log summary conversion rate all-time.
    """

    async with pool.acquire() as conn:

        total = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM retention_log
            WHERE stage = $1;
            """,
            STAGE_NAME,
        )

        if not total:
            return

        converted = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM retention_log
            WHERE stage = $1
            AND converted = TRUE;
            """,
            STAGE_NAME,
        )

        rate = (converted / total) * 100

        log.info(
            "Retention summary | total=%d converted=%d rate=%.2f%%",
            total,
            converted,
            rate,
        )


async def check_low_conversion_alert(app, pool):
    """
    Jika conversion rate < threshold dalam 14 hari terakhir,
    kirim alert ke admin (max 1x per 24 jam).
    """

    async with pool.acquire() as conn:

        row = await conn.fetchrow(
            f"""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE converted = TRUE) AS converted
            FROM retention_log
            WHERE stage = $1
            AND sent_at >= NOW() - INTERVAL '{ANALYSIS_WINDOW_DAYS} days';
            """,
            STAGE_NAME,
        )

        total = row["total"]
        converted = row["converted"]

        # Sample terlalu kecil → jangan alert
        if not total or total < MIN_SAMPLE_SIZE:
            return

        rate = (converted / total) * 100

        # Rate masih sehat → tidak perlu alert
        if rate >= MIN_CONVERSION_RATE:
            return

        # Cek cooldown alert
        already_alerted = await conn.fetchval(
            f"""
            SELECT 1
            FROM retention_log
            WHERE stage = $1
            AND sent_at >= NOW() - INTERVAL '{ALERT_COOLDOWN_HOURS} hours'
            LIMIT 1;
            """,
            ALERT_STAGE,
        )

        if already_alerted:
            return

        # Kirim alert ke admin
        try:
            admin_ids = await admin_cache.get_admin_ids()

            message = (
                "⚠️ RETENTION PERFORMANCE ALERT\n\n"
                f"Conversion rate (last {ANALYSIS_WINDOW_DAYS} days): {rate:.2f}%\n"
                f"Total reminder: {total}\n"
                f"Converted: {converted}\n\n"
                "Copy atau timing mungkin perlu dioptimasi."
            )

            for admin_id in admin_ids:
                await app.send_message(
                    chat_id=admin_id,
                    text=message,
                )

            # Catat alert sebagai event
            await conn.execute(
                """
                INSERT INTO retention_log (user_id, stage)
                VALUES (0, $1);
                """,
                ALERT_STAGE,
            )

            log.warning(
                "Low retention conversion alert sent (%.2f%%)",
                rate,
            )

        except Exception:
            log.exception("Failed sending retention alert")
