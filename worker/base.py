import asyncio
import logging
import threading
from .scheduler import run_scheduler_loop
from .tasks import sample_task

logger = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self):
        self.is_running = False
        self.active_tasks = []
        self.task_count = 0
        self._loop = None
        self._thread = None

    def start(self):
        if self.is_running:
            logger.warning("Worker already running")
            return

        logger.info("Starting async background worker...")
        self.is_running = True

        # tạo loop riêng + chạy trong thread riêng
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(run_scheduler_loop(self))
        except Exception as e:
            logger.error(f"Worker loop crashed: {e}")

    def stop(self):
        logger.info("Stopping worker...")
        self.is_running = False
        if self._loop and not self._loop.is_closed():
            try:
                if self._loop.is_running():
                    self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError as e:
                logger.debug(f"Loop stop error (ignored): {e}")
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Worker stopped")

    async def _run_sample_task(self):
        """Wrapper method for sample task that can be called by APScheduler"""
        try:
            await sample_task.run(self)
        except Exception as e:
            logger.error(f"Error running sample task: {e}")
