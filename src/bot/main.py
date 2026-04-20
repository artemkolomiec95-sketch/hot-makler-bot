import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

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


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health server on port {port}")
    server.serve_forever()


async def sync_sheets():
    logger.info("Syncing Google Sheets...")
    props = await asyncio.get_event_loop().run_in_executor(None, fetch_properties)
    update_cache(props)
    from src.storage.db import SessionLocal
    from src.storage.repositories import PropertyRepo
    async with SessionLocal() as session:
        await PropertyRepo(session).save_all(props)
    logger.info(f"Synced {len(props)} properties")


async def main():
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn)

    await init_db()
    await sync_sheets()

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

    logger.info("Bot started @hot_makler_fukuok_bot")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    # Запускаем health-сервер в отдельном потоке
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    asyncio.run(main())
