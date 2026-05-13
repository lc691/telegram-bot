from fastapi import Request

from configs.logging_setup import log


# --- Safe int converter ---
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# --- Hitung amount dengan logging ---
def calculate_amount(data: dict, vip_prices: dict | None = None) -> int:
    """
    Hitung jumlah donasi dari payload Trakteer.
    - Jika ada `net_amount`, itu prioritas
    - Kalau ada `amount`, pakai itu
    - Kalau ada `price` & `quantity`, kalikan
    """
    try:
        # 1. Cek net_amount (paling valid, setelah fee dipotong)
        if "net_amount" in data:
            try:
                return int(data["net_amount"])
            except (TypeError, ValueError):
                pass

        # 2. Cek amount (format lain Trakteer)
        if "amount" in data:
            try:
                return int(data["amount"])
            except (TypeError, ValueError):
                pass

        # 3. Hitung dari price * quantity
        quantity = int(data.get("quantity", 1) or 1)
        unit_price = int(data.get("price", 0) or 0)
        total_amount = unit_price * quantity

        return total_amount

    except Exception as e:

        log.warning(f"[CALC] ❌ Gagal hitung amount: {e}, payload={data}")
        return 0


def extract_donor_identity(data: dict) -> str | None:
    """
    Cari identitas donatur dari payload Trakteer.
    Urutan fallback:
    1. supporter_message (user_id Telegram, kalau ada)
    2. supporter_name / supporter_id
    3. email
    """
    # 1. Parsing dari supporter_message
    msg = data.get("supporter_message", "")
    if msg and "daftar_short_" in msg:
        try:
            parts = msg.split("_")
            user_id = int(parts[2])  # contoh: daftar_short_897426027_1hari
            return str(user_id)
        except Exception:
            pass

    # 2. supporter_name / supporter_id
    donor = data.get("supporter_name") or data.get("supporter_id")
    if donor:
        return str(donor).strip()

    # 3. email
    donor = data.get("email")
    if donor:
        return str(donor).strip()

    return None


# --- Parsing payload (JSON / Form) ---
async def parse_payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        return await request.json()

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return dict(form)

    raise ValueError("Unsupported content-type")
