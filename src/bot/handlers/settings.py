import uuid
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.db.dao import DAO
from src.services.monobank_api import MonobankClient

router = Router()

class SettingsState(StatesGroup):
    waiting_for_token = State()

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message, session: AsyncSession):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        return
    dao = DAO(session)
    user = await dao.get_or_create_user(message.from_user.id)
    token_status = "✅ Настроен" if (user.mono_token or settings.mono_api_token) else "❌ Отсутствует"
    
    text = (
        f"⚙️ **Настройки бота**\n\n"
        f"**Токен Monobank:** {token_status}\n"
        f"**Webhook URL:** `{settings.webhook_base_url}`\n\n"
        f"Отправьте ваш Monobank API Token новым сообщением для обновления."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🔄 Синхронизировать")
async def sync_handler(message: Message, session: AsyncSession):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        return
    dao = DAO(session)
    user = await dao.get_or_create_user(message.from_user.id)
    token = user.mono_token or settings.mono_api_token
    if not token:
        await message.answer("❌ Токен Monobank API не настроен.")
        return

    client = MonobankClient()
    try:
        data = await client.get_client_info(token)
        await dao.save_accounts(data.get("accounts", []), user_id=user.id)
        
        # Setup webhook if base_url is set
        if settings.webhook_base_url and user.webhook_secret:
            wh_url = f"{settings.webhook_base_url}/webhook/mono/{user.webhook_secret}"
            await client.set_webhook(token, wh_url)

        await message.answer("✅ Данные счетов и Webhook успешно обновлены!")
    except Exception as e:
        await message.answer(f"❌ Ошибка синхронизации: {e}")
