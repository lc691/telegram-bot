# bots/drac1n_bot/handlers/admin/callback/routes.py

# ==================== admin - ADD ====================
from .add.admin_add import admin_add_start
from .add.admin_add_confirmation import handle_admin_add_confirmation

# ==================== admin - LIST ====================
from .list.admin_list import start_admin_list_callback
from .list.admin_list_detail import start_admin_detail_callback
from .list.admin_list_page import start_admin_page_callback

# ==================== admin - REMOVE ====================
from .remove.admin_remove import admin_remove_start
from .remove.admin_remove_confirmation import handle_admin_remove_confirmation

# ==================== source ====================
from .source.add_source import admin_add_source_start
from .source.delete_source import admin_delete_source_list_callback
from .source.delete_source_confirm import (
    handle_delete_source_confirm,
    handle_delete_source_yes,
)
from .source.list_source import admin_source_list_callback

# ==================== admin - UPDATE ====================
from .update.admin_update import admin_update_start
from .update.admin_update_confirmation import handle_admin_update_confirmation

admin_callback_routes = {
    "admin_add_start": admin_add_start,
    "admin_remove_start": admin_remove_start,
    "admin_update_start": admin_update_start,
    "admin_list_start": start_admin_list_callback,
    "admin_add_source": admin_add_source_start,
}

admin_regex_routes = {
    r"^admin_page_\d+$": start_admin_page_callback,
    r"^admin_detail_\d+$": start_admin_detail_callback,
    r"admin_add_confirm_(yes|no)_\d+": handle_admin_add_confirmation,
    r"admin_remove_confirm_(yes|no)_\d+": handle_admin_remove_confirmation,
    r"admin_update_confirm_(yes|no)_\d+": handle_admin_update_confirmation,
    r"^admin_source_list_page_\d+$": admin_source_list_callback,
    r"^admin_delete_source_page_\d+$": admin_delete_source_list_callback,
    r"^admin_delete_confirm_\d+$": handle_delete_source_confirm,
    r"^admin_delete_yes_\d+$": handle_delete_source_yes,
}
