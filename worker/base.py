import asyncio
import logging
import threading
from datetime import datetime, timezone
from .scheduler import run_scheduler_loop
from .tasks import sample_task, trending_intelligence_task, heartbeat_task

logger = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self):
        self.is_running = False
        self.active_tasks = []
        self.task_count = 0
        self._loop = None
        self._thread = None
        # Heartbeat tracking
        self.last_heartbeat = None
        self.heartbeat_count = 0
        self.start_timestamp = None

    def start(self):
        if self.is_running:
            logger.warning("Worker already running")
            return

        logger.info("Starting async background worker...")
        self.is_running = True
        self.start_timestamp = datetime.now(timezone.utc)

        # tạo loop riêng + chạy trong thread riêng
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            logger.info("[START] Starting scheduler loop...")
            self._loop.run_until_complete(run_scheduler_loop(self))
            # Should not reach here
            logger.info("[OK] Scheduler loop completed normally")
        except Exception as e:
            logger.error(f"[CRASH] Worker loop crashed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Set flag to indicate crash
            self.is_running = False

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

    async def _run_heartbeat_task(self):
        """Wrapper method for heartbeat task that runs every minute"""
        try:
            await heartbeat_task.run(self)
        except asyncio.CancelledError:
            logger.debug("Heartbeat task cancelled during shutdown")
            # Don't re-raise, let it complete gracefully
        except Exception as e:
            logger.error(f"Error running heartbeat task: {e}")

    async def _run_trending_intelligence_task(self):
        """Wrapper method for trending intelligence task that can be called by APScheduler"""
        start_time = asyncio.get_event_loop().time()
        timeout_seconds = 1800  # 30 minutes timeout

        try:
            logger.info(
                "[START] Starting trending intelligence task with timeout protection")
            logger.info(
                f"[TIMEOUT] Timeout limit: {timeout_seconds}s ({timeout_seconds/60:.1f} minutes)")
            logger.info(
                f"[TASKS] Current active tasks: {len(self.active_tasks)}")

            # Run with timeout protection
            logger.info("[CALL] Calling trending_intelligence_task.run()...")
            result = await asyncio.wait_for(
                trending_intelligence_task.run(self),
                timeout=timeout_seconds
            )

            execution_time = asyncio.get_event_loop().time() - start_time
            logger.info(
                f"[SUCCESS] Trending intelligence task completed in {execution_time:.1f}s")
            logger.info(
                f"[RESULT] Task result status: {result.get('status', 'unknown') if isinstance(result, dict) else 'non-dict result'}")

            return result

        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(
                f"[TIMEOUT] Trending intelligence task timed out after {execution_time:.1f}s (limit: {timeout_seconds}s)")

            # Log timeout details for debugging
            logger.error(
                f"[DEBUG] Active tasks at timeout: {len(self.active_tasks)}")
            logger.error(f"[DEBUG] Task IDs: {self.active_tasks}")

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(
                f"[ERROR] Error running trending intelligence task after {execution_time:.1f}s: {e}")

            # Clear any stuck tasks
            if hasattr(self, 'active_tasks'):
                stuck_tasks = [
                    task for task in self.active_tasks if 'trending_intelligence' in task]
                for task in stuck_tasks:
                    logger.warning(f"[CLEANUP] Clearing stuck task: {task}")
                    self.active_tasks.remove(task)

    async def _run_trending_intelligence_task_with_cleanup(self):
        """Enhanced wrapper with forced cleanup for trending intelligence task"""
        task_id = 'trending_intelligence_main'
        start_time = datetime.now(timezone.utc)

        logger.info("[STATUS]" * 12)
        logger.info(f"[TRIGGER] TRENDING INTELLIGENCE TASK TRIGGERED")
        logger.info(
            f"[TIME] Start Time: {start_time.strftime('%H:%M:%S UTC')}")
        logger.info(f"[TASK] Task ID: {task_id}")
        logger.info(
            f"[ACTIVE] Active Tasks: {len(self.active_tasks)} ({self.active_tasks})")
        logger.info(f"[STATUS] Worker running: {self.is_running}")
        logger.info(f"[COUNT] Total task count: {self.task_count}")
        logger.info("[STATUS]" * 12)

        try:
            # Force cleanup any existing stuck instances first
            logger.info("[CLEANUP] Step 1: Running pre-task cleanup...")
            cleanup_start = datetime.now(timezone.utc)
            await self._force_cleanup_job(task_id)
            cleanup_time = (datetime.now(timezone.utc) -
                            cleanup_start).total_seconds()
            logger.info(f"[STEP1] Step 1 completed in {cleanup_time:.2f}s")

            # Run the actual task
            logger.info(
                "[STEP2] Step 2: Starting trending intelligence pipeline...")
            pipeline_start = datetime.now(timezone.utc)
            result = await self._run_trending_intelligence_task()
            pipeline_time = (datetime.now(timezone.utc) -
                             pipeline_start).total_seconds()
            logger.info(f"[STEP2] Step 2 completed in {pipeline_time:.2f}s")

            total_time = (datetime.now(timezone.utc) -
                          start_time).total_seconds()
            logger.info("=" * 60)
            logger.info(
                f"[SUCCESS] TRENDING INTELLIGENCE TASK COMPLETED SUCCESSFULLY")
            logger.info(f"[TIME] Total execution time: {total_time:.2f}s")
            logger.info(f"[RESULT] Result: {result}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            error_time = (datetime.now(timezone.utc) -
                          start_time).total_seconds()
            logger.error("=" * 60)
            logger.error(f"[FAILED] TRENDING INTELLIGENCE TASK FAILED")
            logger.error(f"[TIME] Failed after: {error_time:.2f}s")
            logger.error(f"[ERROR] Error: {e}")
            logger.error(f"[TASK] Task ID: {task_id}")
            logger.error("=" * 60)

            # Always try cleanup on error
            try:
                logger.info("[CLEANUP] Running error cleanup...")
                await self._force_cleanup_job(task_id)
                logger.info("[OK] Error cleanup completed")
            except Exception as cleanup_error:
                logger.error(
                    f"[ERROR] Error during error cleanup: {cleanup_error}")

            raise

    async def _cleanup_stuck_jobs(self):
        """Periodic cleanup job to handle stuck processes"""
        try:
            logger.info("[CLEANUP] Running periodic stuck job cleanup...")

            # Clear active task tracking
            if hasattr(self, 'active_tasks'):
                old_count = len(self.active_tasks)
                self.active_tasks = [task for task in self.active_tasks
                                     if not any(stuck in task for stuck in ['trending_intelligence', 'sample_task'])]
                new_count = len(self.active_tasks)
                if old_count != new_count:
                    logger.info(
                        f"[CLEANUP] Cleaned {old_count - new_count} stuck task references")

            # Force cleanup the main intelligence job if needed
            await self._force_cleanup_job('trending_intelligence_main')

            logger.info("[OK] Periodic cleanup completed")

        except Exception as e:
            logger.error(f"[ERROR] Error in periodic cleanup: {e}")

    async def _force_cleanup_job(self, job_id):
        """Force cleanup a specific job instance"""
        logger.debug(f"[DEBUG] Starting cleanup for job: {job_id}")

        try:
            # Get current event loop and all tasks
            current_task = asyncio.current_task()
            all_tasks = asyncio.all_tasks()

            logger.debug(f"[DEBUG] Found {len(all_tasks)} total asyncio tasks")

            # Filter out completed tasks and current task
            active_tasks = [task for task in all_tasks
                            if not task.done() and task != current_task]

            logger.debug(
                f"[FOUND] Found {len(active_tasks)} active tasks (excluding current)")

            if active_tasks:
                logger.info(
                    f"[CLEANUP] Force cancelling {len(active_tasks)} running tasks for job {job_id}")

                # Log task details for debugging
                for i, task in enumerate(active_tasks):
                    task_name = getattr(
                        task, 'get_name', lambda: f'Task-{i}')()
                    logger.debug(
                        f"  - Task {i+1}: {task_name} (cancelled: {task.cancelled()})")

                # Cancel all active tasks
                cancelled_count = 0
                for task in active_tasks:
                    if not task.cancelled():
                        task.cancel()
                        cancelled_count += 1

                logger.info(
                    f"[CANCELLED] Sent cancel signal to {cancelled_count} tasks")

                # Wait briefly for tasks to cancel gracefully
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*active_tasks, return_exceptions=True),
                        timeout=10.0  # Increased timeout for cleanup
                    )
                    logger.info(
                        f"[OK] All tasks cancelled gracefully for job {job_id}")
                except asyncio.TimeoutError:
                    logger.warning(
                        f"[WARNING] Some tasks did not cancel within timeout for job {job_id}")
                    # Log which tasks are still running
                    still_running = [
                        task for task in active_tasks if not task.done()]
                    logger.warning(
                        f"[RUNNING] {len(still_running)} tasks still running after cleanup timeout")
                except Exception as gather_error:
                    logger.warning(
                        f"[WARNING] Error during task cancellation gather: {gather_error}")
            else:
                logger.debug(
                    f"[DEBUG] No active tasks to cleanup for job {job_id}")

            # Clean up worker active tasks list
            if hasattr(self, 'active_tasks'):
                old_count = len(self.active_tasks)
                self.active_tasks = [
                    t for t in self.active_tasks if job_id not in t]
                new_count = len(self.active_tasks)
                if old_count != new_count:
                    logger.info(
                        f"[CLEANUP] Cleaned {old_count - new_count} stuck tasks from worker active_tasks")

        except Exception as e:
            logger.error(f"[ERROR] Error in force cleanup for {job_id}: {e}")

        logger.debug(f"[DEBUG] Cleanup completed for job: {job_id}")
