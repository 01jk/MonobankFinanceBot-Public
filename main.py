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
    db_url = settings.database_url
    if os.path.exists("/data") and "data/" in db_url and not "sqlite+aiosqlite:////" in db_url:
        db_url = "sqlite+aiosqlite:////data/finance_bot.db"

    raw_path = db_url.replace("sqlite+aiosqlite:////", "/").replace("sqlite+aiosqlite:///", "")
    db_dir = os.path.dirname(raw_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    logging.info(f"Using database path: {db_url}")
    engine, async_session_factory = await init_db_engine(db_url)

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

    from src.services.scheduler import check_and_send_scheduled_reports
    scheduler_task = asyncio.create_task(check_and_send_scheduled_reports(async_session_factory, bot))

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
