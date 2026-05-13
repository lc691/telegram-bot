# =====================[ EMAIL ]=====================
import smtplib

from email.mime.text import MIMEText

from config import SMTP_PASS, SMTP_USER, SPECIAL_DONORS
from configs.logging_setup import log


def send_email(to, subject, body):
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception as e:
        log.error(f"[EMAIL] Gagal kirim ke {to}: {e}")


def send_email_reply_async(email, message):
    try:
        send_email(email, "Terima kasih atas donasinya 🙏", message)
    except Exception as e:
        log.error(f"[REPLY] Gagal kirim balasan ke {email}: {e}")
