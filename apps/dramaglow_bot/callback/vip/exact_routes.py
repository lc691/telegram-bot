from apps.dramaglow_bot.handlers.vip.add_vip.vip_add import vip_add_start
from apps.dramaglow_bot.handlers.vip.delete_vip.vip_delete import vip_delete_start
from apps.dramaglow_bot.handlers.vip.extend_vip.vip_add_extend import vip_extend_start
from apps.dramaglow_bot.handlers.vip.reset_vip.show_vip_reset_menu import (
    show_vip_reset_menu,
)
from apps.dramaglow_bot.handlers.vip.reset_vip.vip_reset import vip_reset_start
from apps.dramaglow_bot.handlers.vip.reset_vip.vip_reset_all import vip_reset_all_start

vip_exact_routes = {
    "vip_add_start": vip_add_start,
    "vip_extend_start": vip_extend_start,
    "vip_delete_start": vip_delete_start,
    "vip_reset_menu": show_vip_reset_menu,
    "vip_reset_start": vip_reset_start,
    "vip_reset_all_confirm": vip_reset_all_start,
}
