"""
Enhanced Background Worker with Main Flow Orchestrator
Supports both individual engine execution and complete pipeline orchestration
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone
from .scheduler import run_scheduler_loop

# Import all 7 analysis engine tasks
from .tasks.content_analysis_task import run_content_analysis_task
from .tasks.engagement_intelligence_task import run_engagement_intelligence_task
from .tasks.network_intelligence_task import run_network_intelligence_task
from .tasks.temporal_analytics_task import run_temporal_analytics_task
from .tasks.strategic_intelligence_task import run_strategic_intelligence_task
from .tasks.trending_prediction_task import run_trending_prediction_task
from .tasks.meta_trend_intelligence_task import run_weekly_meta_trend_task

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Enhanced Background Worker with Main Flow Orchestrator support."""

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

    # ===============================
    # MAIN FLOW ORCHESTRATOR
    # ===============================

    async def _run_main_flow_orchestrator(self):
        """
        Main Flow Orchestrator - Complete 7-engine sequential pipeline
        Executes all analysis engines in order with Discord reporting
        """
        try:
            logger.info(
                "🚀 [MAIN FLOW] Starting Main Intelligence Flow Orchestrator")
            logger.info(
                "🎯 [MAIN FLOW] Sequential execution of all 7 analysis engines")

            # Import main flow orchestrator
            from pipeline.main_flow import run_main_flow

            # Execute the complete pipeline
            result = await run_main_flow()

            if result.get('status') == 'success':
                successful_engines = result.get('successful_engines', 0)
                total_engines = result.get('total_engines', 7)
                execution_time = result.get('execution_time_seconds', 0)

                logger.info(f"✅ [MAIN FLOW] Pipeline completed successfully!")
                logger.info(
                    f"📊 [MAIN FLOW] Engines: {successful_engines}/{total_engines} successful")
                logger.info(
                    f"⏱️ [MAIN FLOW] Total runtime: {execution_time:.1f}s")
                logger.info(
                    f"📋 [MAIN FLOW] Batch ID: {result.get('batch_id')}")
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ [MAIN FLOW] Pipeline failed: {error_msg}")

            return result

        except ImportError as e:
            logger.error(
                f"❌ [MAIN FLOW] Import error - Main flow orchestrator not available: {e}")
            return {
                'status': 'error',
                'error': f'Main flow orchestrator import failed: {str(e)}',
                'timestamp': str(datetime.now(timezone.utc))
            }
        except Exception as e:
            logger.error(f"❌ [MAIN FLOW] Main flow orchestrator error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': str(datetime.now(timezone.utc))
            }

    # ===============================
    # INDIVIDUAL ENGINE TASK METHODS
    # ===============================

    async def _run_content_analysis_task(self):
        """Content Analysis Engine - content quality and topic analysis"""
        try:
            logger.info("[ENGINE] Starting Content Analysis Engine")
            result = await run_content_analysis_task()
            logger.info(
                f"[ENGINE] Content Analysis completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Content Analysis Engine error: {e}")

    async def _run_engagement_intelligence_task(self):
        """Engagement Intelligence Engine - audience interaction patterns"""
        try:
            logger.info("[ENGINE] Starting Engagement Intelligence Engine")
            result = await run_engagement_intelligence_task()
            logger.info(
                f"[ENGINE] Engagement Intelligence completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Engagement Intelligence Engine error: {e}")

    async def _run_network_intelligence_task(self):
        """Network Intelligence Engine - social network influence mapping"""
        try:
            logger.info("[ENGINE] Starting Network Intelligence Engine")
            result = await run_network_intelligence_task()
            logger.info(
                f"[ENGINE] Network Intelligence completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Network Intelligence Engine error: {e}")

    async def _run_temporal_analytics_task(self):
        """Temporal Analytics Engine - time-based performance optimization"""
        try:
            logger.info("[ENGINE] Starting Temporal Analytics Engine")
            result = await run_temporal_analytics_task()
            logger.info(
                f"[ENGINE] Temporal Analytics completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Temporal Analytics Engine error: {e}")

    async def _run_strategic_intelligence_task(self):
        """Strategic Intelligence Engine - campaign effectiveness analysis"""
        try:
            logger.info("[ENGINE] Starting Strategic Intelligence Engine")
            result = await run_strategic_intelligence_task()
            logger.info(
                f"[ENGINE] Strategic Intelligence completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Strategic Intelligence Engine error: {e}")

    async def _run_trending_prediction_task(self):
        """Trending Prediction Engine - viral content forecasting"""
        try:
            logger.info("[ENGINE] Starting Trending Prediction Engine")
            result = await run_trending_prediction_task()
            logger.info(
                f"[ENGINE] Trending Prediction completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Trending Prediction Engine error: {e}")

    async def _run_meta_trend_intelligence_task(self):
        """Meta-Trend Intelligence Engine - weekly cross-engine analysis"""
        try:
            logger.info(
                "[ENGINE] Starting Meta-Trend Intelligence Engine (Weekly)")
            result = await run_weekly_meta_trend_task()
            logger.info(
                f"[ENGINE] Meta-Trend Intelligence completed: {result.get('status', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"[ENGINE] Meta-Trend Intelligence Engine error: {e}")

    # ===============================
    # LEGACY CLEANUP (DEPRECATED)
    # ===============================

    async def _cleanup_stuck_jobs(self):
        """Periodic cleanup job for all analysis engines"""
        try:
            logger.info(
                "[CLEANUP] Running periodic cleanup for all analysis engines...")

            # Clear active task tracking for all engines
            if hasattr(self, 'active_tasks'):
                old_count = len(self.active_tasks)
                # Remove stuck tasks from all engines
                engine_patterns = [
                    'content_analysis', 'engagement_intelligence', 'network_intelligence',
                    'temporal_analytics', 'strategic_intelligence', 'trending_prediction',
                    'meta_trend_intelligence'
                ]

                self.active_tasks = [
                    task for task in self.active_tasks
                    if not any(pattern in task for pattern in engine_patterns)
                ]

                new_count = len(self.active_tasks)
                if old_count != new_count:
                    logger.info(
                        f"[CLEANUP] Cleaned {old_count - new_count} stuck engine tasks")

            logger.info("[OK] Periodic cleanup completed")

        except Exception as e:
            logger.error(f"[ERROR] Error in periodic cleanup: {e}")
