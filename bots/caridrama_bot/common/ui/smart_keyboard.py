from typing import Optional

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# =====================================================
# Atomic buttons
# =====================================================


def smart_search_button(query: str = "") -> InlineKeyboardButton:
    """
    Tombol inline search.
    Selalu aman walau query kosong.
    """
    return InlineKeyboardButton(
        text="🔍 Cari Drama",
        switch_inline_query_current_chat=query or "",
    )


def smart_request_button(
    *,
    show_id: int,
    user_id: int,
    source: str = "main",  # main | search
) -> InlineKeyboardButton:
    """
    Tombol minta admin.
    """
    return InlineKeyboardButton(
        text="📩 Minta Admin",
        callback_data=f"request:{source}:{show_id}:{user_id}",
    )


def smart_confirm_button(
    *,
    show_id: int,
    user_id: int,
) -> InlineKeyboardButton:
    """
    Tombol konfirmasi hasil match.
    """
    return InlineKeyboardButton(
        text="✅ Ya, ini judulnya",
        callback_data=f"confirm:{show_id}:{user_id}",
    )


# =====================================================
# Keyboard builder
# =====================================================


def build_keyboard(
    *,
    search_query: str = "",
    confirm_id: Optional[int] = None,
    show_id: Optional[int] = None,
    user_id: Optional[int] = None,
    allow_request: bool = False,
) -> InlineKeyboardMarkup:
    """
    Builder keyboard terpadu.

    Aturan:
    - Confirm selalu di baris sendiri
    - Search selalu muncul
    - Request hanya muncul jika allow_request=True
    """

    rows: list[list[InlineKeyboardButton]] = []

    # ==================================================
    # 1️⃣ CONFIRM ROW (opsional, baris sendiri)
    # ==================================================
    if confirm_id is not None and user_id is not None:
        rows.append(
            [
                smart_confirm_button(
                    show_id=confirm_id,
                    user_id=user_id,
                )
            ]
        )

    # ==================================================
    # 2️⃣ ACTION ROW (search + optional request)
    # ==================================================
    action_row: list[InlineKeyboardButton] = [smart_search_button(search_query)]

    if allow_request and show_id is not None and user_id is not None:
        action_row.append(
            smart_request_button(
                show_id=show_id,
                user_id=user_id,
                source="main",
            )
        )

    rows.append(action_row)

    return InlineKeyboardMarkup(rows)
