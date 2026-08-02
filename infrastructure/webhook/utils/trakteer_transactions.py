from typing import Optional, Tuple

from configs.logging_setup import log
from database.connection import get_dict_cursor


def is_transaction_processed(transaction_id: str) -> bool:
    """Cek apakah transaksi sudah pernah diproses."""
    with get_dict_cursor() as (cursor, _):
        cursor.execute(
            "SELECT 1 FROM trakteer_transactions WHERE transaction_id = %s",
            (transaction_id,),
        )
        row = cursor.fetchone()
        return row is not None


def save_transaction(
    transaction_id: str,
    data: dict,
    *,
    user_id: int | None = None,
    paket: str | None = None,
    source_bot: str | None = None,
    amount: int | None = None,
):
    supporter_name = data.get("supporter_name")
    supporter_message = data.get("supporter_message")
    net_amount = int(data.get("net_amount") or 0)

    if amount is None:
        amount, source = calculate_amount(data)
        log.debug(
            "[TRX_LOG] Amount recalculated source=%s amount=%s",
            source,
            amount,
        )

    try:
        with get_dict_cursor(commit=True) as (cursor, _):
            cursor.execute(
                """
                INSERT INTO trakteer_transactions (
                    transaction_id,
                    supporter_name,
                    supporter_message,
                    amount,
                    net_amount,
                    user_id,
                    paket,
                    source_bot
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (transaction_id) DO NOTHING
                RETURNING transaction_id
                """,
                (
                    transaction_id,
                    supporter_name,
                    supporter_message,
                    amount,
                    net_amount,
                    user_id,
                    paket,
                    source_bot,
                ),
            )

            inserted = cursor.fetchone()

            if inserted:
                log.info(
                    "[TRX_LOG] Transaction saved id=%s user_id=%s paket=%s bot=%s",
                    transaction_id,
                    user_id,
                    paket,
                    source_bot,
                )
            else:
                log.debug(
                    "[TRX_LOG] Duplicate transaction ignored id=%s",
                    transaction_id,
                )

    except Exception:
        log.exception(
            "[TRX_LOG] Failed to save transaction id=%s",
            transaction_id,
        )

    #     log.info(
    #     "[TRX_LOG] Transaction saved id=%s",
    #     transaction_id[:8],  # masking
    # )


def get_unit_price_from_db(default: int = 1000) -> int:
    """
    Ambil unit_price dari tabel settings di database.
    Jika gagal atau tidak valid, fallback ke default.
    """
    try:
        with get_dict_cursor() as (cursor, _):
            cursor.execute(
                "SELECT value FROM settings WHERE key = 'unit_price' LIMIT 1"
            )
            row = cursor.fetchone()

            if row and str(row.get("value", "")).isdigit():
                return int(row["value"])

            log.warning(
                "[DB] unit_price not found or invalid, fallback=%s",
                default,
            )

    except Exception:
        log.exception("[DB] Failed to fetch unit_price, fallback=%s", default)

    return default



def calculate_amount(
    data: dict, amount_override: Optional[int] = None
) -> Tuple[int, str]:
    """
    Hitung final amount dari payload Trakteer.

    Prioritas:
    1. amount_override
    2. quantity × UNIT_PRICE (dari DB)
    3. price
    4. net_amount
    5. amount_field
    6. fallback 0
    """

    def to_int(x, default=0):
        try:
            return int(x)
        except (ValueError, TypeError):
            return default

    # 1️⃣ Jika override
    if amount_override is not None:
        return to_int(amount_override), "override"

    # 2️⃣ Ambil unit price dari database
    UNIT_PRICE = get_unit_price_from_db(default=1000)

    quantity = to_int(data.get("quantity"), 0)
    price = to_int(data.get("price"))
    net_amount = to_int(data.get("net_amount"))
    amount_field = to_int(data.get("amount"))

    if quantity > 0:
        total = quantity * UNIT_PRICE
        return total, f"quantity {quantity}×{UNIT_PRICE} (db)"
    if price:
        return price, "price"
    if net_amount:
        return net_amount, "net_amount"
    if amount_field:
        return amount_field, "amount_field"

    return 0, "default"
