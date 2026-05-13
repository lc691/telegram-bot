from db.connect import get_dict_cursor
from bots.drac1n_bot.services.files.repository import extract_part_number

BATCH_SIZE = 500
PAID_FROM_EP = 21


def migrate_files_is_paid():
    offset = 0
    updated = 0

    while True:
        with get_dict_cursor() as (cur, _):
            cur.execute(
                """
                SELECT id, file_name, is_paid
                FROM files
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (BATCH_SIZE, offset),
            )
            rows = cur.fetchall()

        if not rows:
            break

        updates = []

        for row in rows:
            start_ep = extract_part_number(row["file_name"])
            should_paid = start_ep >= PAID_FROM_EP

            if row["is_paid"] != should_paid:
                updates.append((should_paid, row["id"]))

        if updates:
            with get_dict_cursor(commit=True) as (cur, _):
                cur.executemany(
                    "UPDATE files SET is_paid = %s WHERE id = %s",
                    updates,
                )
            updated += len(updates)

        offset += BATCH_SIZE

    print(f"Migration done. Updated rows: {updated}")


if __name__ == "__main__":
    migrate_files_is_paid()
