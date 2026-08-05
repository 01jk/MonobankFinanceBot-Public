from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.dao import DAO
from src.bot.keyboards import get_categories_inline_keyboard, get_transaction_inline_keyboard

router = Router()

@router.callback_query(F.data.startswith("edit_cat:"))
async def edit_category_callback(callback: CallbackQuery, session: AsyncSession):
    tx_id = callback.data.split(":")[1]
    dao = DAO(session)
    categories = await dao.get_categories()
    kb = get_categories_inline_keyboard(tx_id, categories)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(F.data.startswith("set_cat:"))
async def set_category_callback(callback: CallbackQuery, session: AsyncSession):
    _, tx_id, cat_id_str = callback.data.split(":")
    cat_id = int(cat_id_str)
    dao = DAO(session)
    await dao.update_transaction_category(tx_id, cat_id)
    cat = await dao.get_category_by_id(cat_id)

    lines = callback.message.text.split("\n")
    new_lines = []
    for line in lines:
        if line.startswith("Категория:"):
            new_lines.append(f"Категория: {cat.icon} {cat.name}" if cat else f"Категория: {cat_id}")
        else:
            new_lines.append(line)

    kb = get_transaction_inline_keyboard(tx_id, is_internal=False)
    await callback.message.edit_text("\n".join(new_lines), reply_markup=kb)

@router.callback_query(F.data.startswith("toggle_internal:"))
async def toggle_internal_callback(callback: CallbackQuery, session: AsyncSession):
    tx_id = callback.data.split(":")[1]
    dao = DAO(session)
    is_internal = await dao.toggle_transaction_internal(tx_id)
    kb = get_transaction_inline_keyboard(tx_id, is_internal)
    await callback.message.edit_reply_markup(reply_markup=kb)
