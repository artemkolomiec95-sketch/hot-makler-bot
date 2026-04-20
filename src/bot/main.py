import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from src.core.config import settings
from src.storage.db import init_db
from src.integrations.sheets import fetch_properties
from src.integrations.scheduler import setup_scheduler, scheduler
from src.bot.handlers.results import update_cache
from src.bot.handlers import start, search, results, contact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

os.makedirs("data", exist_ok=True)


async def sync_sheets():
    logger.info("Синхронизация Google Sheets...")
    props = await asyncio.get_event_loop().run_in_executor(None, fetch_properties)
    update_cache(props)
    # Сохраняем в SQLite
    from src.storage.db import SessionLocal
    from src.storage.repositories import PropertyRepo
    async with SessionLocal() as session:
        await PropertyRepo(session).save_all(props)
    logger.info(f"Синхронизировано {len(props)} объектов")


async def main():
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn)

    await init_db()
    await sync_sheets()  # первичная загрузка

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(results.router)
    dp.include_router(contact.router)

    setup_scheduler(sync_sheets)
    scheduler.start()

    logger.info("Бот запущен @hot_makler_fukuok_bot")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
