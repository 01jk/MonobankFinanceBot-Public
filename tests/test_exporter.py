import pytest
from datetime import datetime, timedelta, timezone
from src.db.base import init_db_engine, Base
from src.db.models import Transaction, Category, Account
from src.services.exporter import generate_transactions_csv

@pytest.mark.asyncio
async def test_csv_export(tmp_path):
    db_file = tmp_path / "test_csv.db"
    engine, async_session_factory = await init_db_engine(f"sqlite+aiosqlite:///{db_file}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        cat = Category(id=1, name="Продукты", icon="🛒")
        acc = Account(id="acc1", user_id=1, type="black", currency_code=980, balance=10000)
        session.add_all([cat, acc])

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=1)

        tx = Transaction(
            id="t1",
            user_id=1,
            account_id="acc1",
            time=now,
            description="Магазин",
            amount=-25000,
            mcc=5411,
            balance=10000,
            currency_code=980,
            category_id=1
        )
        session.add(tx)
        await session.commit()

        csv_bytes = await generate_transactions_csv(session, 1, start, now + timedelta(days=1))
        content = csv_bytes.decode("utf-8-sig")

        assert "ID Транзакции" in content
        assert "Магазин" in content
        assert "-250,00" in content
        assert "🛒 Продукты" in content
