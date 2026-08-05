import asyncio
import logging
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker
from src.config import settings
from src.services.analytics import calculate_analytics

logger = logging.getLogger(__name__)

async def check_and_send_scheduled_reports(session_factory: async_sessionmaker, bot: Bot):
    last_sent_month = None
    last_sent_year = None

    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Check Monthly Report: Trigger on 1st day of new month
            current_month_key = f"{now.year}-{now.month:02d}"
            if last_sent_month is not None and last_sent_month != current_month_key and now.day == 1:
                # Previous month range
                first_of_curr_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
                last_of_prev_month = first_of_curr_month - timedelta(seconds=1)
                first_of_prev_month = datetime(last_of_prev_month.year, last_of_prev_month.month, 1, tzinfo=timezone.utc)

                async with session_factory() as session:
                    report = await calculate_analytics(session, settings.admin_telegram_id, first_of_prev_month, last_of_prev_month)
                    month_name = first_of_prev_month.strftime("%B %Y")
                    text = f"📅 **Автоматический финансовый отчет за месяц ({month_name})**\n\n"
                    text += f"💵 **Доход:** `{report.total_income:.2f}` ₴\n"
                    text += f"💸 **Расход:** `{report.total_expenses:.2f}` ₴\n"
                    text += f"📈 **Чистый поток:** `{report.cash_flow:.2f}` ₴\n"
                    text += f"📅 **Средний дневной расход:** `{report.daily_average:.2f}` ₴\n\n"
                    if report.category_breakdown:
                        text += "🏷️ **Расходы по категориям:**\n"
                        for item in report.category_breakdown:
                            text += f"• {item['category']}: `{item['amount']:.2f}` ₴ ({item['percentage']:.1f}%)\n"

                    await bot.send_message(chat_id=settings.admin_telegram_id, text=text, parse_mode="Markdown")
                    last_sent_month = current_month_key

            elif last_sent_month is None:
                last_sent_month = current_month_key

            # Check Yearly Report: Trigger on Jan 1st
            current_year_key = str(now.year)
            if last_sent_year is not None and last_sent_year != current_year_key and now.month == 1 and now.day == 1:
                prev_year = now.year - 1
                start_year = datetime(prev_year, 1, 1, tzinfo=timezone.utc)
                end_year = datetime(prev_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

                async with session_factory() as session:
                    report = await calculate_analytics(session, settings.admin_telegram_id, start_year, end_year)
                    text = f"🎆 **Автоматический годовой отчет ({prev_year})**\n\n"
                    text += f"💵 **Совокупный доход:** `{report.total_income:.2f}` ₴\n"
                    text += f"💸 **Совокупный расход:** `{report.total_expenses:.2f}` ₴\n"
                    text += f"📈 **Чистый поток:** `{report.cash_flow:.2f}` ₴\n"
                    text += f"📅 **Средний дневной расход:** `{report.daily_average:.2f}` ₴\n\n"
                    if report.category_breakdown:
                        text += "🏷️ **Топ категорий за год:**\n"
                        for item in report.category_breakdown:
                            text += f"• {item['category']}: `{item['amount']:.2f}` ₴ ({item['percentage']:.1f}%)\n"

                    await bot.send_message(chat_id=settings.admin_telegram_id, text=text, parse_mode="Markdown")
                    last_sent_year = current_year_key

            elif last_sent_year is None:
                last_sent_year = current_year_key

        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")

        # Sleep 1 hour before next check
        await asyncio.sleep(3600)
