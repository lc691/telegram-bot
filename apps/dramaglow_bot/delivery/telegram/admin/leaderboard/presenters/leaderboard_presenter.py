from .leaderboard_formatter import format_vip_leaderboard
from .leaderboard_keyboard import leaderboard_keyboard
from ....user.common.konstanta import PAGE_SIZE


def build_leaderboard_text(*, data, period, page, total, date: str | None):
    """
    Build text leaderboard VIP.
    Presenter murni: tidak ada I/O, tidak ada logging.
    """

    # Defensive default (tidak mengubah perilaku bisnis)
    if page < 1:
        page = 1

    return format_vip_leaderboard(
        data=data,
        period=period,
        page=page,
        page_size=PAGE_SIZE,
        total_count=total,
        date=date,
    )


def build_leaderboard_keyboard(*, period, page, date: str | None):
    """
    Build keyboard leaderboard VIP.
    """

    # Defensive default
    if page < 1:
        page = 1

    return leaderboard_keyboard(
        period=period,
        page=page,
        date=date,
    )
