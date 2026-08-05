import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models import Category, MCCMapping

DEFAULT_CATEGORIES = [
    {"name": "Продукты и супермаркеты", "icon": "🛒"},
    {"name": "Кафе и рестораны", "icon": "🍽️"},
    {"name": "Авто и АЗС", "icon": "⛽"},
    {"name": "Транспорт и такси", "icon": "🚕"},
    {"name": "Аптеки и медицина", "icon": "💊"},
    {"name": "Коммунальные и связь", "icon": "📱"},
    {"name": "Развлечения и отдых", "icon": "🎉"},
    {"name": "Одежда и обувь", "icon": "👕"},
    {"name": "Другое", "icon": "📦"},
]

MCC_RULE_MAP = {
    5411: 1, 5499: 1,  # Продукты
    5812: 2, 5814: 2,  # Кафе
    5541: 3, 5542: 3,  # Авто
    4121: 4, 4111: 4,  # Транспорт
    5912: 5,           # Аптеки
    4814: 6, 4899: 6,  # Коммуналка
}

async def seed_initial_data(session: AsyncSession, mcc_loc_path: str = "mcc-loc.json"):
    res = await session.execute(select(Category))
    if not res.scalars().all():
        for cat in DEFAULT_CATEGORIES:
            session.add(Category(name=cat["name"], icon=cat["icon"]))
        await session.commit()

    res = await session.execute(select(MCCMapping))
    if not res.scalars().all() and os.path.exists(mcc_loc_path):
        with open(mcc_loc_path, "r", encoding="utf-8") as f:
            mcc_data = json.load(f)
        
        mappings = []
        for mcc_str, loc in mcc_data.items():
            mcc_code = int(mcc_str)
            cat_id = MCC_RULE_MAP.get(mcc_code, 9)  # Default 9 ("Другое")
            mappings.append(MCCMapping(mcc=mcc_code, category_id=cat_id, description_uk=loc.get("uk")))
        
        session.add_all(mappings)
        await session.commit()
