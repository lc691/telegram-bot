# ensure_tables.py
from configs.logging_setup import log
from db.connect import get_db_cursor

# ========================== #
# === MASTER UTBK     === #
# ========================== #


def ensure_users_utbk_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users_utbk (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    is_vip BOOLEAN DEFAULT FALSE,
                    vip_start TIMESTAMPTZ,
                    vip_expired TIMESTAMPTZ,
                    vip_purchases INTEGER DEFAULT 0,
                    free_access_count INTEGER DEFAULT 0,
                    vip_reminded BOOLEAN DEFAULT FALSE,
                    last_free_access TIMESTAMPTZ,
                    first_name TEXT NOT NULL,
                    username TEXT,
                    total_score INTEGER DEFAULT 0,
                    total_correct INTEGER DEFAULT 0,
                    last_answered_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """
            )

            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_users_utbk_updated_at'
                    ) THEN
                        CREATE TRIGGER trigger_users_utbk_updated_at
                        BEFORE UPDATE ON users_utbk
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                    END IF;
                END;
                $$;
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_utbk_vip_status ON users_utbk(is_vip);
            """
            )

            conn.commit()
            log.info("✅ Tabel 'users_utbk' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'users_utbk': {e}")


def ensure_questions_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id SERIAL PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    option_a TEXT NOT NULL,
                    option_b TEXT NOT NULL,
                    option_c TEXT NOT NULL,
                    option_d TEXT NOT NULL,
                    option_e TEXT NOT NULL,
                    correct_option CHAR(1) NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D', 'E')),
                    category TEXT,
                    sub_category TEXT,
                    explanation TEXT,
                    difficulty VARCHAR(10) CHECK (difficulty IN ('Mudah', 'Sedang', 'Sulit')),
                    source TEXT,
                    created_by BIGINT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'questions' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'questions': {e}")


def ensure_exam_results_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exam_results (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    category TEXT,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    user_answer CHAR(1),
                    is_correct BOOLEAN,
                    total_duration_sec INTEGER,
                    accuracy_percent NUMERIC(5,2),
                    started_at TIMESTAMPTZ,
                    finished_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_exam_results_user_id ON exam_results(user_id);
            """
            )
            conn.commit()
            log.info("✅ Tabel 'exam_results' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'exam_results': {e}")


def ensure_exam_results_details_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exam_results_details (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    question_id INT NOT NULL,
                    answered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'exam_results_details' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'exam_results_details': {e}")


def ensure_user_answers_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_answers (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users_utbk(user_id) ON DELETE CASCADE,
                    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
                    user_answer CHAR(1) CHECK (user_answer IN ('A', 'B', 'C', 'D')),
                    is_correct BOOLEAN,
                    answered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    difficulty_cache VARCHAR(10) CHECK (difficulty_cache IN ('Mudah', 'Sedang', 'Sulit'))
                );
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_answers_user_id ON user_answers(user_id);
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_answers_question_id ON user_answers(question_id);
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_answers_session_id ON user_answers(session_id);
            """
            )

            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION update_last_answered()
                RETURNS TRIGGER AS $$
                BEGIN
                    UPDATE users_utbk
                    SET last_answered_at = CURRENT_TIMESTAMP
                    WHERE user_id = NEW.user_id;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """
            )
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_last_answered'
                    ) THEN
                        CREATE TRIGGER trigger_update_last_answered
                        AFTER INSERT ON user_answers
                        FOR EACH ROW
                        EXECUTE FUNCTION update_last_answered();
                    END IF;
                END;
                $$;
            """
            )
            conn.commit()
            log.info("✅ Tabel 'user_answers' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'user_answers': {e}")

    # =======================================================


def ensure_vip_users_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vip_users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    paket TEXT,
                    status TEXT DEFAULT 'active'
                );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'vip_users' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'vip_users': {e}")


def ensure_active_sessions_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS active_sessions (
                    user_id BIGINT PRIMARY KEY,
                    data JSONB NOT NULL,
                    source_bot TEXT DEFAULT 'utbk',
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION update_session_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
            )

            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_active_sessions_updated_at'
                    ) THEN
                        CREATE TRIGGER trigger_active_sessions_updated_at
                        BEFORE UPDATE ON active_sessions
                        FOR EACH ROW
                        EXECUTE FUNCTION update_session_timestamp();
                    END IF;
                END;
                $$;
                """
            )

            conn.commit()
            log.info("✅ Tabel 'active_sessions' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'active_sessions': {e}")


def ensure_usage_log_table():
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_log (
                    user_id BIGINT NOT NULL,
                    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    count INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (user_id, log_date)
                );
            """
            )
            conn.commit()
            log.info("✅ Tabel 'vip_users' berhasil dicek/dibuat.")
    except Exception as e:
        log.error(f"❌ Gagal membuat tabel 'vip_users': {e}")


def ensure_all_tables():
    ensure_users_utbk_table()
    ensure_active_sessions_table()
    ensure_exam_results_details_table()
    ensure_questions_table()
    ensure_user_answers_table()
    ensure_exam_results_table()
    ensure_vip_users_table()
    ensure_usage_log_table()


def execute_query(query: str):
    """Fungsi umum untuk eksekusi query bebas"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(query)
            conn.commit()
    except Exception as e:
        log.error(f"Gagal eksekusi query: {e}")
