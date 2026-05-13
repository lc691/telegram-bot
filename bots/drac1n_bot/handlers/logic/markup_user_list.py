from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_user_list_keyboard(offset, limit, total, vip, search):
    buttons = []
    query_base = f"vip={'true' if vip else 'false'}"
    if search:
        query_base += f"&search={search}"

    prev_offset = max(0, offset - limit)
    next_offset = offset + limit

    nav_row = []
    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(
                "⬅️ Prev", callback_data=f"list_users?{query_base}&offset={prev_offset}"
            )
        )
    if next_offset < total:
        nav_row.append(
            InlineKeyboardButton(
                "Next ➡️", callback_data=f"list_users?{query_base}&offset={next_offset}"
            )
        )

    buttons.append(
        [InlineKeyboardButton("⭐ VIP", callback_data="list_users?vip=true")]
    )
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)
