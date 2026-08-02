# db/image_learning.py
from typing import Optional

from configs.logging_setup import log
from database.connection import get_dict_cursor


def log_match_stat(user_id: Optional[int], show_id: Optional[int], outcome: str, similarity: Optional[float]):
    try:
        with get_dict_cursor() as (cur, _):
            cur.execute(
                """
                INSERT INTO image_match_stats (show_id, user_id, outcome, similarity, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (show_id, user_id, outcome, similarity),
            )
    except Exception:
        log.exception("[STATS] Failed to log image_match_stats")

def create_show_request(user_id: int, image_path: str) -> Optional[int]:
    try:
        with get_dict_cursor() as (cur, _):
            cur.execute(
                """
                INSERT INTO show_requests (user_id, image_path, created_at, status)
                VALUES (%s, %s, NOW(), 'requested')
                RETURNING id
                """,
                (user_id, image_path),
            )
            row = cur.fetchone()
            return row["id"] if row else None
    except Exception:
        log.exception("[REQUEST] Failed to create show_request")
        return None

def get_request_by_id(request_id: int):
    try:
        with get_dict_cursor() as (cur, _):
            cur.execute("SELECT * FROM show_requests WHERE id = %s", (request_id,))
            return cur.fetchone()
    except Exception:
        log.exception("[REQUEST] Failed to get_request_by_id")
        return None

def mark_request_processed(request_id: int, status: str, processed_by: Optional[int] = None):
    try:
        with get_dict_cursor() as (cur, _):
            cur.execute(
                """
                UPDATE show_requests
                SET status = %s, processed_by = %s, processed_at = NOW()
                WHERE id = %s
                """,
                (status, processed_by, request_id),
            )
    except Exception:
        log.exception("[REQUEST] Failed to mark_request_processed")

def record_approved_request(request_id: int, show_id: int):
    try:
        with get_dict_cursor() as (cur, _):
            cur.execute(
                """
                INSERT INTO approved_requests (request_id, show_id, embedding_add_at)
                VALUES (%s, %s, NOW())
                """,
                (request_id, show_id),
            )
    except Exception:
        log.exception("[LEARN] Failed to record approved request")
