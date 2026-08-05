from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.db.dao import DAO

router = Router()

@router.message(F.text == "👤 Профиль / Счета")
async def profile_handler(message: Message, session: AsyncSession):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        return
    dao = DAO(session)
    accounts = await dao.get_user_accounts(message.from_user.id)
    if not accounts:
        await message.answer("ℹ️ Счета еще не загружены. Перейдите в ⚙️ Настройки и привяжите токен Монобанка.")
        return

    total_balance = sum(acc.balance for acc in accounts) / 100.0
    text = f"💳 **Ваши счета Monobank:**\n\n"
    for acc in accounts:
        bal = acc.balance / 100.0
        pan = f"({acc.masked_pan})" if acc.masked_pan else ""
        text += f"• **{acc.type.upper()}** {pan}: `{bal:.2f}` UAH\n"

    text += f"\n💰 **Общий баланс:** `{total_balance:.2f}` UAH"
    await message.answer(text, parse_mode="Markdown")
