from configs.logging_setup import log
from database.connection import get_db_cursor

# ========================== #
# === TABEL UTAMA: USERS === #
# ========================== #


def ensure_users_table():
    """Tabel utama untuk menyimpan data user"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS public.users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    is_vip BOOLEAN DEFAULT FALSE,
                    vip_expired TIMESTAMPTZ,
                    free_access_count INTEGER DEFAULT 0,
                    last_free_access TIMESTAMPTZ,
                    vip_start TIMESTAMPTZ,
                    vip_purchases INTEGER DEFAULT 0,
                    vip_reminded BOOLEAN DEFAULT FALSE,
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    first_name TEXT,
                    username TEXT,
                    vip_expiry_notified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE UNIQUE INDEX IF NOT EXISTS unique_user_id
                    ON public.users (user_id);

                CREATE UNIQUE INDEX IF NOT EXISTS users_referral_code_key
                    ON public.users (referral_code);

                CREATE TRIGGER set_updated_at
                    BEFORE UPDATE ON users
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                """
            )
            conn.commit()
            log.info("✅ Tabel 'users' sudah tersedia atau berhasil dibuat.")
    except Exception as e:
        log.error("❌ Gagal membuat tabel 'users': %s", e, exc_info=True)


def ensure_user_exists(user_id: int):
    """Memastikan user sudah ada di tabel users"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                INSERT INTO users (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
            """,
                (user_id,),
            )
            conn.commit()
            log.info(f"[ENSURE USER] Memastikan user_id={user_id} ada di tabel users.")
    except Exception as e:
        log.error(f"[ENSURE USER] Gagal memastikan user ada: {e}", exc_info=True)


# ========================== #
# === FILE MANAGEMENT     === #
# ========================== #


def ensure_files_table():
    """Membuat tabel 'files' jika belum ada, sesuai skema PostgreSQL."""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id SERIAL PRIMARY KEY,
                    file_id TEXT UNIQUE,
                    file_name TEXT,
                    file_type TEXT,
                    file_size BIGINT,
                    message_id INTEGER,
                    free_hash TEXT UNIQUE,
                    paid_hash TEXT UNIQUE,
                    channel_username TEXT,
                    main_title TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (file_name, file_size, file_type)
                )
                """
            )
            conn.commit()
    except Exception as e:
        log.error(f"Gagal membuat tabel files: {e}")


def ensure_file_views_table():
    """
    Membuat tabel file_views jika belum ada.
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_views (
                    id SERIAL PRIMARY KEY,
                    hash TEXT UNIQUE,
                    views INTEGER DEFAULT 0
                )
            """
            )
            conn.commit()
            log.info("✅ Tabel file_views berhasil dipastikan ada.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel file_views: {e}", exc_info=True)


def ensure_file_upload_log_table():
    """Log pengunggahan file"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_upload_log (
                    id SERIAL PRIMARY KEY,
                    file_id TEXT,
                    uploader TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS unique_upload_log ON file_upload_log (file_id, uploader);
            """
            )
            conn.commit()
            log.info(
                "Tabel file_upload_log dan index unik berhasil dibuat atau sudah ada."
            )
    except Exception as e:
        log.error(f"Gagal membuat tabel file_upload_log atau index unik: {e}")


def ensure_video_stats_table():
    """Statistik pemutaran video"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS video_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    file_id TEXT,
                    play_count INTEGER DEFAULT 0,
                    last_played TIMESTAMP,
                    UNIQUE(user_id, file_id)
                );
            """
            )
            conn.commit()
    except Exception as e:
        log.error(f"Gagal membuat tabel video_stats: {e}")


# ========================== #
# === VIP MANAGEMENT      === #
# ========================== #


def ensure_vip_logs_table():
    """Log transaksi VIP"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS public.vip_logs (
                    id SERIAL PRIMARY KEY,
                    target_user_id BIGINT NOT NULL,
                    admin_user_id BIGINT,
                    paket TEXT,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    durasi_hari INTEGER,
                    is_extend BOOLEAN DEFAULT FALSE,
                    expired_baru TIMESTAMPTZ,
                    keterangan TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    is_notified BOOLEAN NOT NULL DEFAULT FALSE,
                    source_bot TEXT DEFAULT 'dracln',
                    source_bot TEXT DEFAULT 'dracln',
                    timestamp_date DATE GENERATED ALWAYS AS (
                        (timestamp AT TIME ZONE 'UTC')::date
                    ) STORED
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_vip_log_unique_daily
                    ON public.vip_logs (target_user_id, paket, timestamp_date)
                    WHERE is_notified = FALSE;

                CREATE INDEX IF NOT EXISTS idx_vip_logs_not_notified
                    ON public.vip_logs (target_user_id, paket, "timestamp")
                    WHERE is_notified = FALSE;
            """
            )
            conn.commit()
            log.info("✅ Tabel 'vip_logs' sudah tersedia atau berhasil dibuat.")
    except Exception as e:
        log.error("❌ Gagal membuat tabel 'vip_logs': %s", e, exc_info=True)


# ========================== #
# === ADMIN MANAGEMENT    === #
# ========================== #


def ensure_admins_table():
    """Tabel master data admin"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_admins_user_id ON admins(user_id);
            """
            )
            conn.commit()
            # log.info("✅ Tabel `admins` berhasil dipastikan (GLOBAL).")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel admins: {e}", exc_info=True)


def ensure_admin_state_table():
    """Membuat tabel state langkah aktif admin"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_state (
                    admin_id BIGINT PRIMARY KEY,
                    step TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_admin_state_admin_id ON admin_state(admin_id);
                """
            )
            conn.commit()
            log.info("✅ Tabel `admin_state` berhasil dipastikan.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel admin_state: {e}", exc_info=True)


def ensure_admin_temp_state_table():
    """Membuat tabel penyimpanan sementara untuk input bertahap admin"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_temp_state (
                    admin_id BIGINT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (admin_id, key)
                );
                CREATE INDEX IF NOT EXISTS idx_admin_temp_admin_id ON admin_temp_state(admin_id);
                """
            )
            conn.commit()
            log.info("✅ Tabel `admin_temp_state` berhasil dipastikan.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel admin_temp_state: {e}", exc_info=True)


# ========================== #
# === DONASI / PEMBAYARAN === #
# ========================== #


def ensure_donasi_token_table():
    """Token donasi aktif per user & metode"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS donasi_token (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    token TEXT NOT NULL,
                    metode TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, metode)
                )
            """
            )
            conn.commit()
    except Exception as e:
        log.error(f"Gagal membuat tabel donasi_token: {e}")


def ensure_pending_donations_table():
    """Donasi yang sedang diproses"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_donations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    token TEXT UNIQUE,
                    method TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
    except Exception as e:
        log.error(f"Gagal membuat tabel pending_donations: {e}")


from configs.logging_setup import log
from database.connection import get_db_cursor


def ensure_donation_log_table():
    """Pastikan tabel donation_log lengkap dengan kolom: status, source_bot, confirmed_at."""
    try:
        with get_db_cursor() as (cursor, conn):
            # Buat tabel jika belum ada
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS donation_log (
                    id SERIAL PRIMARY KEY,
                    email TEXT,
                    amount INTEGER,
                    message TEXT,
                    user_id BIGINT,
                    paket TEXT,
                    type VARCHAR(20),
                    is_notified BOOLEAN NOT NULL DEFAULT FALSE,
                    source_bot TEXT NOT NULL DEFAULT 'drac',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending'
                );
                """
            )

            # Tambahkan kolom 'status' jika belum ada
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='donation_log' AND column_name='status'
                    ) THEN
                        ALTER TABLE donation_log
                        ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
                    END IF;
                END
                $$;
                """
            )

            # Tambahkan kolom 'source_bot' jika belum ada
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='donation_log' AND column_name='source_bot'
                    ) THEN
                        ALTER TABLE donation_log
                        ADD COLUMN source_bot TEXT NOT NULL DEFAULT 'drac';
                    END IF;
                END
                $$;
                """
            )

            # Tambahkan kolom 'confirmed_at' jika belum ada
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='donation_log' AND column_name='confirmed_at'
                    ) THEN
                        ALTER TABLE donation_log
                        ADD COLUMN confirmed_at TIMESTAMP;
                    END IF;
                END
                $$;
                """
            )

            # Merubah kolom drac-> drac1n
            cursor.execute(
                """
                UPDATE donation_log
                SET source_bot = 'drac1n'
                WHERE source_bot = 'drac';
                """
            )

            conn.commit()
            log.info("✅ Tabel 'donation_log' berhasil dicek dan diperbarui.")

    except Exception as e:
        log.error(
            f"❌ Gagal membuat/memperbarui tabel donation_log: {e}", exc_info=True
        )


# ========================== #
# === FORWARD MESSAGE     === #
# ========================== #


def ensure_forward_messages_table():
    """Menyimpan pesan yang diteruskan"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS forward_messages (
                    id SERIAL PRIMARY KEY,
                    original_chat_id BIGINT,
                    original_message_id BIGINT,
                    forward_from_user_id BIGINT,
                    forward_date TIMESTAMP,
                    forward_text TEXT,
                    media_file_id TEXT,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(original_chat_id, original_message_id)
                )
            """
            )
            conn.commit()
    except Exception as e:
        log.error(f"Gagal membuat tabel forward_messages: {e}")


# ========================== #
# === BROADCAST MESSAGE   === #
# ========================== #


def ensure_broadcast_logs_table():
    """Log pengiriman broadcast"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS broadcast_logs (
                    id SERIAL PRIMARY KEY,
                    broadcast_user_id BIGINT,
                    target_user_id BIGINT,
                    success BOOLEAN,
                    error_msg TEXT,
                    sent_at TIMESTAMP DEFAULT NOW()
                )
            """
            )
            conn.commit()
            log.info("✅ Tabel broadcast_logs siap digunakan.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel broadcast_logs: {e}")


# ========================== #
# === MASTER CHANNEL      === #
# ========================== #


def ensure_user_channel_check_table():
    """Status join user ke channel"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_channel_check (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    channel_username TEXT,
                    is_joined BOOLEAN,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'user_channel_check' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'user_channel_check': {e}")


def ensure_adding_channel_users_table():
    """Tabel untuk melacak user yang sedang dalam proses menambahkan channel"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS adding_channel_users (
                    user_id BIGINT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()
            log.info("✅ Tabel 'adding_channel_users' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'adding_channel_users': {e}")


def ensure_required_channels_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS required_channels (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    added_by TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'required_channels' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'required_channels': {e}")


# ================================== #
# === MASTER REQUEST SOURCE      === #
# ================================== #
def ensure_request_sources_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS request_sources (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,    -- misalnya: 'a', 'b', 'c'
                label TEXT NOT NULL           -- misalnya: 'Source A', 'Source B'
            );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'request_sources' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'request_sources': {e}")


# ========================== #
# === MASTER FUNCTION     === #
# ========================== #


def ensure_all_tables():
    """Menjalankan semua fungsi pembuatan tabel"""
    ensure_users_table()
    ensure_user_channel_check_table()
    ensure_adding_channel_users_table()
    ensure_required_channels_table()
    ensure_files_table()
    ensure_file_upload_log_table()
    ensure_video_stats_table()
    ensure_vip_logs_table()
    ensure_admins_table()
    ensure_admin_state_table()
    ensure_admin_temp_state_table()
    ensure_donasi_token_table()
    ensure_pending_donations_table()
    ensure_donation_log_table()
    ensure_forward_messages_table()
    ensure_broadcast_logs_table()
    ensure_request_sources_table()


def execute_query(query: str):
    """Fungsi umum untuk eksekusi query bebas"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(query)
            conn.commit()
    except Exception as e:
        log.error(f"Gagal eksekusi query: {e}")
