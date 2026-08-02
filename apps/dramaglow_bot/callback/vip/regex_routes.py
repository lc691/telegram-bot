import re

from apps.dramaglow_bot.handlers.vip.add_vip.vip_add_confirmation import (
    handle_vip_add_confirmation,
)
from apps.dramaglow_bot.handlers.vip.add_vip.vip_package_selection import (
    handle_vip_package_selection,
)
from apps.dramaglow_bot.handlers.vip.delete_vip.vip_delete import (
    handle_vip_delete_confirmation,
    handle_vip_delete_selection,
)
from apps.dramaglow_bot.handlers.vip.extend_vip.vip_add_extend import (
    handle_vip_extend_confirmation,
    handle_vip_extend_page,
    handle_vip_extend_user_selection,
)
from apps.dramaglow_bot.handlers.vip.reset_vip.vip_reset import (
    handle_vip_reset_selection,
)
from apps.dramaglow_bot.handlers.vip.reset_vip.vip_reset_all import (
    handle_vip_reset_all_step,
)
from apps.dramaglow_bot.handlers.vip.reset_vip.vip_reset_confirmation import (
    handle_vip_reset_confirmation,
)
from apps.dramaglow_bot.handlers.vip.vip_stats import (
    handle_vip_stats,
    register_vip_stats_handler,
)

vip_regex_routes = {
    re.compile(r"^vip_extend_page:(\d+):(glow|drac1n|utbk)$"): handle_vip_extend_page,
    re.compile(r"^vip_extend_user:(\d+)$"): handle_vip_extend_user_selection,
    re.compile(r"^vip_extend_confirm_(yes|no)$"): handle_vip_extend_confirmation,
    re.compile(r"^vip_add_[a-z0-9]+$"): handle_vip_package_selection,
    re.compile(r"^vip_add_confirm_(yes|no)$"): handle_vip_add_confirmation,
    re.compile(r"^vip_extend_(?!confirm_)[a-z0-9]+$"): handle_vip_package_selection,
    re.compile(r"^vip_delete_confirm_(yes|no)$"): handle_vip_delete_confirmation,
    re.compile(r"^vip_delete_select_\d+$"): handle_vip_delete_selection,
    re.compile(r"^vip_reset_confirm_yes$"): handle_vip_reset_confirmation,
    re.compile(
        r"^vip_reset_all_confirm_yes:(glow|drac1n|utbk)$"
    ): handle_vip_reset_all_step,
    re.compile(r"^vip_reset_select_\d+$"): handle_vip_reset_selection,
    re.compile(
        r"^vip_stats:(glow|drac1n|utbk|vip|donation):(vip(?:-\w+)?|donation):\d+$"
    ): handle_vip_stats,
}

# Tambahan dari register dinamis
pattern_str, handler = register_vip_stats_handler()
vip_regex_routes[re.compile(pattern_str)] = handler
