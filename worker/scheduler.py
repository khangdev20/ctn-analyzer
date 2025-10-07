import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .features.trending_config import get_config

logger = logging.getLogger(__name__)


async def run_scheduler_loop(worker):
    """Async scheduler loop"""
    scheduler = AsyncIOScheduler()

    # Load configuration
    config = get_config()
    trending_interval_minutes = config.collection_interval_minutes
    logger.info(
        f"[SCHEDULE] Scheduling trending intelligence task every {trending_interval_minutes} minutes")

    # Schedule trending intelligence task (main task)
    scheduler.add_job(
        worker._run_trending_intelligence_task_with_cleanup,
        'interval',
        minutes=trending_interval_minutes,  # From config (15 minutes)
        id='trending_intelligence_main',
        max_instances=1,  # Prevent overlapping executions
        misfire_grace_time=300  # 5 minutes grace time
    )

    # Schedule sample task (for testing)
    scheduler.add_job(
        worker._run_sample_task,
        'interval',
        minutes=2,  # Every 2 minutes for testing
        id='sample_task_test',
        max_instances=1
    )

    # Schedule cleanup task (maintenance)
    scheduler.add_job(
        worker._cleanup_stuck_jobs,
        'interval',
        minutes=30,  # Every 30 minutes
        id='cleanup_stuck_jobs',
        max_instances=1
    )

    scheduler.start()
    logger.info(
        f"[SCHEDULER] Scheduler started with {len(scheduler.get_jobs())} jobs")

    try:
        while worker.is_running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("[CANCELLED] Scheduler loop cancelled")
    finally:
        try:
            scheduler.shutdown(wait=False)
            logger.info("[SHUTDOWN] Scheduler shutdown")
        except Exception as e:
            logger.debug(f"Scheduler shutdown error (ignored): {e}")
