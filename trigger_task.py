#!/usr/bin/env python3
"""
Script to manually trigger the trending intelligence task to run
This will execute the actual task with full processing
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see all messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trigger_task.log')
    ]
)

logger = logging.getLogger(__name__)


async def trigger_trending_intelligence_task():
    """Manually trigger the trending intelligence task"""

    logger.info("=" * 60)
    logger.info("MANUAL TRIGGER: TRENDING INTELLIGENCE TASK")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    try:
        # Import worker
        logger.info("Step 1: Importing BackgroundWorker...")
        from worker.base import BackgroundWorker
        logger.info("[OK] BackgroundWorker imported")

        # Initialize worker
        logger.info("Step 2: Initializing worker...")
        worker = BackgroundWorker()
        logger.info(f"[OK] Worker initialized")
        logger.info(f"   - Active tasks: {len(worker.active_tasks)}")
        logger.info("")

        # Check if task method exists
        if not hasattr(worker, '_run_trending_intelligence_task_with_cleanup'):
            logger.error(
                "[ERROR] _run_trending_intelligence_task_with_cleanup method not found!")
            return False

        logger.info("Step 3: Triggering trending intelligence task...")
        logger.info("This will run the ACTUAL task with full processing...")
        logger.info("Processing may take several minutes...")
        logger.info("")

        # Run the actual task
        start_time = datetime.now()
        logger.info(f"[TASK START] {start_time.strftime('%H:%M:%S')}")

        await worker._run_trending_intelligence_task_with_cleanup()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"[TASK COMPLETE] {end_time.strftime('%H:%M:%S')}")
        logger.info(
            f"[DURATION] {duration:.2f} seconds ({duration/60:.1f} minutes)")
        logger.info("")

        logger.info(
            "[SUCCESS] Trending intelligence task completed successfully!")
        logger.info(f"Final active tasks: {len(worker.active_tasks)}")

        return True

    except Exception as e:
        logger.error(f"[ERROR] Task execution failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def trigger_basic_task():
    """Alternative: trigger the basic task without cleanup wrapper"""

    logger.info("=" * 60)
    logger.info("MANUAL TRIGGER: BASIC TRENDING INTELLIGENCE TASK")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    try:
        # Import worker
        from worker.base import BackgroundWorker
        logger.info("[OK] BackgroundWorker imported")

        # Initialize worker
        worker = BackgroundWorker()
        logger.info(f"[OK] Worker initialized")
        logger.info("")

        # Check if basic task method exists
        if not hasattr(worker, '_run_trending_intelligence_task'):
            logger.error(
                "[ERROR] _run_trending_intelligence_task method not found!")
            return False

        logger.info("Step 3: Triggering basic trending intelligence task...")
        logger.info("This will run the basic task without cleanup wrapper...")
        logger.info("")

        # Run the basic task
        start_time = datetime.now()
        logger.info(f"[TASK START] {start_time.strftime('%H:%M:%S')}")

        await worker._run_trending_intelligence_task(worker)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"[TASK COMPLETE] {end_time.strftime('%H:%M:%S')}")
        logger.info(
            f"[DURATION] {duration:.2f} seconds ({duration/60:.1f} minutes)")
        logger.info("")

        logger.info("[SUCCESS] Basic trending intelligence task completed!")

        return True

    except Exception as e:
        logger.error(f"[ERROR] Basic task execution failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def trigger_via_api():
    """Alternative: trigger via API endpoint"""

    logger.info("=" * 60)
    logger.info("MANUAL TRIGGER: VIA API ENDPOINT")
    logger.info("=" * 60)

    try:
        import requests

        # Try to trigger via local API
        api_url = "http://127.0.0.1:5000/trigger-intelligence"

        logger.info(f"Sending POST request to: {api_url}")
        logger.info("This assumes the Flask app is running...")

        response = requests.post(api_url, timeout=30)

        if response.status_code == 200:
            logger.info("[SUCCESS] API trigger successful!")
            logger.info(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"[ERROR] API returned status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error(
            "[ERROR] Could not connect to API. Is the Flask app running?")
        logger.error("Try running: python run.py")
        return False
    except Exception as e:
        logger.error(f"[ERROR] API trigger failed: {e}")
        return False


async def main():
    """Main function with options"""

    logger.info("TRENDING INTELLIGENCE TASK TRIGGER")
    logger.info("Choose trigger method:")
    logger.info("1. Full task with cleanup (recommended)")
    logger.info("2. Basic task without cleanup")
    logger.info("3. Via API endpoint")
    logger.info("")

    # Get user choice
    try:
        choice = input("Enter choice (1-3) [default: 1]: ").strip()
        if not choice:
            choice = "1"
    except KeyboardInterrupt:
        logger.info("User cancelled")
        return

    logger.info(f"Selected option: {choice}")
    logger.info("")

    success = False

    if choice == "1":
        success = await trigger_trending_intelligence_task()
    elif choice == "2":
        success = await trigger_basic_task()
    elif choice == "3":
        success = await trigger_via_api()
    else:
        logger.error("Invalid choice")
        return

    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("TRIGGER COMPLETED SUCCESSFULLY!")
    else:
        logger.info("TRIGGER FAILED!")
    logger.info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Check trigger_task.log for detailed output")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Task trigger interrupted by user")
    except Exception as e:
        logger.error(f"Task trigger failed: {e}")
