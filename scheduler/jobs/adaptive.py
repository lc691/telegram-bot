from configs.logging_setup import log
from .constants import STAGE_NAME


FAILURE_EVALUATION_DAYS = 3


async def update_failures(pool):
    """
    Update adaptive offset jika reminder tidak convert
    dalam 3 hari setelah dikirim.

    Logic:
        0 fail  -> offset 0
        1 fail  -> offset +3 hari
        >=2 fail -> offset +7 hari

    Menggunakan failure_processed untuk mencegah double increment.
    """

    async with pool.acquire() as conn:

        rows = await conn.fetch(
            """
            SELECT id, user_id
            FROM retention_log
            WHERE stage = $1
            AND converted = FALSE
            AND failure_processed = FALSE
            AND sent_at <= NOW() - ($2 * INTERVAL '1 day');
            """,
            STAGE_NAME,
            FAILURE_EVALUATION_DAYS,
        )

        if not rows:
            return

        for row in rows:
            user_id = row["user_id"]

            record = await conn.fetchrow(
                """
                SELECT fail_count
                FROM retention_adaptive
                WHERE user_id = $1;
                """,
                user_id,
            )

            if record:
                new_fail = record["fail_count"] + 1
            else:
                new_fail = 1

            # Adaptive offset logic
            if new_fail >= 2:
                offset_days = 7
            elif new_fail == 1:
                offset_days = 3
            else:
                offset_days = 0

            await conn.execute(
                """
                INSERT INTO retention_adaptive (user_id, fail_count, offset_days)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    fail_count = EXCLUDED.fail_count,
                    offset_days = EXCLUDED.offset_days,
                    updated_at = NOW();
                """,
                user_id,
                new_fail,
                offset_days,
            )

            # Mark failure as processed
            await conn.execute(
                """
                UPDATE retention_log
                SET failure_processed = TRUE
                WHERE id = $1;
                """,
                row["id"],
            )

        log.info("Adaptive retention updated for %d users", len(rows))
