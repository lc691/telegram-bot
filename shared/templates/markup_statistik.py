from datetime import datetime, timedelta

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_vip_data(cursor):
    cursor.execute(
        """
        SELECT user_id, vip_expired, first_name, username
        FROM users
        WHERE is_vip = TRUE
        ORDER BY vip_expired DESC
    """
    )
    return cursor.fetchall(), "👑 **Daftar VIP Aktif:**"


def get_donation_data(cursor):
    cursor.execute(
        """
        SELECT email, amount, message, timestamp
        FROM donation_log
        WHERE type = 'vip'
        ORDER BY timestamp DESC
    """
    )
    return cursor.fetchall(), "💰 **Log Donasi VIP:**"


def generate_vip_message(data_slice):
    today = datetime.today().date()
    msg = ""
    for user_id, expired, first_name, username in data_slice:
        expired_date = expired.date() if isinstance(expired, datetime) else expired
        expired_str = expired_date.strftime("%Y-%m-%d")

        if expired_date < today:
            status = "❌"
        elif expired_date <= today + timedelta(days=3):
            status = "⚠️"
        else:
            status = "✅"

        mention = (
            f"[{first_name}](tg://user?id={user_id})" if first_name else f"`{user_id}`"
        )
        uname = f"(@{username})" if username else ""
        msg += f"{status} {mention} {uname}\n"
        msg += f"   🗓️ Hingga: **{expired_str}**\n\n"
    return msg


def generate_donation_message(data_slice):
    msg = ""
    for email, amount, message, timestamp in data_slice:
        ts_str = (
            timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(timestamp, datetime)
            else str(timestamp)
        )
        msg += f"📧 {email}\n"
        msg += f"💵 {amount}\n"
        msg += f"📜 {message or '-'}\n"
        msg += f"🕒 {ts_str}\n\n"
    return msg


def build_navigation_buttons(stat_type, page, max_page):
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ Prev", callback_data=f"vip_stats:{stat_type}:{page - 1}"
            )
        )
    if page < max_page:
        nav_buttons.append(
            InlineKeyboardButton(
                "➡️ Next", callback_data=f"vip_stats:{stat_type}:{page + 1}"
            )
        )
    return nav_buttons
