from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field("", validation_alias="BOT_TOKEN")
    admin_telegram_id: int = Field(0, validation_alias="ADMIN_TELEGRAM_ID")
    mono_api_token: str = Field("", validation_alias="MONO_API_TOKEN")
    webhook_base_url: str = Field("", validation_alias="WEBHOOK_BASE_URL")
    webhook_secret: str = Field("secret", validation_alias="WEBHOOK_SECRET")
    port: int = Field(8080, validation_alias="PORT")
    database_url: str = Field("sqlite+aiosqlite:///finance_bot.db", validation_alias="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
