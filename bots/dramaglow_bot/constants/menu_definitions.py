from bots.dramaglow_bot.keyboard.admin_tools import generate_admin_tools_markup
from bots.dramaglow_bot.keyboard.dashboard_tools import generate_dashboard_markup
from bots.dramaglow_bot.keyboard.source_tools import generate_source_markup
from bots.dramaglow_bot.keyboard.stats_tools import generate_stats_markup
from bots.dramaglow_bot.keyboard.vip_tools import generate_vip_menus_markup
from bots.dramaglow_bot.utils.channel_markup_factory import generate_channel_markup

menus = {
    "admin_tools_menu": {
        "title": "👨‍💼 **Admin Tools**\nKelola pengguna dan akses admin.",
        "markup": generate_admin_tools_markup,
    },
    "vip_tools_menu": {
        "title": "🌟 **VIP Tools**\nAtur fitur eksklusif untuk pengguna VIP.",
        "markup": generate_vip_menus_markup,
    },
    "channel_menu": {
        "title": "📱 **Channel Manager**\nKelola saluran dan grup terhubung.",
        "markup": generate_channel_markup,
    },
    "request_menu": {
        "title": "🎬 **Source Film**\nKelola sumber film yang tersedia.",
        "markup": generate_source_markup,
    },
    "show_stats": {
        "title": "📈 **Statistik Penayangan**\nReport data stats.",
        "markup": generate_stats_markup,
    },
    "dashboard": {
        "title": "📊 **Dashboard Utama**\nNavigasi utama untuk semua fitur bot.",
        "markup": generate_dashboard_markup,
    },
}
