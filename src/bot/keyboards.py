from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from src.db.models import Category

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="👤 Профиль / Счета"), KeyboardButton(text="📊 Финансовый отчет")],
        [KeyboardButton(text="🔄 Синхронизировать"), KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_period_inline_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="Сегодня", callback_data="report_today"), InlineKeyboardButton(text="За неделю", callback_data="report_week")],
        [InlineKeyboardButton(text="Текущий месяц", callback_data="report_month")],
        [InlineKeyboardButton(text="📥 Скачать CSV (Месяц)", callback_data="export_csv_month"), InlineKeyboardButton(text="📥 Скачать CSV (Всё)", callback_data="export_csv_all")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_transaction_inline_keyboard(tx_id: str, is_internal: bool) -> InlineKeyboardMarkup:
    internal_str = "ДА 🟢" if is_internal else "НЕТ 🔴"
    kb = [
        [InlineKeyboardButton(text="🏷️ Изменить категорию", callback_data=f"edit_cat:{tx_id}")],
        [InlineKeyboardButton(text=f"🔄 Свой перевод: {internal_str}", callback_data=f"toggle_internal:{tx_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_categories_inline_keyboard(tx_id: str, categories: List[Category]) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(text=f"{cat.icon} {cat.name}", callback_data=f"set_cat:{tx_id}:{cat.id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
