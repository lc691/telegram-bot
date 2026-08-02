import time

from psycopg2.extras import execute_batch

from configs.logging_setup import log
from db.connect import get_db_cursor


TOP_TRENDING_LIMIT = 1000


def refresh_trending_cache():

    start_time = time.perf_counter()

    try:
        with get_db_cursor() as (cursor, conn):

            # =====================================================
            # COMPUTE TRENDING SCORE
            # =====================================================

            cursor.execute(
                """
                WITH scored AS (

                    SELECT
                        sf.show_id,

                        SUM(vs.play_count) AS total_plays,

                        MAX(vs.last_played) AS last_played,

                        (
                            SUM(vs.play_count)::float
                            /
                            POWER(
                                GREATEST(
                                    EXTRACT(
                                        EPOCH FROM (
                                            NOW() - MAX(vs.last_played)
                                        )
                                    ) / 3600,
                                    1
                                ),
                                1.3
                            )
                        ) AS score

                    FROM video_stats vs

                    JOIN files f0
                        ON f0.file_id = vs.file_id

                    JOIN show_files sf
                        ON sf.file_id = f0.id

                    WHERE vs.last_played >= NOW() - INTERVAL '30 days'

                    GROUP BY sf.show_id

                    HAVING SUM(vs.play_count) > 0
                ),

                ranked AS (

                    SELECT
                        s.id AS show_id,
                        s.title,
                        s.thumbnail_url,
                        f.channel_username,
                        sf.message_id,
                        sc.score,
                        sc.total_plays,
                        sc.last_played

                    FROM scored sc

                    JOIN shows s
                        ON s.id = sc.show_id

                    JOIN LATERAL (
                        SELECT
                            sf2.file_id,
                            sf2.message_id
                        FROM show_files sf2
                        WHERE sf2.show_id = sc.show_id
                        AND sf2.message_id IS NOT NULL
                        ORDER BY sf2.message_id DESC
                        LIMIT 1
                    ) sf ON TRUE

                    JOIN files f
                        ON f.id = sf.file_id

                    ORDER BY sc.score DESC

                    LIMIT %s
                )

                SELECT
                    show_id,
                    title,
                    thumbnail_url,
                    channel_username,
                    message_id,
                    score,
                    total_plays,
                    last_played

                FROM ranked

                ORDER BY score DESC
                """,
                (TOP_TRENDING_LIMIT,),
            )

            rows = cursor.fetchall() or []

            if not rows:
                log.warning(
                    "[TRENDING] no rows generated"
                )
                return

            # =====================================================
            # BUILD INSERT PAYLOAD
            # =====================================================

            payload = []

            for rank, row in enumerate(rows, start=1):

                (
                    show_id,
                    title,
                    thumbnail_url,
                    channel_username,
                    message_id,
                    score,
                    total_plays,
                    last_played,
                ) = row

                payload.append(
                    (
                        show_id,
                        score,
                        total_plays,
                        last_played,
                        message_id,
                        channel_username,
                        thumbnail_url,
                        title,
                        rank,
                    )
                )

            # =====================================================
            # REBUILD CACHE
            # =====================================================

            cursor.execute(
                "TRUNCATE TABLE trending_cache"
            )

            execute_batch(
                cursor,
                """
                INSERT INTO trending_cache (
                    show_id,
                    score,
                    total_plays,
                    last_played,
                    message_id,
                    channel_username,
                    thumbnail_url,
                    title,
                    rank
                )
                VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                payload,
                page_size=500,
            )

            conn.commit()

        duration = time.perf_counter() - start_time

        log.info(
            "[TRENDING] cache refreshed rows=%s duration=%.2fs",
            len(payload),
            duration,
        )

    except Exception:
        log.exception(
            "[TRENDING] refresh failed"
        )
        raise


if __name__ == "__main__":

    refresh_trending_cache()