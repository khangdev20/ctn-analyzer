"""
Background Worker Module
Handles all background tasks and processes for the bot.
"""
import threading
import time
import logging
import schedule
from datetime import datetime
from typing import List, Dict, Any
import requests
from config import Config
from llms.llm_models import LLMModels
from notifiers.discord_bot_sender import send_discord_notification

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Main background worker class that handles scheduled tasks."""

    def __init__(self):
        self.is_running = False
        self.worker_thread = None
        self.active_tasks = []
        self.task_count = 0

    def start(self):
        """Start the background worker."""
        if self.is_running:
            logger.warning("Worker is already running")
            return

        logger.info("Starting background worker...")
        self.is_running = True

        # Schedule tasks
        self._schedule_tasks()

        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._run_scheduler,
            daemon=True
        )
        self.worker_thread.start()

        logger.info("Background worker started successfully")

    def stop(self):
        """Stop the background worker."""
        logger.info("Stopping background worker...")
        self.is_running = False

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)

        logger.info("Background worker stopped")

    def _schedule_tasks(self):
        """Schedule all background tasks."""
        # Example: Schedule a task to run every minute
        schedule.every(20).seconds.do(self._sample_task)

        # Example: Schedule a task to run every hour
        schedule.every(1).hours.do(self._hourly_maintenance)

        # Example: Schedule a daily task
        schedule.every().day.at("02:00").do(self._daily_cleanup)

        logger.info("Tasks scheduled successfully")

    def _run_scheduler(self):
        """Run the task scheduler in a loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retrying\

    # Async Scheduler
    def _schedule_tasks_async(self):
        """Schedule all background tasks."""
        # Example: Schedule a task to run every minute
        schedule.every(20).seconds.do(self._sample_task)
        logger.info("Tasks scheduled successfully")

    async def _run_scheduler_async(self):
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retrying

    def _sample_task(self):
        """Sample background task - replace with your actual logic."""
        task_id = f"sample_task_{self.task_count}"
        self.task_count += 1

        try:
            self.active_tasks.append(task_id)
            logger.info(f"Running sample task {task_id}")

            send_discord_notification(
                channel_id="1420430652326674523",
                title="success",
                description="tést"
            )

            # Your bot logic here
            # Example: Process data, make API calls, etc.
            self._process_data()

            logger.info(f"Completed sample task {task_id}")

        except Exception as e:
            logger.error(f"Error in sample task {task_id}: {e}")
        finally:
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

    def _hourly_maintenance(self):
        """Hourly maintenance task."""
        task_id = f"hourly_maintenance_{int(time.time())}"

        try:
            self.active_tasks.append(task_id)
            logger.info(f"Running hourly maintenance {task_id}")

            # Example maintenance tasks:
            # - Clean up temporary files
            # - Update statistics
            # - Check system health
            self._cleanup_temp_files()
            self._update_statistics()

            logger.info(f"Completed hourly maintenance {task_id}")

        except Exception as e:
            logger.error(f"Error in hourly maintenance {task_id}: {e}")
        finally:
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

    def _daily_cleanup(self):
        """Daily cleanup task."""
        task_id = f"daily_cleanup_{datetime.now().strftime('%Y%m%d')}"

        try:
            self.active_tasks.append(task_id)
            logger.info(f"Running daily cleanup {task_id}")

            # Example cleanup tasks:
            # - Archive old logs
            # - Clean database
            # - Generate reports
            self._archive_logs()
            self._generate_daily_report()

            logger.info(f"Completed daily cleanup {task_id}")

        except Exception as e:
            logger.error(f"Error in daily cleanup {task_id}: {e}")
        finally:
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

    def _process_data(self):
        """Process data - implement your bot's main logic here."""
        # Example: Fetch data from an API
        try:
            # Replace with your actual data processing logic
            logger.info("Processing data...")

            # Example API call (replace with your actual endpoints)
            # response = requests.get('https://api.example.com/data', timeout=Config.API_TIMEOUT)
            # data = response.json()

            # Process the data
            # your_processing_logic(data)

            time.sleep(2)  # Simulate processing time
            logger.info("Data processing completed")

        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        logger.info("Cleaning up temporary files...")
        # Implement cleanup logic here
        pass

    def _update_statistics(self):
        """Update system statistics."""
        logger.info("Updating statistics...")
        # Implement statistics update logic here
        pass

    def _archive_logs(self):
        """Archive old log files."""
        logger.info("Archiving old logs...")
        # Implement log archiving logic here
        pass

    def _generate_daily_report(self):
        """Generate daily report."""
        logger.info("Generating daily report...")
        # Implement report generation logic here
        pass

    def get_active_tasks_count(self) -> int:
        """Get the number of currently active tasks."""
        return len(self.active_tasks)

    def get_active_tasks(self) -> List[str]:
        """Get list of currently active tasks."""
        return self.active_tasks.copy()

    def add_custom_task(self, task_func, *args, **kwargs):
        """Add a custom task to be executed."""
        try:
            task_id = f"custom_task_{int(time.time())}"
            self.active_tasks.append(task_id)

            logger.info(f"Executing custom task {task_id}")
            result = task_func(*args, **kwargs)
            logger.info(f"Custom task {task_id} completed")

            return result

        except Exception as e:
            logger.error(f"Error in custom task {task_id}: {e}")
            raise
        finally:
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
