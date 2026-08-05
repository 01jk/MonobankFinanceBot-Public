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
