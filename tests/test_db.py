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
