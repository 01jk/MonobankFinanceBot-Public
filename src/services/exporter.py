import csv
import io
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Transaction, Category, Account

async def generate_transactions_csv(
    session: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime
) -> bytes:
    stmt = (
        select(Transaction, Category, Account)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .outerjoin(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.time >= start_date,
                Transaction.time <= end_date
            )
        )
        .order_by(Transaction.time.desc())
    )
    res = await session.execute(stmt)
    rows = res.all()

    output = io.StringIO()
    # Write UTF-8 BOM for Excel compatibility on Windows
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')

    # Header
    writer.writerow([
        "ID Транзакции",
        "Дата и время",
        "Счет / Карта",
        "Описание",
        "Сумма (грн)",
        "Тип",
        "Категория",
        "Внутренний перевод",
        "MCC",
        "Комментарий"
    ])

    for tx, cat, acc in rows:
        amount_uah = tx.amount / 100.0
        tx_type = "Доход" if tx.amount > 0 else "Расход"
        cat_str = f"{cat.icon} {cat.name}" if cat else "Другое"
        acc_str = f"{acc.type.upper()} ({acc.masked_pan})" if (acc and acc.masked_pan) else (acc.type.upper() if acc else tx.account_id)
        is_internal_str = "Да" if tx.is_internal else "Нет"
        time_str = tx.time.strftime("%Y-%m-%d %H:%M:%S")

        writer.writerow([
            tx.id,
            time_str,
            acc_str,
            tx.description,
            f"{amount_uah:.2f}".replace('.', ','),
            tx_type,
            cat_str,
            is_internal_str,
            tx.mcc,
            tx.comment or ""
        ])

    return output.getvalue().encode('utf-8-sig')
