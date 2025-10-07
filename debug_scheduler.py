#!/usr/bin/env python3
"""
Debug script to check why trending intelligence task is not logging
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_scheduler.log')
    ]
)

logger = logging.getLogger(__name__)


async def debug_worker_and_scheduler():
    """Debug the worker and scheduler setup"""

    logger.info("🔍 DEBUGGING WORKER AND SCHEDULER")
    logger.info("=" * 50)

    try:
        # Test worker import and initialization
        logger.info("Step 1: Testing worker import...")
        from worker.base import BackgroundWorker
        logger.info("✅ BackgroundWorker imported successfully")

        # Test scheduler import
        logger.info("Step 2: Testing scheduler import...")
        from worker.scheduler import run_scheduler_loop
        logger.info("✅ Scheduler imported successfully")

        # Test config import
        logger.info("Step 3: Testing config import...")
        from worker.features.trending_config import get_config
        config = get_config()
        logger.info(
            f"✅ Config loaded: interval = {config.collection_interval_minutes} minutes")

        # Initialize worker
        logger.info("Step 4: Initializing worker...")
        worker = BackgroundWorker()
        logger.info(f"✅ Worker initialized: {worker}")
        logger.info(f"   - is_running: {worker.is_running}")
        logger.info(f"   - active_tasks: {worker.active_tasks}")
        logger.info(f"   - task_count: {worker.task_count}")

        # Check if the task method exists
        logger.info("Step 5: Checking task methods...")
        if hasattr(worker, '_run_trending_intelligence_task_with_cleanup'):
            logger.info(
                "✅ _run_trending_intelligence_task_with_cleanup method exists")
        else:
            logger.error(
                "❌ _run_trending_intelligence_task_with_cleanup method NOT found")

        if hasattr(worker, '_run_trending_intelligence_task'):
            logger.info("✅ _run_trending_intelligence_task method exists")
        else:
            logger.error("❌ _run_trending_intelligence_task method NOT found")

        # Test manual call to the cleanup method
        logger.info("Step 6: Testing manual call to cleanup method...")
        try:
            # Don't actually run it, just check if it's callable
            method = getattr(
                worker, '_run_trending_intelligence_task_with_cleanup', None)
            if method and callable(method):
                logger.info("✅ Cleanup method is callable")
                logger.info("   Method signature: {}".format(
                    method.__doc__ or "No docstring"))
            else:
                logger.error("❌ Cleanup method is not callable")
        except Exception as e:
            logger.error(f"❌ Error checking cleanup method: {e}")

        # Test scheduler setup (but don't run it)
        logger.info("Step 7: Testing scheduler setup...")
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()

        # Add the job like in the real scheduler
        scheduler.add_job(
            worker._run_trending_intelligence_task_with_cleanup,
            'interval',
            minutes=config.collection_interval_minutes,
            id='trending_intelligence_main',
            max_instances=1,
            misfire_grace_time=300
        )

        jobs = scheduler.get_jobs()
        logger.info(f"✅ Scheduler setup successful with {len(jobs)} jobs")
        for job in jobs:
            logger.info(
                f"   - Job: {job.id}, func: {job.func.__name__}, next_run: {job.next_run_time}")

        # Test the task import
        logger.info("Step 8: Testing task imports...")
        from worker.tasks import trending_intelligence_task
        logger.info("✅ trending_intelligence_task imported successfully")

        if hasattr(trending_intelligence_task, 'run'):
            logger.info("✅ trending_intelligence_task.run method exists")
        else:
            logger.error("❌ trending_intelligence_task.run method NOT found")

        logger.info("=" * 50)
        logger.info("🎉 ALL DEBUGGING STEPS COMPLETED")
        logger.info("=" * 50)

        return True

    except Exception as e:
        logger.error(f"❌ DEBUGGING FAILED: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return False


async def test_scheduler_timing():
    """Test if the scheduler timing is working correctly"""

    logger.info("⏰ TESTING SCHEDULER TIMING")
    logger.info("=" * 40)

    try:
        from worker.features.trending_config import get_config
        config = get_config()

        interval_minutes = config.collection_interval_minutes
        interval_seconds = interval_minutes * 60

        logger.info(
            f"📅 Configured interval: {interval_minutes} minutes ({interval_seconds} seconds)")

        # Calculate next expected run time
        now = datetime.now(timezone.utc)
        logger.info(f"🕒 Current time: {now.strftime('%H:%M:%S UTC')}")

        # If task runs every 15 minutes, when would be the next run?
        current_minute = now.minute
        next_run_minute = (
            (current_minute // interval_minutes) + 1) * interval_minutes

        if next_run_minute >= 60:
            next_hour = now.hour + 1
            next_run_minute = next_run_minute - 60
        else:
            next_hour = now.hour

        next_run = now.replace(
            hour=next_hour, minute=next_run_minute, second=0, microsecond=0)
        time_until_next = (next_run - now).total_seconds()

        logger.info(
            f"⏰ Next expected run: {next_run.strftime('%H:%M:%S UTC')}")
        logger.info(
            f"⏳ Time until next run: {time_until_next:.0f} seconds ({time_until_next/60:.1f} minutes)")

        if time_until_next > 0:
            logger.info(
                f"💡 Task should run automatically in {time_until_next/60:.1f} minutes")
        else:
            logger.info("💡 Task should have run already or will run very soon")

    except Exception as e:
        logger.error(f"❌ Timing test failed: {e}")


async def main():
    """Run all debug tests"""
    logger.info("🚀 Starting Trending Intelligence Debug Session")
    logger.info(
        f"📅 Debug started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Run debugging steps
    debug_success = await debug_worker_and_scheduler()

    if debug_success:
        logger.info("")
        await test_scheduler_timing()

    logger.info("")
    logger.info("🏁 Debug session completed")
    logger.info("📄 Check debug_scheduler.log for detailed output")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Debug interrupted by user")
    except Exception as e:
        logger.error(f"Debug failed: {e}")
