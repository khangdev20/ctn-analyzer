from datetime import datetime
import logging
import asyncio

from notifiers.discord_webhook_sender import send_discord_message_webhook

logger = logging.getLogger(__name__)


async def run(worker):
    task_id = f"sample_task_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)

    try:
        logger.info(f"Running {task_id}")

        send_discord_message_webhook(content=f"")

        # giả lập xử lý async
        await _process_data()

        logger.info(f"Completed {task_id}")
    except Exception as e:
        logger.error(f"Error in {task_id}: {e}")
    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)


async def _process_data():
    logger.info("Processing data...")
    await asyncio.sleep(2)  # giả lập xử lý async
    logger.info("Data processed")
