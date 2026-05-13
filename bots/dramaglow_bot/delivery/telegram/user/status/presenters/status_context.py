from ..usecases.get_status_data import get_status_data
from ...common.display_name import get_display_name


def build_status_context(
    *,
    user_id: int,
    user,
    admin_cache,
) -> dict:
    """
    Context builder untuk UI status.
    Tidak ada logic bisnis.
    """

    lang_code = getattr(user, "language_code", "id") or "id"
    is_admin = admin_cache.is_admin(user_id)

    return {
        "user_id": user_id,
        "user": user,
        "username": get_display_name(user),
        "lang_code": lang_code,
        "is_admin": is_admin,
        "status_data": get_status_data(user_id) or {},
    }
