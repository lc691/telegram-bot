from configs.logging_setup import log
from db.connect import get_dict_cursor


# ===============================
# INTERNAL: PERIOD FILTER
# ===============================
def _build_period_filter(period: str, date: str | None):
    """
    Build SQL filter + params berdasarkan period.
    Seluruh logic berbasis timestamp_date_wib (WIB).
    """

    if period == "all":
        return "", []

    if period == "daily":
        if not date:
            raise ValueError("daily leaderboard requires date")
        return "AND l.timestamp_date_wib = %s", [date]

    if period == "weekly":
        # 7 hari terakhir inklusif (WIB)
        return (
            "AND l.timestamp_date_wib >= (CURRENT_DATE AT TIME ZONE 'Asia/Jakarta') - INTERVAL '6 days'",
            [],
        )

    if period == "monthly":
        # 30 hari terakhir inklusif (WIB)
        return (
            "AND l.timestamp_date_wib >= (CURRENT_DATE AT TIME ZONE 'Asia/Jakarta') - INTERVAL '29 days'",
            [],
        )

    return "", []



# ===============================
# FETCH: LEADERBOARD DATA
# ===============================
def fetch_vip_leaderboard(*, limit: int, offset: int, period: str, date: str | None):
    """
    Ambil leaderboard VIP (grouped by user).
    - 1 query
    - WIB-correct
    - index-friendly
    """

    period_filter, params = _build_period_filter(period, date)

    query = f"""
        SELECT
            u.user_id,
            u.username,
            u.first_name,
            COUNT(l.id) AS total_purchase
        FROM vip_logs l
        JOIN users u ON u.user_id = l.target_user_id
        WHERE u.abuse_flag = false
        {period_filter}
        GROUP BY u.user_id, u.username, u.first_name
        ORDER BY total_purchase DESC
        LIMIT %s OFFSET %s
    """

    log.debug(
        "[VIP_REPO] leaderboard request period=%s date=%s limit=%s offset=%s",
        period,
        date,
        limit,
        offset,
    )

    with get_dict_cursor() as (cur, _):
        cur.execute(query, params + [limit, offset])
        rows = cur.fetchall()

    log.debug(
        "[VIP_REPO] leaderboard rows=%s period=%s date=%s",
        len(rows),
        period,
        date,
    )

    return rows



# ===============================
# FETCH: TOTAL COUNT
# ===============================
def fetch_vip_total(*, period: str, date: str | None) -> int:
    """
    Hitung total transaksi VIP sesuai period (WIB).
    Digunakan untuk info agregat, bukan pagination logic.
    """

    if period == "all":
        where_clause, params = "TRUE", []

    elif period == "daily":
        if not date:
            raise ValueError("daily leaderboard requires date")
        where_clause, params = "timestamp_date_wib = %s", [date]

    elif period == "weekly":
        where_clause, params = (
            "timestamp_date_wib >= (CURRENT_DATE AT TIME ZONE 'Asia/Jakarta') - INTERVAL '6 days'",
            [],
        )

    elif period == "monthly":
        where_clause, params = (
            "timestamp_date_wib >= (CURRENT_DATE AT TIME ZONE 'Asia/Jakarta') - INTERVAL '29 days'",
            [],
        )

    else:
        where_clause, params = "TRUE", []

    query = f"""
        SELECT COUNT(*) AS total
        FROM vip_logs
        WHERE {where_clause}
    """

    log.debug(
        "[VIP_REPO] total request period=%s date=%s",
        period,
        date,
    )

    with get_dict_cursor() as (cur, _):
        cur.execute(query, params)
        total = cur.fetchone()["total"]

    log.debug(
        "[VIP_REPO] total=%s period=%s date=%s",
        total,
        period,
        date,
    )

    return total
