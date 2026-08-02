from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_user_list_text(users, offset, total, source):
    if not users:
        return f"🚫 Tidak ada pengguna ditemukan di `{source}`."

    lines = [
        f"📋 **Daftar Pengguna `{source}`**",
        f"👥 Total: {total} pengguna\n",
        f"(Menampilkan dari #{offset + 1})\n",
    ]
    for i, user in enumerate(users, start=offset + 1):
        uid, name, uname, is_vip, expired = user
        tag = f"@{uname}" if uname else "-"
        status = "✅ VIP" if is_vip else "🆓 Free"
        exp = f" (sampai {expired.strftime('%Y-%m-%d')})" if expired else ""
        lines.append(f"**{i}.** {uid} — {name} ({tag})\n   {status}{exp}")
    return "\n".join(lines)


def generate_user_list_keyboard(offset, limit, total, vip, search, source):
    buttons = []
    query_base = f"vip={'true' if vip else 'false'}&source={source}"
    if search:
        query_base += f"&search={search}"

    prev_offset = max(0, offset - limit)
    next_offset = offset + limit

    source_switch_row = [
        InlineKeyboardButton("📚 UTBK", callback_data="list_users?source=utbk"),
        InlineKeyboardButton("🧪 Drac1n", callback_data="list_users?source=drac1n"),
    ]

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

    filter_label = "✅ Semua" if vip else "⭐ VIP"
    filter_row = [
        InlineKeyboardButton(
            filter_label,
            callback_data=f"list_users?{query_base}&vip={'false' if vip else 'true'}",
        )
    ]

    buttons.append(source_switch_row)
    buttons.append(filter_row)
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="dashboard")])
    return InlineKeyboardMarkup(buttons)
