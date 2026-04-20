from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    realtor_tg_id: int

    google_sheets_id: str = ""
    google_service_account_json: str = "credentials.json"

    whatsapp_provider: str = "telegram"
    sheets_sync_interval_hours: int = 8

    sentry_dsn: str = ""
    env: str = "development"

    database_url: str = "sqlite+aiosqlite:///data/bot.db"


settings = Settings()
