from pydantic import BaseSettings


TARGET_CHANNEL = "dracinshort"

class Settings(BaseSettings):

    BOT_TOKEN: str

    # Grup / channel admin untuk notifikasi tiket
    ADMIN_FEEDBACK_CHAT_ID: int

    # Opsional
    ADMIN_IDS: list[int] = []

    class Config:
        env_file = ".env"


settings = Settings()