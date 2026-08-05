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
