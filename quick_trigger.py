#!/usr/bin/env python3
"""
Simple script to trigger trending intelligence task immediately
No prompts, just runs the task directly
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('quick_trigger.log')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Run trending intelligence task immediately"""

    logger.info("QUICK TRIGGER: Trending Intelligence Task")
    logger.info("=" * 50)

    try:
        # Import and initialize worker
        from worker.base import BackgroundWorker
        worker = BackgroundWorker()

        logger.info("Starting trending intelligence task...")
        start_time = datetime.now()

        # Run the task with cleanup
        await worker._run_trending_intelligence_task_with_cleanup()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 50)
        logger.info("TASK COMPLETED SUCCESSFULLY!")
        logger.info(
            f"Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"Check logs and data folders for results")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Task failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
