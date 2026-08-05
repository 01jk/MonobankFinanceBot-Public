import uuid
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.db.dao import DAO
from src.bot.keyboards import get_main_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        await message.answer("❌ Доступ запрещен. Бот работает в приватном режиме.")
        return

    dao = DAO(session)
    user = await dao.get_or_create_user(telegram_id=message.from_user.id, is_admin=True)
    
    if not user.webhook_secret:
        user.webhook_secret = str(uuid.uuid4())
        await session.commit()

    text = (
        "👋 Добро пожаловать в бота учета финансов Monobank!\n\n"
        "Для начала работы введите токен Monobank API в настройках (`⚙️ Настройки`)."
    )
    await message.answer(text, reply_markup=get_main_keyboard())
