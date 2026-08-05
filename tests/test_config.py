import os
import pytest
from src.config import Settings

def test_settings_load(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token")
    monkeypatch.setenv("ADMIN_TELEGRAM_ID", "12345")
    monkeypatch.setenv("MONO_API_TOKEN", "test_mono_token")

    st = Settings()
    assert st.bot_token == "test_bot_token"
    assert st.admin_telegram_id == 12345
    assert st.mono_api_token == "test_mono_token"
