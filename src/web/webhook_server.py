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
                    from src.config import settings
                    if secret == settings.webhook_secret:
                        res = await session.execute(select(User).where(User.is_admin == True))
                        user = res.scalar_one_or_none()
                        if not user:
                            res = await session.execute(select(User))
                            user = res.scalars().first()
                    else:
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
                    await dao.update_account_balance(account_id, stmt_item["balance"])
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
