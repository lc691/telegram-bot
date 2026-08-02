from shared.utils.search_state_manager import UserSearchStateManager
from shared.utils.admin_cache import admin_cache

class SearchEntryResult:
    def __init__(self, *, is_admin: bool, display_name: str):
        self.is_admin = is_admin
        self.display_name = display_name


def run_search_entry_flow(*, user) -> SearchEntryResult:
    user_id = user.id
    first_name = user.first_name or ""
    username = user.username or ""
    display_name = username or first_name or "Teman"

    # Admin → menu utama
    if admin_cache.is_admin(user_id):
        return SearchEntryResult(
            is_admin=True,
            display_name=display_name,
        )

    # User biasa → set FSM
    fsm = UserSearchStateManager(user_id)
    fsm.clear_all()
    fsm.set_step("awaiting_input")

    return SearchEntryResult(
        is_admin=False,
        display_name=display_name,
    )
