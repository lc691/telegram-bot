from datetime import datetime, timezone

from configs.logging_setup import log
from database.connection import get_db_cursor


def update_video_stat(user_id: int, file_id: str) -> None:
    """
    Menambahkan atau memperbarui statistik pemutaran video.
    - Jika belum ada, buat entri baru dengan play_count = 1.
    - Jika sudah ada, tingkatkan play_count dan perbarui last_played.
    """
    now_utc = datetime.now(timezone.utc)
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO video_stats (user_id, file_id, play_count, last_played)
                VALUES (%s, %s, 1, %s)
                ON CONFLICT (user_id, file_id)
                DO UPDATE SET
                    play_count = video_stats.play_count + 1,
                    last_played = EXCLUDED.last_played
                """,
                (user_id, file_id, now_utc),
            )
            conn.commit()
            log.info("Video stat diperbarui: user_id=%s, file_id=%s", user_id, file_id)
    except Exception as e:
        log.error(
            "Gagal update_video_stat user_id=%s, file_id=%s: %s",
            user_id,
            file_id,
            e,
            exc_info=True,
        )
