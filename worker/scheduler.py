import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


async def run_scheduler_loop(worker):
    """Async scheduler loop"""
    scheduler = AsyncIOScheduler()

    # Schedule tasks
    scheduler.add_job(
        worker._run_sample_task,
        'interval',
        seconds=10,
        id='sample_task'
    )

    scheduler.start()

    try:
        while worker.is_running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Scheduler loop cancelled")
    finally:
        try:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")
        except Exception as e:
            logger.debug(f"Scheduler shutdown error (ignored): {e}")
