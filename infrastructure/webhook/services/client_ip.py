from fastapi import Request
import ipaddress


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_real_client_ip(request: Request) -> str:
    headers = request.headers

    # =================================================
    # 1. CLOUDFLARE (PALING VALID kalau memang pakai CF)
    # =================================================
    cf_ip = headers.get("cf-connecting-ip")
    cf_ray = headers.get("cf-ray")  # indikator request via Cloudflare

    if cf_ip and cf_ray and is_valid_ip(cf_ip):
        return cf_ip

    # =================================================
    # 2. X-FORWARDED-FOR (hanya fallback)
    # =================================================
    xff = headers.get("x-forwarded-for")
    if xff:
        ip_list = [ip.strip() for ip in xff.split(",")]

        for ip in ip_list:
            if is_valid_ip(ip):
                return ip  # ambil IP valid pertama

    # =================================================
    # 3. DIRECT CONNECTION
    # =================================================
    if request.client and is_valid_ip(request.client.host):
        return request.client.host

    return "unknown"
