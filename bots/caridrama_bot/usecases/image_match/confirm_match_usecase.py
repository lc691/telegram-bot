from ...domain.show_repository import get_show_with_latest_file_full


def confirm_match_usecase(show_id: int) -> dict | None:
    return get_show_with_latest_file_full(show_id)
