import hashlib

from datetime import datetime, timedelta

from configs.logging_setup import log


# ============================
#  ANTI-ABUSE ENGINE
# ============================
class AntiAbuse:
    def __init__(self, cursor):
        self.cursor = cursor

    # ---------------------------------------------------------
    # Get last IP & Device (if logging enabled)
    # ---------------------------------------------------------
    def get_recent_access(self, user_id):
        try:
            self.cursor.execute("""
                SELECT ip_address, device_id 
                FROM user_access_logs
                WHERE user_id = %s
                ORDER BY id DESC LIMIT 1
            """, (user_id,))
            return self.cursor.fetchone() or (None, None)
        except:
            return (None, None)

    # ---------------------------------------------------------
    # Check common IP usage
    # ---------------------------------------------------------
    def same_ip_users(self, ip):
        self.cursor.execute("""
            SELECT user_id 
            FROM user_access_logs
            WHERE ip_address = %s
            GROUP BY user_id
        """, (ip,))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows] if rows else []

    # ---------------------------------------------------------
    # Check device reuse
    # ---------------------------------------------------------
    def same_device_users(self, device_id):
        self.cursor.execute("""
            SELECT user_id 
            FROM user_access_logs
            WHERE device_id = %s
            GROUP BY user_id
        """, (device_id,))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows] if rows else []

    # ---------------------------------------------------------
    # Behavioral patterns
    # ---------------------------------------------------------
    def check_referral_anomalies(self, user_id):
        score = 0

        # 1. referral terlalu cepat bertambah (spam)
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM users 
            WHERE referrer_user_id = %s 
              AND created_at > NOW() - INTERVAL '1 hour'
        """, (user_id,))
        hourly_refs = self.cursor.fetchone()[0]

        if hourly_refs >= 5:
            score += 40
        elif hourly_refs >= 3:
            score += 25

        # 2. referral hanya 1 device/IP → indikasi self-referral
        self.cursor.execute("""
            SELECT referred_user_id,count(*) 
            FROM affiliate_commission_logs
            WHERE referrer_user_id = %s
            GROUP BY referred_user_id
        """, (user_id,))
        uniq = self.cursor.fetchall()
        if uniq and len(uniq) <= 1:
            score += 20

        return score

    # ---------------------------------------------------------
    # Main scoring
    # ---------------------------------------------------------
    def calculate_score(self, user_id):
        score = 0

        ip, device = self.get_recent_access(user_id)

        # A) SAME IP
        if ip:
            same_ip_users = self.same_ip_users(ip)
            if len(same_ip_users) >= 3:
                score += 50
            elif len(same_ip_users) >= 2:
                score += 25

        # B) SAME DEVICE
        if device:
            same_dev_users = self.same_device_users(device)
            if len(same_dev_users) >= 3:
                score += 50
            elif len(same_dev_users) >= 2:
                score += 25

        # C) BEHAVIORAL
        score += self.check_referral_anomalies(user_id)

        return min(score, 100)

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------
    def detect(self, user_id):
        score = self.calculate_score(user_id)

        if score >= 80:
            return "ABUSE", score
        elif score >= 60:
            return "SUSPECT", score
        else:
            return "OK", score
