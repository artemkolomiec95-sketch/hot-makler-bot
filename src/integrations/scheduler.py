import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.core.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def setup_scheduler(sync_func):
    scheduler.add_job(
        sync_func,
        trigger=IntervalTrigger(hours=settings.sheets_sync_interval_hours),
        id="sheets_sync",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(f"Планировщик: синхронизация Sheets каждые {settings.sheets_sync_interval_hours}ч")
