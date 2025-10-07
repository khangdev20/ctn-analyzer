"""
Trending Intelligence Workflow - Main Task
Pipeline tự động phân tích các bài viết trending trên mạng xã hội
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from worker.features.data_collector import collect_trending_data
from worker.features.intelligence_pipeline import TrendingIntelligencePipeline
from worker.features.trending_config import get_config, get_metrics, get_topics_tracker
from notifiers.discord_webhook_sender import send_discord_message_webhook
from mock_data_provider import generate_mock_trending_data

logger = logging.getLogger(__name__)


class TrendingIntelligenceTask:
    """Main task orchestrator for the trending intelligence workflow"""

    def __init__(self):
        self.pipeline = TrendingIntelligencePipeline()
        self.batch_id = None
        self.config = get_config()
        self.metrics = get_metrics()
        self.topics_tracker = get_topics_tracker()
        self.start_time = None

    def generate_batch_id(self) -> str:
        """Generate unique batch ID with format YYYYMMDDTHHMMZ"""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y%m%dT%H%MZ")

    def cleanup_stuck_tasks(self, worker) -> int:
        """Clean up any stuck trending intelligence tasks"""
        if not hasattr(worker, 'active_tasks'):
            return 0

        stuck_tasks = [
            task for task in worker.active_tasks if 'trending_intelligence' in task]
        cleanup_count = 0

        for task in stuck_tasks:
            logger.warning(f"[CLEANUP] Cleaning up stuck task: {task}")
            worker.active_tasks.remove(task)
            cleanup_count += 1

        if cleanup_count > 0:
            logger.info(f"[CLEANUP] Cleaned up {cleanup_count} stuck tasks")

        return cleanup_count

    async def run_full_pipeline(self, worker) -> Dict:
        """Run complete trending intelligence pipeline"""
        self.batch_id = self.generate_batch_id()
        task_id = f"trending_intelligence_{self.batch_id}"
        self.start_time = datetime.now(timezone.utc)

        logger.info(
            f"[START] Starting Trending Intelligence Pipeline - Batch: {self.batch_id}")
        logger.info(f"[TASK] Task ID: {task_id}")
        logger.info(f"[TIME] Start Time: {self.start_time.isoformat()}")

        # Add timeout protection per stage
        stage_timeout = 600  # 10 minutes per stage

        try:
            # Stage 1: Collect Data (with timeout)
            logger.info("[STAGE1] Starting Stage 1 with timeout protection...")
            await self._send_progress_update(1, "Data Collection", "start", "Fetching trending posts from API")

            raw_data = await asyncio.wait_for(
                self._stage_1_collect_data(),
                timeout=stage_timeout
            )
            if not raw_data:
                logger.error("[ERROR] Stage 1 failed: No data collected")
                await self._send_progress_update(1, "Data Collection", "error", "No data collected from API")
                return {"status": "failed", "stage": 1, "batch_id": self.batch_id}

            posts_count = len(raw_data.get("data", []))
            await self._send_progress_update(1, "Data Collection", "success", f"{posts_count} posts collected")

            # Stage 2: Clean Data (with timeout)
            logger.info("[STAGE2] Starting Stage 2 with timeout protection...")
            await self._send_progress_update(2, "Data Cleaning", "start", "Processing and cleaning post data")

            cleaned_data = await asyncio.wait_for(
                self._stage_2_clean_data(raw_data),
                timeout=stage_timeout
            )
            if not cleaned_data:
                logger.error("[ERROR] Stage 2 failed: Data cleaning failed")
                await self._send_progress_update(2, "Data Cleaning", "error", "Data preprocessing failed")
                return {"status": "failed", "stage": 2, "batch_id": self.batch_id}

            cleaned_count = len(cleaned_data.get("posts", []))
            await self._send_progress_update(2, "Data Cleaning", "success", f"{cleaned_count} posts cleaned")

            # Stage 3: Calculate Raw Scores (with timeout)
            logger.info("[STAGE3] Starting Stage 3 with timeout protection...")
            await self._send_progress_update(3, "Score Calculation", "start", "Computing engagement metrics")

            scored_data = await asyncio.wait_for(
                self._stage_3_calculate_scores(cleaned_data),
                timeout=stage_timeout
            )
            if not scored_data:
                logger.error(
                    "[ERROR] Stage 3 failed: Score calculation failed")
                await self._send_progress_update(3, "Score Calculation", "error", "Performance scoring failed")
                return {"status": "failed", "stage": 3, "batch_id": self.batch_id}

            scored_count = len(scored_data.get("posts", []))
            await self._send_progress_update(3, "Score Calculation", "success", f"{scored_count} posts scored")

            # Stage 3.5: Content Quality Analysis (with timeout)
            logger.info("[STAGE3.5] Starting Content Quality Analysis...")
            await self._send_progress_update(4, "Content Analysis", "start", "Analyzing content quality and sentiment")

            content_analyzed_data = await asyncio.wait_for(
                self._stage_3_5_analyze_content_quality(scored_data),
                timeout=stage_timeout
            )
            if not content_analyzed_data:
                logger.warning("[WARNING] Content analysis failed, continuing with scored data")
                content_analyzed_data = scored_data
            else:
                analyzed_count = len(content_analyzed_data.get("content_analysis", {}).get("analyzed_posts", []))
                await self._send_progress_update(4, "Content Analysis", "success", f"{analyzed_count} posts analyzed for content quality")

            # Stage 4: Analyze Strategies (with timeout - longer for LLM calls)
            logger.info(
                "[STAGE4] Starting Stage 5 with extended timeout for LLM processing...")
            await self._send_progress_update(5, "Strategy Analysis", "start", "Running LLM analysis (may take 10-20 minutes)")

            analysis_results = await asyncio.wait_for(
                self._stage_4_analyze_strategies(content_analyzed_data),
                timeout=stage_timeout * 2  # 20 minutes for LLM processing
            )
            if not analysis_results:
                logger.error(
                    "[ERROR] Stage 5 failed: Strategy analysis failed")
                await self._send_progress_update(5, "Strategy Analysis", "error", "LLM analysis failed")
                return {"status": "failed", "stage": 5, "batch_id": self.batch_id}

            insights_count = len(analysis_results.get("insights", []))
            await self._send_progress_update(5, "Strategy Analysis", "success", f"{insights_count} insights generated")

            # Stage 6: Format & Notify (with timeout)
            logger.info("[STAGE6] Starting Stage 6 with timeout protection...")
            await self._send_progress_update(6, "Format & Notify", "start", "Generating final report")

            notification_result = await asyncio.wait_for(
                self._stage_5_format_notify(analysis_results),
                timeout=stage_timeout
            )

            if notification_result:
                await self._send_progress_update(6, "Format & Notify", "success", "Report sent to Discord")
            else:
                await self._send_progress_update(6, "Format & Notify", "error", "Failed to send final report")

            logger.info(
                f"[SUCCESS] Pipeline completed successfully - Batch: {self.batch_id}")

            # Record successful run metrics
            processing_time = (datetime.now(timezone.utc) -
                               self.start_time).total_seconds()
            posts_count = len(content_analyzed_data.get("posts", []))
            self.metrics.record_run(True, processing_time, posts_count)

            # Update topics tracker
            trending_topics = analysis_results.get(
                "aggregate_metrics", {}).get("trending_tags", [])
            topic_data = [{"name": tag, "score": 50}
                          for tag in trending_topics[:10]]  # Default score
            self.topics_tracker.update_topics(topic_data)

            return {
                "status": "success",
                "batch_id": self.batch_id,
                "stages_completed": 6,
                "total_posts_analyzed": posts_count,
                "processing_time_seconds": processing_time,
                "notification_sent": notification_result,
                "content_analysis_completed": bool(content_analyzed_data.get("content_analysis"))
            }

        except asyncio.TimeoutError as e:
            processing_time = (datetime.now(timezone.utc) -
                               self.start_time).total_seconds()
            error_msg = f"Pipeline timed out after {processing_time:.1f}s"
            logger.error(f"[TIMEOUT] {error_msg}")

            # Send timeout notification
            await self._send_progress_update(0, "Pipeline Timeout", "timeout", f"Exceeded {processing_time:.1f}s limit")

            # Record timeout as failed run
            self.metrics.record_run(False, processing_time, 0, error_msg)

            return {
                "status": "timeout",
                "batch_id": self.batch_id,
                "error": error_msg,
                "processing_time_seconds": processing_time
            }

        except Exception as e:
            processing_time = (datetime.now(timezone.utc) -
                               self.start_time).total_seconds()
            logger.error(
                f"[ERROR] Pipeline failed - Batch {self.batch_id} after {processing_time:.1f}s: {e}")

            # Send error notification
            await self._send_progress_update(0, "Pipeline Error", "error", f"Unexpected error: {str(e)[:100]}")

            # Record failed run metrics
            self.metrics.record_run(False, processing_time, 0, str(e))

            return {
                "status": "error",
                "batch_id": self.batch_id,
                "error": str(e),
                "processing_time_seconds": processing_time
            }

    async def _stage_1_collect_data(self) -> Optional[Dict]:
        """Stage 1: Collect Data - Thu thập dữ liệu trending with fallback to mock data"""
        logger.info("[STAGE1] Stage 1: Collecting trending data...")

        try:
            # Try to collect real data first
            def collect_data():
                return collect_trending_data(num_pages=self.config.batch_size, key='trending')

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            filename = await loop.run_in_executor(None, collect_data)

            if filename:
                # Read the collected data
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if we got actual data
                if data.get('data') and len(data['data']) > 0:
                    # Save to structured directory
                    await self._save_raw_data(data, filename)
                    logger.info(
                        f"[SUCCESS] Stage 1 completed: {len(data.get('data', []))} posts collected from API")
                    return data

            # If no data from API, fall back to mock data
            logger.warning(
                "[FALLBACK] API data unavailable, using mock data for testing")
            return await self._use_mock_data_fallback()

        except Exception as e:
            logger.error(f"[ERROR] Stage 1 API error: {e}")
            logger.info("[FALLBACK] Using mock data due to API error")
            return await self._use_mock_data_fallback()

    async def _use_mock_data_fallback(self) -> Optional[Dict]:
        """Generate mock data when real API is unavailable"""
        try:
            logger.info("[MOCK] Generating mock trending data...")

            # Generate mock data
            mock_data = generate_mock_trending_data(25)

            # Add batch information
            mock_data["batch_id"] = self.batch_id
            mock_data["source"] = "mock_fallback"

            # Save mock data to structured directory
            await self._save_raw_data(mock_data, f"mock_{self.batch_id}.json")

            logger.info(
                f"[SUCCESS] Mock data generated: {len(mock_data.get('data', []))} posts")
            return mock_data

        except Exception as e:
            logger.error(f"[ERROR] Mock data generation failed: {e}")
            return None

    async def _stage_2_clean_data(self, raw_data: Dict) -> Optional[Dict]:
        """Stage 2: Clean Data - Chuẩn hoá và lọc dữ liệu"""
        logger.info("[STAGE2] Stage 2: Cleaning and preprocessing data...")

        try:
            cleaned_data = await self.pipeline.clean_data(raw_data, self.batch_id)

            logger.info(
                f"[SUCCESS] Stage 2 completed: {len(cleaned_data.get('posts', []))} posts cleaned")
            return cleaned_data

        except Exception as e:
            logger.error(f"[ERROR] Stage 2 error: {e}")
            return None

    async def _stage_3_calculate_scores(self, cleaned_data: Dict) -> Optional[Dict]:
        """Stage 3: Calculate Raw Scores - Tính toán điểm định lượng"""
        logger.info("[STAGE3] Stage 3: Calculating performance scores...")

        try:
            scored_data = await self.pipeline.calculate_scores(cleaned_data, self.batch_id)

            logger.info(
                f"[SUCCESS] Stage 3 completed: Scores calculated for {len(scored_data.get('posts', []))} posts")
            return scored_data

        except Exception as e:
            logger.error(f"[ERROR] Stage 3 error: {e}")
            return None

    async def _stage_3_5_analyze_content_quality(self, scored_data: Dict) -> Optional[Dict]:
        """Stage 3.5: Analyze Content Quality - AI-powered content analysis"""
        logger.info("[STAGE3.5] Stage 3.5: Analyzing content quality and sentiment...")

        try:
            # Import content analysis components
            from worker.features.content_analyzer import ContentAnalyzer
            from worker.features.content_analysis_prompts import ContentAnalysisPromptHandler
            
            content_analyzer = ContentAnalyzer()
            prompt_handler = ContentAnalysisPromptHandler()
            
            posts = scored_data.get("posts", [])
            
            # Run content analysis
            content_analysis_results = await content_analyzer.analyze_content_batch(posts)
            
            # Generate Discord-ready content analysis report
            discord_content_report = await prompt_handler.generate_content_analysis_discord_report(posts)
            
            # Merge with existing scored data
            enhanced_data = scored_data.copy()
            enhanced_data.update({
                "content_analysis": content_analysis_results,
                "discord_content_report": discord_content_report,
                "stage": "content_analyzed"
            })
            
            logger.info(
                f"[SUCCESS] Stage 3.5 completed: Content analysis for {len(content_analysis_results.get('analyzed_posts', []))} posts")
            return enhanced_data

        except Exception as e:
            logger.error(f"[ERROR] Stage 3.5 error: {e}")
            return None

    async def _stage_4_analyze_strategies(self, scored_data: Dict) -> Optional[Dict]:
        """Stage 4: Analyze Strategies - Phân tích chiến lược và pattern"""
        logger.info("[STAGE4] Stage 4: Analyzing content strategies...")

        try:
            analysis_results = await self.pipeline.analyze_strategies(scored_data, self.batch_id)

            logger.info(
                f"[SUCCESS] Stage 4 completed: Strategy analysis for {len(analysis_results.get('insights', []))} insights")
            return analysis_results

        except Exception as e:
            logger.error(f"[ERROR] Stage 4 error: {e}")
            return None

    async def _stage_5_format_notify(self, analysis_results: Dict) -> bool:
        """Stage 5: Format & Notify - Gửi báo cáo qua Discord"""
        logger.info(
            "[STAGE5] Stage 5: Formatting and sending notifications...")

        try:
            report = await self.pipeline.format_report(analysis_results, self.batch_id)

            # Send to Discord webhook
            success = await self._send_discord_notification(report)

            logger.info(
                f"[SUCCESS] Stage 5 completed: Notification sent = {success}")
            return success

        except Exception as e:
            logger.error(f"[ERROR] Stage 5 error: {e}")
            return False

    async def _save_raw_data(self, data: Dict, original_filename: str):
        """Save raw data to structured directory"""
        try:
            now = datetime.now(timezone.utc)
            dir_path = f"data/raw/{now.year:04d}/{now.month:02d}/{now.day:02d}/{now.hour:02d}"

            os.makedirs(dir_path, exist_ok=True)

            structured_data = {
                "batch_id": self.batch_id,
                "source": "trending_feed",
                "fetched_at": now.isoformat(),
                "items": data.get("data", []),
                "metadata": {
                    "total_items": data.get("total_items", 0),
                    "cleaned_items_count": data.get("cleaned_items_count", 0),
                    "original_filename": original_filename
                }
            }

            filepath = f"{dir_path}/{self.batch_id}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)

            logger.info(f"[SAVED] Raw data saved to: {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save structured raw data: {e}")

    async def _send_discord_notification(self, report: Dict) -> bool:
        """Send formatted report to Discord using rich embeds"""
        try:
            # Check if report already has Discord embed
            if "discord_embed" in report:
                embed_payload = report["discord_embed"]
                logger.info(
                    "[DISCORD] Using pre-generated Discord embed from report")
            else:
                # Generate Discord embed on-the-fly
                logger.info(
                    "[EMBED] Generating Discord embed for notification...")
                embed_payload = await self.pipeline.create_discord_embed(report, {
                    'title_prefix': 'Trending Intelligence',
                    'max_fields': 5,
                    'show_links': False,
                    'include_footer_timestamp': True
                })

            # Send embed payload to Discord
            def send_embed():
                return send_discord_message_webhook(embed_payload)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, send_embed)

            if result:
                logger.info(
                    "[SUCCESS] Discord embed notification sent successfully")
            else:
                logger.error("[ERROR] Discord embed notification failed")

            return result is not None

        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            # Fallback to simple text message
            try:
                fallback_message = self._format_discord_message(report)

                def send_fallback():
                    return send_discord_message_webhook(fallback_message)

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, send_fallback)
                logger.info("[SENT] Sent fallback text message to Discord")
                return result is not None
            except:
                return False

    async def _send_progress_update(self, stage: int, stage_name: str, status: str, details: str = "") -> None:
        """Log progress update (Discord messaging disabled)"""
        try:
            # Progress stage indicators (text-based for Windows compatibility)
            stage_names = {
                1: "[DATA]",       # Data Collection
                2: "[CLEAN]",      # Data Cleaning
                3: "[SCORE]",      # Score Calculation
                4: "[CONTENT]",    # Content Analysis
                5: "[ANALYZE]",    # Strategy Analysis
                6: "[NOTIFY]"      # Format & Notify
            }
            
            status_prefixes = {
                "start": "[START]",
                "success": "[SUCCESS]",
                "error": "[ERROR]",
                "timeout": "[TIMEOUT]"
            }

            stage_prefix = stage_names.get(stage, "[STAGE]")
            status_prefix = status_prefixes.get(status, "[INFO]")

            elapsed_time = (datetime.now(timezone.utc) -
                            self.start_time).total_seconds()

            # Log progress locally instead of sending to Discord
            progress_bar = "#" * stage + "-" * (6 - stage)
            log_message = f"{status_prefix} Stage {stage}: {stage_name} {stage_prefix} | Progress: [{progress_bar}] {stage}/6 | Elapsed: {elapsed_time:.1f}s"

            if details:
                log_message += f" | Details: {details}"

            logger.info(log_message)

            # Discord messaging disabled - only log locally
            logger.debug(
                f"[PROGRESS] Stage {stage} - {status} (Discord updates disabled)")

        except Exception as e:
            logger.debug(f"Progress logging failed: {e}")

    def _format_discord_message(self, report: Dict) -> str:
        """Format report for Discord message"""
        batch_id = report.get("batch_id", "Unknown")
        summary = report.get("summary", {})
        top_insights = report.get("top_insights", [])

        message = f"""**Trending Intelligence Report - {batch_id}**
            **Summary:**
            • Total Posts Analyzed: {summary.get('total_posts', 0)}
            • Top Performing Tags: {', '.join(summary.get('trending_tags', [])[:3])}
            • Average Engagement Score: {summary.get('avg_engagement_score', 0):.2f}
            • Success Pattern Score: {summary.get('success_pattern_score', 0):.2f}

            **Key Insights:**
        """

        for i, insight in enumerate(top_insights[:3], 1):
            message += f"{i}. {insight.get('title', 'N/A')}\n   {insight.get('description', 'N/A')}\n\n"

        message += f"Report generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"

        return message


# Task runner function for the scheduler
async def run(worker):
    """Main task runner called by the scheduler"""
    task_id = f"trending_intelligence_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)

    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info(f"[START] TRENDING INTELLIGENCE TASK RUNNER STARTED")
    logger.info(f"[TASK] Task ID: {task_id}")
    logger.info(f"[TIME] Start time: {start_time.isoformat()}")
    logger.info(f"[COUNT] Worker task count: {worker.task_count}")
    logger.info(
        f"[ACTIVE] Active tasks: {len(worker.active_tasks)} - {worker.active_tasks}")
    logger.info("=" * 60)

    try:
        logger.info(
            f"[INSTANCE] Creating TrendingIntelligenceTask instance...")
        task = TrendingIntelligenceTask()

        logger.info(f"[PIPELINE] Running full pipeline for {task_id}...")
        result = await task.run_full_pipeline(worker)

        execution_time = (datetime.now(timezone.utc) -
                          start_time).total_seconds()
        logger.info("[SUCCESS]" * 6)
        logger.info(
            f"[SUCCESS] TRENDING INTELLIGENCE TASK COMPLETED SUCCESSFULLY")
        logger.info(f"[TIME] Total execution time: {execution_time:.2f}s")
        logger.info(
            f"[RESULT] Result status: {result.get('status', 'unknown')}")
        logger.info(f"[TASK] Task ID: {task_id}")
        logger.info("[SUCCESS]" * 6)

        return result

    except Exception as e:
        execution_time = (datetime.now(timezone.utc) -
                          start_time).total_seconds()
        logger.error("[ERROR]" * 6)
        logger.error(f"[FAILED] TRENDING INTELLIGENCE TASK FAILED")
        logger.error(f"[TIME] Failed after: {execution_time:.2f}s")
        logger.error(f"[ERROR] Error: {str(e)}")
        logger.error(f"[TASK] Task ID: {task_id}")
        logger.error("[ERROR]" * 6)

        return {"status": "error", "error": str(e), "task_id": task_id, "execution_time": execution_time}
    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)
            logger.info(f"[REMOVED] Removed {task_id} from active tasks")
