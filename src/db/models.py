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
