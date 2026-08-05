from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.db.dao import DAO
from src.services.monobank_api import MonobankClient

router = Router()

@router.message(F.text == "👤 Профиль / Счета")
async def profile_handler(message: Message, session: AsyncSession):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        return
    dao = DAO(session)
    user = await dao.get_or_create_user(message.from_user.id)
    accounts = await dao.get_user_accounts(message.from_user.id)

    token = user.mono_token or settings.mono_api_token
    if not accounts and token:
        client = MonobankClient()
        try:
            data = await client.get_client_info(token)
            await dao.save_accounts(data.get("accounts", []), user_id=user.id)
            accounts = await dao.get_user_accounts(message.from_user.id)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка получения счетов: {e}")
            return

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

