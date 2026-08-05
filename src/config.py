from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Any

def clean_quotes(v: Any) -> Any:
    if isinstance(v, str):
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1].strip()
    return v

class Settings(BaseSettings):
    bot_token: str = Field("", validation_alias="BOT_TOKEN")
    admin_telegram_id: int = Field(0, validation_alias="ADMIN_TELEGRAM_ID")
    mono_api_token: str = Field("", validation_alias="MONO_API_TOKEN")
    webhook_base_url: str = Field("", validation_alias="WEBHOOK_BASE_URL")
    webhook_secret: str = Field("secret", validation_alias="WEBHOOK_SECRET")
    port: int = Field(8080, validation_alias="PORT")
    database_url: str = Field("sqlite+aiosqlite:////data/finance_bot.db", validation_alias="DATABASE_URL")

    @field_validator("bot_token", "mono_api_token", "webhook_base_url", "webhook_secret", "database_url", mode="before")
    @classmethod
    def strip_quotes_str(cls, v):
        return clean_quotes(v)

    @field_validator("admin_telegram_id", "port", mode="before")
    @classmethod
    def strip_quotes_int(cls, v):
        val = clean_quotes(v)
        return int(val) if val else 0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
