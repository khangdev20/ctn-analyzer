import logging
import asyncio
from datetime import datetime, timezone

from worker.features.feeds_collector import feeds_collector

logger = logging.getLogger(__name__)


async def run(worker):
    task_id = f"sample_task_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)

    try:
        # Show current time and worker status
        current_time = datetime.now(timezone.utc)
        uptime_info = f"[TIME] {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        worker_info = f"[ACTIVE] Active: {len(worker.active_tasks)} tasks | Total: {worker.task_count} runs"

        logger.info(f"[TASK] {task_id} - {uptime_info}")
        logger.info(f"[STATUS] Worker Status: {worker_info}")

        # Simple health check - just print current status
        print(f"\n{'='*60}")
        print(f"[HEARTBEAT] WORKER HEARTBEAT - {uptime_info}")
        print(f"[STATUS] {worker_info}")
        print(f"[OK] System Running Normally")
        print(f"{'='*60}\n")

        # Simulate async processing (reduced time for more frequent updates)
        await _process_data()

        logger.info(f"[DONE] Completed {task_id}")
    except Exception as e:
        logger.error(f"Error in {task_id}: {e}")
    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)


async def _process_data():
    logger.info("[PROCESSING] Processing heartbeat data...")
    await asyncio.sleep(1)  # Reduced sleep time for faster heartbeat
    logger.info("[OK] Heartbeat data processed")
