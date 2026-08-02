from db.connect import get_dict_cursor


class FeedbackRepository:
    """
    Repository Feedback DCSTV
    """

    # =====================================================
    # TICKET
    # =====================================================

    def create_ticket(
        self,
        *,
        ticket_no: str,
        user_id: int,
        category: str,
        title: str | None,
        description: str,
        status: str = "pending",
    ):

        with get_dict_cursor(commit=True) as (cur, conn):

            cur.execute(
                """
                INSERT INTO feedback_ticket (
                    ticket_no,
                    user_id,
                    category,
                    title,
                    description,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING *
                """,
                (
                    ticket_no,
                    user_id,
                    category,
                    title,
                    description,
                    status,
                ),
            )

            return cur.fetchone()

    def get_ticket_by_id(
        self,
        ticket_id: int,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT *
                FROM feedback_ticket
                WHERE id = %s
                """,
                (ticket_id,),
            )

            return cur.fetchone()

    def get_ticket_by_no(
        self,
        ticket_no: str,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT *
                FROM feedback_ticket
                WHERE ticket_no = %s
                """,
                (ticket_no,),
            )

            return cur.fetchone()

    def get_user_tickets(
        self,
        user_id: int,
        limit: int = 10,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT *
                FROM feedback_ticket
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (
                    user_id,
                    limit,
                ),
            )

            return cur.fetchall()

    def get_latest_tickets(
        self,
        limit: int = 20,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT *
                FROM feedback_ticket
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )

            return cur.fetchall()

    def get_pending_tickets(
        self,
        limit: int = 50,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT *
                FROM feedback_ticket
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT %s
                """,
                (limit,),
            )

            return cur.fetchall()

    def get_tickets_by_status(
        self,
        *,
        status: str,
        limit: int = 50,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT *
                FROM feedback_ticket
                WHERE status = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (
                    status,
                    limit,
                ),
            )

            return cur.fetchall()

    def update_status(
        self,
        *,
        ticket_no: str,
        status: str,
        admin_note: str | None = None,
    ):

        with get_dict_cursor(commit=True) as (cur, conn):

            cur.execute(
                """
                UPDATE feedback_ticket
                SET
                    status = %s,
                    admin_note = %s,
                    updated_at = NOW()
                WHERE ticket_no = %s
                RETURNING *
                """,
                (
                    status,
                    admin_note,
                    ticket_no,
                ),
            )

            return cur.fetchone()

    def close_ticket(
        self,
        *,
        ticket_no: str,
        status: str = "resolved",
        admin_note: str | None = None,
    ):

        with get_dict_cursor(commit=True) as (cur, conn):

            cur.execute(
                """
                UPDATE feedback_ticket
                SET
                    status = %s,
                    admin_note = %s,
                    resolved_at = NOW(),
                    updated_at = NOW()
                WHERE ticket_no = %s
                RETURNING *
                """,
                (
                    status,
                    admin_note,
                    ticket_no,
                ),
            )

            return cur.fetchone()

    # =====================================================
    # STATISTICS
    # =====================================================

    def count_by_category(
        self,
        category: str,
    ) -> int:

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM feedback_ticket
                WHERE category = %s
                """,
                (category,),
            )

            row = cur.fetchone()

            return row["total"] if row else 0

    def count_by_status(
        self,
        status: str,
    ) -> int:

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM feedback_ticket
                WHERE status = %s
                """,
                (status,),
            )

            row = cur.fetchone()

            return row["total"] if row else 0

    # =====================================================
    # RATING
    # =====================================================

    def create_rating(
        self,
        *,
        user_id: int,
        rating: int,
    ):

        with get_dict_cursor(commit=True) as (cur, conn):

            cur.execute(
                """
                INSERT INTO feedback_rating (
                    user_id,
                    rating
                )
                VALUES (
                    %s,
                    %s
                )
                RETURNING *
                """,
                (
                    user_id,
                    rating,
                ),
            )

            return cur.fetchone()

    def get_average_rating(
        self,
    ) -> float:

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT COALESCE(
                    ROUND(AVG(rating)::numeric, 2),
                    0
                ) AS avg_rating
                FROM feedback_rating
                """
            )

            row = cur.fetchone()

            return float(row["avg_rating"] or 0)

    def get_total_rating(
        self,
    ) -> int:

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM feedback_rating
                """
            )

            row = cur.fetchone()

            return row["total"] if row else 0

    def get_rating_distribution(
        self,
    ):

        with get_dict_cursor() as (cur, conn):

            cur.execute(
                """
                SELECT
                    rating,
                    COUNT(*) AS total
                FROM feedback_rating
                GROUP BY rating
                ORDER BY rating DESC
                """
            )

            return cur.fetchall()


feedback_repository = FeedbackRepository()