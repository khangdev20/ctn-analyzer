import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def run(worker):
    """Heartbeat task - runs every minute to show worker is alive"""
    task_id = f"heartbeat_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)

    try:
        # Check if worker is still running
        if not worker.is_running:
            logger.info(f"⏹️ Worker stopping, skipping heartbeat {task_id}")
            return

        current_time = datetime.now(timezone.utc)
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S UTC')

        # Calculate uptime since worker started
        if not hasattr(worker, 'start_timestamp') or worker.start_timestamp is None:
            worker.start_timestamp = current_time

        uptime = current_time - worker.start_timestamp
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

        # Create status message
        status_info = {
            'timestamp': timestamp,
            'uptime': uptime_str,
            'total_tasks': worker.task_count,
            'active_tasks': len(worker.active_tasks),
            'task_id': task_id
        }

        # Log to console with visual formatting
        print(f"\n{'=' * 20}")
        print(f"[HEARTBEAT] WORKER HEARTBEAT")
        print(f"[TIME] Time: {timestamp}")
        print(f"[UPTIME] Uptime: {uptime_str}")
        print(
            f"[TASKS] Tasks: {worker.task_count} total | {len(worker.active_tasks)} active")
        print(f"[CURRENT] Current: {task_id}")
        print(f"[STATUS] Status: RUNNING")
        print(f"{'=' * 20}\n")

        # Also log to file
        logger.info(
            f"[HEARTBEAT] HEARTBEAT - {timestamp} | Uptime: {uptime_str} | Tasks: {worker.task_count}")

        # Update worker heartbeat info
        worker.last_heartbeat = current_time
        worker.heartbeat_count += 1

        # Quick async operation with cancellation check
        try:
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info(
                f"[CANCELLED] Heartbeat {task_id} cancelled gracefully")
            raise

        logger.info(f"[OK] Heartbeat {task_id} completed")

    except asyncio.CancelledError:
        logger.info(
            f"[SHUTDOWN] Heartbeat {task_id} cancelled during shutdown")
        raise  # Re-raise to let scheduler handle it properly
    except Exception as e:
        logger.error(f"[ERROR] Error in heartbeat {task_id}: {e}")
    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)
