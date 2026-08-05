import uuid
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.db.dao import DAO
from src.services.monobank_api import MonobankClient

router = Router()

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

@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_({"👤 Профиль / Счета", "📊 Финансовый отчет", "🔄 Синхронизировать", "⚙️ Настройки"}))
async def token_input_handler(message: Message, session: AsyncSession):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        return
    
    token = message.text.strip()
    if len(token) < 20:
        await message.answer("⚠️ Неверный формат токена Monobank API.")
        return

    dao = DAO(session)
    user = await dao.get_or_create_user(message.from_user.id)
    if not user.webhook_secret:
        user.webhook_secret = str(uuid.uuid4())
    
    await dao.set_mono_token(user.id, token, user.webhook_secret)

    client = MonobankClient()
    try:
        data = await client.get_client_info(token)
        await dao.save_accounts(data.get("accounts", []), user_id=user.id)

        if settings.webhook_base_url and user.webhook_secret:
            wh_url = f"{settings.webhook_base_url}/webhook/mono/{user.webhook_secret}"
            await client.set_webhook(token, wh_url)

        await message.answer("✅ Токен привязан! Счета и Webhook успешно синхронизированы.")
    except Exception as e:
        await message.answer(f"⚠️ Токен сохранен, но при автосинхронизации произошла ошибка: {e}")
