from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.bot.keyboards import get_period_inline_keyboard
from src.services.analytics import calculate_analytics

router = Router()

@router.message(F.text == "📊 Финансовый отчет")
async def reports_menu(message: Message):
    if settings.admin_telegram_id and message.from_user.id != settings.admin_telegram_id:
        return
    await message.answer("Выберите период для формирования отчета:", reply_markup=get_period_inline_keyboard())

@router.callback_query(F.data.startswith("report_"))
async def process_report_callback(callback: CallbackQuery, session: AsyncSession):
    period = callback.data.split("_")[1]
    now = datetime.now(timezone.utc)
    
    if period == "today":
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        title = "Сегодня"
    elif period == "week":
        start = now - timedelta(days=7)
        title = "За последние 7 дней"
    else:  # month
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        title = "Текущий месяц"

    report = await calculate_analytics(session, callback.from_user.id, start, now)

    text = f"📊 **Финансовый отчет ({title})**\n\n"
    text += f"💵 **Доход:** `{report.total_income:.2f}` ₴\n"
    text += f"💸 **Расход:** `{report.total_expenses:.2f}` ₴\n"
    text += f"📈 **Чистый поток:** `{report.cash_flow:.2f}` ₴\n"
    text += f"📅 **Средний дневной расход:** `{report.daily_average:.2f}` ₴\n\n"

    if report.category_breakdown:
        text += "🏷️ **Расходы по категориям:**\n"
        for item in report.category_breakdown:
            text += f"• {item['category']}: `{item['amount']:.2f}` ₴ ({item['percentage']:.1f}%)\n"
    else:
        text += "ℹ️ Расходов за данный период не найдено."

    await callback.message.edit_text(text, parse_mode="Markdown")

@router.callback_query(F.data.startswith("export_csv_"))
async def process_export_csv_callback(callback: CallbackQuery, session: AsyncSession):
    scope = callback.data.split("_")[2]
    now = datetime.now(timezone.utc)
    
    if scope == "month":
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        filename = f"monobank_finance_{now.year}_{now.month:02d}.csv"
    else:  # all
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        filename = f"monobank_finance_all_{now.strftime('%Y%m%d')}.csv"

    from aiogram.types import BufferedInputFile
    from src.services.exporter import generate_transactions_csv

    csv_bytes = await generate_transactions_csv(session, callback.from_user.id, start, now + timedelta(days=1))
    file = BufferedInputFile(csv_bytes, filename=filename)

    await callback.message.answer_document(file, caption=f"📄 Выгрузка доходов и расходов (`{filename}`)", parse_mode="Markdown")
    await callback.answer()
