from common.utils.admin_state_manager import AdminStateManager
from common.utils.vip_state_manager import VipStateManager

# Daftar command yang digunakan untuk membatalkan atau mereset state aktif
CANCEL_COMMANDS = {"/dashboard", "/batal", "/cancel"}


def should_cancel_state_on_command(text: str) -> bool:
    """
    Cek apakah teks pesan merupakan salah satu command untuk membatalkan state.
    """
    return text.strip().lower() in CANCEL_COMMANDS


def cancel_all_states(user_id: int, source_bot: str = "drac1n") -> None:
    """
    Reset atau hapus semua state yang terkait dengan user_id dan bot tertentu.
    """
    AdminStateManager(user_id, source_bot=source_bot).clear()
    VipStateManager(user_id, source_bot=source_bot).clear()
