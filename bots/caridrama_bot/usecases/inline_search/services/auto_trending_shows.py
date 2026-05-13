from ..types import ResultKind, SearchResult


def get_auto_trending_shows(
    *,
    cursor,
    limit: int,
    offset: int,
) -> SearchResult:
    """
    AUTO TRENDING (TIME-DECAY MODEL)

    Filosofi:
    ----------
    Trending ≠ Popularity (total lifetime plays).
    Trending = kecepatan interaksi terhadap waktu terakhir aktivitas.

    Model yang digunakan:
        score = total_plays / (age_hours ^ 1.3)

    Dimana:
        total_plays = SUM(play_count semua file dalam 1 show)
        last_played = MAX(last_played semua file dalam 1 show)
        age_hours   = jam sejak show terakhir dimainkan

    Kenapa model ini:
        - Show lama tapi tidak aktif → turun perlahan
        - Show yang sedang aktif → naik cepat
        - Tidak memakai hard window (tidak ada cutoff 3 hari)
        - Stabil untuk konten episodik (banyak part)

    Pagination:
        - Ambil limit + 1 untuk deteksi has_more
        - Return hanya `limit`
        - has_more diset berdasarkan extra row

    Performance Notes:
        - Wajib ada index:
            video_stats(file_id)
            video_stats(last_played DESC)
            show_files(show_id)
            show_files(file_id)
    """

    if limit <= 0:
        return SearchResult.empty(ResultKind.TRENDING)

    offset = max(offset, 0)
    fetch_limit = limit + 1

    cursor.execute(
        """
        WITH show_stats AS (
            -- 1️⃣ Agregasi per show (gabungkan semua part)
            SELECT
                sf.show_id,
                SUM(vs.play_count) AS total_plays,
                MAX(vs.last_played) AS last_played
            FROM video_stats vs
            JOIN files f ON f.file_id = vs.file_id
            JOIN show_files sf ON sf.file_id = f.id
            GROUP BY sf.show_id
            HAVING SUM(vs.play_count) > 0
        ),
        scored AS (
            -- 2️⃣ Hitung score trending (time-decay)
            SELECT
                s.id AS show_id,
                s.title,
                s.thumbnail_url,
                ss.total_plays,
                ss.last_played,
                (
                    ss.total_plays::float
                    /
                    POWER(
                        GREATEST(
                            EXTRACT(EPOCH FROM (NOW() - ss.last_played)) / 3600,
                            1
                        ),
                        1.3
                    )
                ) AS score
            FROM show_stats ss
            JOIN shows s ON s.id = ss.show_id
        ),
        ranked AS (
            -- 3️⃣ Ambil 1 file representatif per show
            SELECT
                sc.show_id,
                sc.title,
                sc.thumbnail_url,
                f.channel_username,
                sf.message_id,
                sc.score,
                ROW_NUMBER() OVER (
                    PARTITION BY sc.show_id
                    ORDER BY sf.message_id DESC
                ) AS rn
            FROM scored sc
            JOIN show_files sf ON sf.show_id = sc.show_id
            JOIN files f ON f.id = sf.file_id
            WHERE sf.message_id IS NOT NULL
        )
        SELECT
            show_id,
            title,
            thumbnail_url,
            channel_username,
            message_id
        FROM ranked
        WHERE rn = 1
        ORDER BY score DESC
        LIMIT %s OFFSET %s
        """,
        (fetch_limit, offset),
    )

    raw_rows = cursor.fetchall() or []

    # ==============================
    # PAGINATION DETECTION
    # ==============================
    has_more = len(raw_rows) > limit
    rows = raw_rows[:limit]

    return SearchResult(
        rows=rows,
        kind=ResultKind.TRENDING if rows else ResultKind.FALLBACK,
        has_more=has_more,
    )
