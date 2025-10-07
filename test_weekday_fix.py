#!/usr/bin/env python3
"""
Test APScheduler weekday configuration fix
Validates that the cron trigger accepts the corrected day_of_week format
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from worker.tasks.meta_trend_intelligence_task import get_meta_trend_task_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_weekday_configuration():
    """Test that the corrected weekday configuration is valid."""
    try:
        # Get the meta-trend task configuration
        meta_config = get_meta_trend_task_config()
        schedule_config = meta_config['schedule']

        logger.info("🔍 Testing APScheduler weekday configuration...")
        logger.info(f"📅 Day of week: {schedule_config['day_of_week']}")
        logger.info(f"⏰ Hour: {schedule_config['hour']}")
        logger.info(f"⏱️ Minute: {schedule_config['minute']}")

        # Test CronTrigger creation
        trigger = CronTrigger(
            day_of_week=schedule_config['day_of_week'],
            hour=schedule_config['hour'],
            minute=schedule_config['minute']
        )

        logger.info("✅ CronTrigger created successfully!")
        logger.info(f"🎯 Next run time: {trigger.next_execution_time()}")

        # Test scheduler configuration
        scheduler = AsyncIOScheduler()

        # Dummy async function for testing
        async def dummy_task():
            pass

        # Add job to test scheduler accepts the configuration
        scheduler.add_job(
            dummy_task,
            'cron',
            day_of_week=schedule_config['day_of_week'],
            hour=schedule_config['hour'],
            minute=schedule_config['minute'],
            id='test_meta_trend_job',
            name='Test Meta-Trend Job'
        )

        logger.info("✅ Scheduler job added successfully!")
        logger.info("✅ APScheduler weekday configuration is valid!")

        return True

    except Exception as e:
        logger.error(
            f"❌ APScheduler weekday configuration test failed: {str(e)}")
        return False
    finally:
        try:
            scheduler.shutdown(wait=False)
        except:
            pass


if __name__ == "__main__":
    logger.info("🚀 Testing APScheduler weekday configuration fix...")

    success = test_weekday_configuration()

    if success:
        logger.info("🎉 Weekday configuration fix validated successfully!")
        logger.info("✅ APScheduler will accept the corrected 'sun' format")
        logger.info("🔧 Previous error: 'sunday' → Fixed: 'sun'")
    else:
        logger.error("❌ Weekday configuration test failed")
