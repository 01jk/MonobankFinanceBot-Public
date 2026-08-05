# Monobank Finance Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot for Monobank finance tracking (incomes, expenses, categories, real-time webhooks, analytics reports, Railway deployable).

**Architecture:** Async Python 3.11 with aiogram 3.x for Telegram interface and aiohttp server for Monobank Webhook integration. Database managed via SQLAlchemy 2.0 async engine and SQLite (`aiosqlite`).

**Tech Stack:** Python 3.11, aiogram 3.x, aiohttp, SQLAlchemy 2.0, aiosqlite, pydantic v2, pytest, pytest-asyncio, python-dotenv.

---

### Task 1: Project Environment & Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create `requirements.txt`**

```text
aiogram>=3.4.1
aiohttp>=3.9.3
sqlalchemy>=2.0.28
aiosqlite>=0.20.0
pydantic>=2.6.4
pydantic-settings>=2.2.1
python-dotenv>=1.0.1
pytest>=8.1.1
pytest-asyncio>=0.23.6
```

- [ ] **Step 2: Create `.env.example`**

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_TELEGRAM_ID=123456789
MONO_API_TOKEN=u3AulkpZFI1lIuGsik6vuPsVWqN7GoWs6o_MO2sdf301
WEBHOOK_BASE_URL=https://your-app.up.railway.app
WEBHOOK_SECRET=super_secret_webhook_key_123
PORT=8080
DATABASE_URL=sqlite+aiosqlite:///data/finance_bot.db
```

- [ ] **Step 3: Create `src/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field(..., validation_alias="BOT_TOKEN")
    admin_telegram_id: int = Field(..., validation_alias="ADMIN_TELEGRAM_ID")
    mono_api_token: str = Field("", validation_alias="MONO_API_TOKEN")
    webhook_base_url: str = Field("", validation_alias="WEBHOOK_BASE_URL")
    webhook_secret: str = Field("secret", validation_alias="WEBHOOK_SECRET")
    port: int = Field(8080, validation_alias="PORT")
    database_url: str = Field("sqlite+aiosqlite:///finance_bot.db", validation_alias="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
```

- [ ] **Step 4: Create `tests/test_config.py`**

```python
import os
import pytest
from src.config import Settings

def test_settings_load(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token")
    monkeypatch.setenv("ADMIN_TELEGRAM_ID", "12345")
    monkeypatch.setenv("MONO_API_TOKEN", "test_mono_token")

    st = Settings()
    assert st.bot_token == "test_bot_token"
    assert st.admin_telegram_id == 12345
    assert st.mono_api_token == "test_mono_token"
```

- [ ] **Step 5: Run tests to verify config loading**

Run: `pytest tests/test_config.py`
Expected: PASS

---

### Task 2: Database Layer & Models

**Files:**
- Create: `src/db/__init__.py`
- Create: `src/db/base.py`
- Create: `src/db/models.py`
- Create: `src/db/dao.py`
- Create: `src/db/seed.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Create `src/db/base.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

async def init_db_engine(db_url: str):
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, async_session
```

- [ ] **Step 2: Create `src/db/models.py`**

```python
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    mono_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # account_id
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
    currency_code: Mapped[int] = mapped_column(Integer)
    balance: Mapped[int] = mapped_column(BigInteger, default=0)
    credit_limit: Mapped[int] = mapped_column(BigInteger, default=0)
    masked_pan: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    iban: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    icon: Mapped[str] = mapped_column(String(10), default="📦")
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)

class MCCMapping(Base):
    __tablename__ = "mcc_mappings"

    mcc: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"))
    description_uk: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    account_id: Mapped[str] = mapped_column(String(255), ForeignKey("accounts.id"))
    time: Mapped[datetime] = mapped_column(DateTime)
    description: Mapped[str] = mapped_column(String(500))
    amount: Mapped[int] = mapped_column(BigInteger)  # kopecks (>0 income, <0 expense)
    mcc: Mapped[int] = mapped_column(Integer)
    balance: Mapped[int] = mapped_column(BigInteger)
    currency_code: Mapped[int] = mapped_column(Integer)
    commission_rate: Mapped[int] = mapped_column(BigInteger, default=0)
    cashback_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
```

- [ ] **Step 3: Create `src/db/dao.py`**

```python
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import User, Account, Category, MCCMapping, Transaction

class DAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, telegram_id: int, is_admin: bool = False) -> User:
        res = await self.session.execute(select(User).where(User.id == telegram_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(id=telegram_id, is_admin=is_admin)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def set_mono_token(self, user_id: int, token: str, secret: str):
        await self.session.execute(
            update(User).where(User.id == user_id).values(mono_token=token, webhook_secret=secret)
        )
        await self.session.commit()

    async def save_accounts(self, accounts_data: List[dict], user_id: int):
        for acc in accounts_data:
            acc_id = acc["id"]
            res = await self.session.execute(select(Account).where(Account.id == acc_id))
            existing = res.scalar_one_or_none()
            masked_pan = acc.get("maskedPan", [None])[0] if acc.get("maskedPan") else None
            if existing:
                existing.balance = acc.get("balance", 0)
                existing.credit_limit = acc.get("creditLimit", 0)
                existing.masked_pan = masked_pan
                existing.iban = acc.get("iban")
            else:
                new_acc = Account(
                    id=acc_id,
                    user_id=user_id,
                    type=acc.get("type", "unknown"),
                    currency_code=acc.get("currencyCode", 980),
                    balance=acc.get("balance", 0),
                    credit_limit=acc.get("creditLimit", 0),
                    masked_pan=masked_pan,
                    iban=acc.get("iban")
                )
                self.session.add(new_acc)
        await self.session.commit()

    async def get_user_accounts(self, user_id: int) -> List[Account]:
        res = await self.session.execute(select(Account).where(Account.user_id == user_id, Account.is_active == True))
        return list(res.scalars().all())

    async def add_transaction(self, tx: Transaction) -> bool:
        res = await self.session.execute(select(Transaction).where(Transaction.id == tx.id))
        if res.scalar_one_or_none():
            return False  # Already exists
        self.session.add(tx)
        await self.session.commit()
        return True

    async def get_categories(self) -> List[Category]:
        res = await self.session.execute(select(Category))
        return list(res.scalars().all())

    async def get_category_by_id(self, cat_id: int) -> Optional[Category]:
        res = await self.session.execute(select(Category).where(Category.id == cat_id))
        return res.scalar_one_or_none()

    async def get_mcc_category(self, mcc: int) -> Optional[int]:
        res = await self.session.execute(select(MCCMapping.category_id).where(MCCMapping.mcc == mcc))
        return res.scalar_one_or_none()

    async def update_transaction_category(self, tx_id: str, category_id: int):
        await self.session.execute(
            update(Transaction).where(Transaction.id == tx_id).values(category_id=category_id)
        )
        await self.session.commit()

    async def toggle_transaction_internal(self, tx_id: str) -> bool:
        res = await self.session.execute(select(Transaction).where(Transaction.id == tx_id))
        tx = res.scalar_one_or_none()
        if tx:
            tx.is_internal = not tx.is_internal
            await self.session.commit()
            return tx.is_internal
        return False
```

- [ ] **Step 4: Create `src/db/seed.py`**

```python
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
```

- [ ] **Step 5: Create `tests/test_db.py`**

```python
import pytest
from src.db.base import init_db_engine, Base
from src.db.dao import DAO
from src.db.seed import seed_initial_data
from src.db.models import Transaction
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_db_flow(tmp_path):
    db_file = tmp_path / "test.db"
    engine, async_session_factory = await init_db_engine(f"sqlite+aiosqlite:///{db_file}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        dao = DAO(session)
        user = await dao.get_or_create_user(telegram_id=1001, is_admin=True)
        assert user.id == 1001

        await seed_initial_data(session, mcc_loc_path="mcc-loc.json")
        cats = await dao.get_categories()
        assert len(cats) >= 9

        tx = Transaction(
            id="tx1",
            user_id=1001,
            account_id="acc1",
            time=datetime.now(timezone.utc),
            description="Supermarket",
            amount=-15000,
            mcc=5411,
            balance=50000,
            currency_code=980
        )
        saved = await dao.add_transaction(tx)
        assert saved is True

        duplicate_saved = await dao.add_transaction(tx)
        assert duplicate_saved is False
```

- [ ] **Step 6: Run tests to verify DB & DAO**

Run: `pytest tests/test_db.py`
Expected: PASS

---

### Task 3: Monobank API Client & Service

**Files:**
- Create: `src/services/__init__.py`
- Create: `src/services/monobank_api.py`
- Create: `tests/test_monobank_api.py`

- [ ] **Step 1: Create `src/services/monobank_api.py`**

```python
import asyncio
import time
import aiohttp
from typing import Dict, Any, Optional

class MonobankRateLimitError(Exception):
    pass

class MonobankClient:
    def __init__(self, base_url: str = "https://api.monobank.ua"):
        self.base_url = base_url
        self._last_request_time: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, token: str) -> asyncio.Lock:
        if token not in self._locks:
            self._locks[token] = asyncio.Lock()
        return self._locks[token]

    async def _check_rate_limit(self, token: str):
        last_time = self._last_request_time.get(token, 0)
        elapsed = time.time() - last_time
        if elapsed < 60:
            raise MonobankRateLimitError(f"Rate limit exceeded. Wait {int(60 - elapsed)}s.")

    async def get_client_info(self, token: str) -> Dict[str, Any]:
        async with self._get_lock(token):
            await self._check_rate_limit(token)
            headers = {"X-Token": token}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/personal/client-info", headers=headers) as resp:
                    self._last_request_time[token] = time.time()
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        raise MonobankRateLimitError("Monobank API 429 Too Many Requests")
                    else:
                        text = await resp.text()
                        raise Exception(f"Monobank API error {resp.status}: {text}")

    async def get_statement(self, token: str, account: str, from_ts: int, to_ts: Optional[int] = None) -> list:
        async with self._get_lock(token):
            await self._check_rate_limit(token)
            headers = {"X-Token": token}
            url = f"{self.base_url}/personal/statement/{account}/{from_ts}"
            if to_ts:
                url += f"/{to_ts}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    self._last_request_time[token] = time.time()
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        raise MonobankRateLimitError("Monobank API 429 Too Many Requests")
                    else:
                        text = await resp.text()
                        raise Exception(f"Monobank API error {resp.status}: {text}")

    async def set_webhook(self, token: str, webhook_url: str) -> bool:
        headers = {"X-Token": token}
        payload = {"webHookUrl": webhook_url}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/personal/webhook", headers=headers, json=payload) as resp:
                return resp.status == 200
```

- [ ] **Step 2: Create `tests/test_monobank_api.py`**

```python
import pytest
import time
from src.services.monobank_api import MonobankClient, MonobankRateLimitError

@pytest.mark.asyncio
async def test_rate_limit_check():
    client = MonobankClient()
    token = "test_token_123"
    client._last_request_time[token] = time.time()
    
    with pytest.raises(MonobankRateLimitError):
        await client._check_rate_limit(token)
```

- [ ] **Step 3: Run API client test**

Run: `pytest tests/test_monobank_api.py`
Expected: PASS

---

### Task 4: Financial Analytics Module

**Files:**
- Create: `src/services/analytics.py`
- Create: `tests/test_analytics.py`

- [ ] **Step 1: Create `src/services/analytics.py`**

```python
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Transaction, Category

class AnalyticsReport:
    def __init__(
        self,
        total_income: float,
        total_expenses: float,
        cash_flow: float,
        daily_average: float,
        category_breakdown: List[Dict[str, Any]]
    ):
        self.total_income = total_income
        self.total_expenses = total_expenses
        self.cash_flow = cash_flow
        self.daily_average = daily_average
        self.category_breakdown = category_breakdown

async def calculate_analytics(
    session: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> AnalyticsReport:
    stmt = select(Transaction, Category).outerjoin(
        Category, Transaction.category_id == Category.id
    ).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.time >= start_date,
            Transaction.time <= end_date,
            Transaction.is_internal == False
        )
    )
    res = await session.execute(stmt)
    rows = res.all()

    total_income_kopecks = 0
    total_expenses_kopecks = 0
    cat_expenses: Dict[str, Dict[str, Any]] = {}

    for tx, cat in rows:
        amount = tx.amount
        cat_name = f"{cat.icon} {cat.name}" if cat else "📦 Другое"
        if amount > 0:
            total_income_kopecks += amount
        else:
            exp = abs(amount)
            total_expenses_kopecks += exp
            if cat_name not in cat_expenses:
                cat_expenses[cat_name] = 0
            cat_expenses[cat_name] += exp

    total_income = total_income_kopecks / 100.0
    total_expenses = total_expenses_kopecks / 100.0
    cash_flow = total_income - total_expenses

    days_cnt = max((end_date - start_date).days, 1)
    daily_average = total_expenses / days_cnt

    breakdown = []
    for cat_name, exp_kopecks in sorted(cat_expenses.items(), key=lambda x: x[1], reverse=True):
        amount_uah = exp_kopecks / 100.0
        pct = (amount_uah / total_expenses * 100.0) if total_expenses > 0 else 0.0
        breakdown.append({
            "category": cat_name,
            "amount": amount_uah,
            "percentage": pct
        })

    return AnalyticsReport(
        total_income=total_income,
        total_expenses=total_expenses,
        cash_flow=cash_flow,
        daily_average=daily_average,
        category_breakdown=breakdown
    )
```

- [ ] **Step 2: Create `tests/test_analytics.py`**

```python
import pytest
from datetime import datetime, timedelta, timezone
from src.db.base import init_db_engine, Base
from src.db.models import Transaction, Category
from src.services.analytics import calculate_analytics

@pytest.mark.asyncio
async def test_analytics_calculation(tmp_path):
    db_file = tmp_path / "test_analytics.db"
    engine, async_session_factory = await init_db_engine(f"sqlite+aiosqlite:///{db_file}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        cat = Category(id=1, name="Продукты", icon="🛒")
        session.add(cat)
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=10)

        tx1 = Transaction(id="t1", user_id=1, account_id="a", time=now, description="D", amount=-20000, mcc=5411, balance=0, currency_code=980, category_id=1)
        tx2 = Transaction(id="t2", user_id=1, account_id="a", time=now, description="D", amount=50000, mcc=0, balance=0, currency_code=980)
        tx_internal = Transaction(id="t3", user_id=1, account_id="a", time=now, description="D", amount=-100000, mcc=0, balance=0, currency_code=980, is_internal=True)

        session.add_all([tx1, tx2, tx_internal])
        await session.commit()

        report = await calculate_analytics(session, 1, start, now + timedelta(days=1))
        assert report.total_income == 500.0
        assert report.total_expenses == 200.0
        assert report.cash_flow == 300.0
        assert len(report.category_breakdown) == 1
        assert report.category_breakdown[0]["category"] == "🛒 Продукты"
        assert report.category_breakdown[0]["amount"] == 200.0
```

- [ ] **Step 3: Run analytics tests**

Run: `pytest tests/test_analytics.py`
Expected: PASS

---

### Task 5: Telegram Bot Keyboards & Handlers

**Files:**
- Create: `src/bot/__init__.py`
- Create: `src/bot/keyboards.py`
- Create: `src/bot/handlers/__init__.py`
- Create: `src/bot/handlers/start.py`
- Create: `src/bot/handlers/reports.py`
- Create: `src/bot/handlers/settings.py`
- Create: `src/bot/handlers/callbacks.py`

- [ ] **Step 1: Create `src/bot/keyboards.py`**

```python
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
        [InlineKeyboardButton(text="Текущий месяц", callback_data="report_month")]
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
```

- [ ] **Step 2: Create `src/bot/handlers/start.py`**

```python
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
    if message.from_user.id != settings.admin_telegram_id:
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
```

- [ ] **Step 3: Create `src/bot/handlers/reports.py` & `profile.py`**

Create `src/bot/handlers/profile.py`:
```python
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.db.dao import DAO
from src.services.monobank_api import MonobankClient, MonobankRateLimitError

router = Router()

@router.message(F.text == "👤 Профиль / Счета")
async def profile_handler(message: Message, session: AsyncSession):
    if message.from_user.id != settings.admin_telegram_id:
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
```

Create `src/bot/handlers/reports.py`:
```python
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
    if message.from_user.id != settings.admin_telegram_id:
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
```

- [ ] **Step 4: Create `src/bot/handlers/settings.py` & `callbacks.py`**

Create `src/bot/handlers/settings.py`:
```python
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
    if message.from_user.id != settings.admin_telegram_id:
        return
    dao = DAO(session)
    user = await dao.get_or_create_user(message.from_user.id)
    token_status = "✅ Настроен" if user.mono_token else "❌ Отсутствует"
    
    text = (
        f"⚙️ **Настройки бота**\n\n"
        f"**Токен Monobank:** {token_status}\n"
        f"**Webhook URL:** `{settings.webhook_base_url}`\n\n"
        f"Отправьте ваш Monobank API Token сообщением для обновления."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🔄 Синхронизировать")
async def sync_handler(message: Message, session: AsyncSession):
    if message.from_user.id != settings.admin_telegram_id:
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
```

Create `src/bot/handlers/callbacks.py`:
```python
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
            new_lines.append(f"Категория: {cat.icon} {cat.name}")
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
```

---

### Task 6: Webhook Server & Application Runner

**Files:**
- Create: `src/web/__init__.py`
- Create: `src/web/webhook_server.py`
- Create: `main.py`
- Create: `Dockerfile`
- Create: `Procfile`

- [ ] **Step 1: Create `src/web/webhook_server.py`**

```python
from aiohttp import web
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker
from src.db.dao import DAO
from src.db.models import Transaction, User
from src.bot.keyboards import get_transaction_inline_keyboard
from datetime import datetime, timezone
from sqlalchemy import select

def create_webhook_app(session_factory: async_sessionmaker, bot: Bot) -> web.Application:
    app = web.Application()

    async def handle_webhook(request: web.Request):
        secret = request.match_info.get("secret")
        
        # Monobank sends GET to validate webhook
        if request.method == "GET":
            return web.Response(status=200, text="OK")

        if request.method == "POST":
            data = await request.json()
            if data.get("type") == "StatementItem":
                stmt_item = data["data"]["statementItem"]
                account_id = data["data"]["account"]

                async with session_factory() as session:
                    dao = DAO(session)
                    res = await session.execute(select(User).where(User.webhook_secret == secret))
                    user = res.scalar_one_or_none()
                    if not user:
                        return web.Response(status=403, text="Forbidden")

                    cat_id = await dao.get_mcc_category(stmt_item["mcc"]) or 9
                    cat = await dao.get_category_by_id(cat_id)

                    tx = Transaction(
                        id=stmt_item["id"],
                        user_id=user.id,
                        account_id=account_id,
                        time=datetime.fromtimestamp(stmt_item["time"], tz=timezone.utc),
                        description=stmt_item.get("description", ""),
                        amount=stmt_item["amount"],
                        mcc=stmt_item["mcc"],
                        balance=stmt_item["balance"],
                        currency_code=stmt_item.get("currencyCode", 980),
                        commission_rate=stmt_item.get("commissionRate", 0),
                        cashback_amount=stmt_item.get("cashbackAmount", 0),
                        comment=stmt_item.get("comment"),
                        is_internal=False,
                        category_id=cat_id
                    )

                    saved = await dao.add_transaction(tx)
                    if saved:
                        amount_uah = abs(tx.amount) / 100.0
                        tx_type = "📈 Доход" if tx.amount > 0 else "💸 Расход"
                        cat_str = f"{cat.icon} {cat.name}" if cat else "📦 Другое"
                        bal_uah = tx.balance / 100.0

                        msg_text = (
                            f"{tx_type}: `{amount_uah:.2f}` ₴\n"
                            f"Описание: {tx.description}\n"
                            f"Категория: {cat_str}\n"
                            f"Остаток: `{bal_uah:.2f}` ₴"
                        )
                        kb = get_transaction_inline_keyboard(tx.id, is_internal=False)
                        await bot.send_message(chat_id=user.id, text=msg_text, reply_markup=kb, parse_mode="Markdown")

            return web.Response(status=200, text="OK")

    app.router.add_get("/webhook/mono/{secret}", handle_webhook)
    app.router.add_post("/webhook/mono/{secret}", handle_webhook)
    return app
```

- [ ] **Step 2: Create `main.py`**

```python
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiohttp import web
from src.config import settings
from src.db.base import init_db_engine, Base
from src.db.seed import seed_initial_data
from src.bot.handlers import start, profile, reports, settings as settings_handler, callbacks
from src.web.webhook_server import create_webhook_app

logging.basicConfig(level=logging.INFO)

async def main():
    db_dir = os.path.dirname(settings.database_url.replace("sqlite+aiosqlite:///", ""))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    engine, async_session_factory = await init_db_engine(settings.database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await seed_initial_data(session)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # DB session middleware
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with async_session_factory() as session:
            data["session"] = session
            return await handler(event, data)

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(reports.router)
    dp.include_router(settings_handler.router)
    dp.include_router(callbacks.router)

    app = create_webhook_app(async_session_factory, bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.port)
    await site.start()
    logging.info(f"Webhook server started on port {settings.port}")

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Create `Dockerfile` & `Procfile`**

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
```

Create `Procfile`:
```text
web: python main.py
```

---

### Task 7: Full System Verification

- [ ] **Step 1: Run all unit and integration tests**

Run: `pytest -v`
Expected: ALL TESTS PASS
