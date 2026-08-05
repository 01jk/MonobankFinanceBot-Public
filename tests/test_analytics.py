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
