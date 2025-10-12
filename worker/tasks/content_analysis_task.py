"""
Content Analysis Task
Specialized task for running comprehensive content analysis with Discord reporting
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from worker.features.content_analyzer import ContentAnalyzer
from worker.features.content_analysis_prompts import ContentAnalysisPromptHandler
from worker.features.data_collector import collect_trending_data
from notifiers.discord_webhook_sender import send_discord_message_webhook
from mock_data_provider import generate_mock_trending_data

logger = logging.getLogger(__name__)


class ContentAnalysisTask:
    """Specialized task for content analysis with Discord integration"""

    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.prompt_handler = ContentAnalysisPromptHandler()
        self.batch_id = None

    def generate_batch_id(self) -> str:
        """Generate unique batch ID for this analysis"""
        now = datetime.now(timezone.utc)
        return f"content_analysis_{now.strftime('%Y%m%dT%H%MZ')}"

    async def run_content_analysis_workflow(self, data_source: str = "api", data_type: str = "latest", num_posts: int = 25, send_discord: bool = True) -> Dict:
        """
        Run complete content analysis workflow with Discord reporting

        Args:
            data_source: "api" for real data, "mock" for test data
            data_type: "latest" for newest posts, "trending" for trending posts (when data_source="api")
            num_posts: Number of posts to analyze (default 25)
            send_discord: Whether to send Discord notifications (default True)

        Returns:
            Dictionary with analysis results and Discord message status
        """
        self.batch_id = self.generate_batch_id()
        start_time = datetime.now(timezone.utc)

        logger.info(f"[CONTENT] Starting analysis - {data_type.upper()}")

        try:
            # Step 1: Data Collection
            posts_data = await self._collect_posts_data(data_source, data_type, num_posts)

            if not posts_data:
                logger.error("[ERROR] No data collected for analysis")
                return {
                    "status": "failed",
                    "error": "No data available for analysis",
                    "batch_id": self.batch_id
                }

            logger.info(f"[DATA] Collected {len(posts_data)} posts")

            # Step 2: Run Content Analysis
            analysis_results = await self.content_analyzer.analyze_content_batch(posts_data)

            if not analysis_results.get("analyzed_posts"):
                logger.error("[ERROR] Content analysis failed")
                return {
                    "status": "failed",
                    "error": "Content analysis produced no results",
                    "batch_id": self.batch_id
                }

            # Step 3 & 4: Discord Reporting (conditional)
            discord_success = False
            if send_discord:
                discord_report = await self.prompt_handler.generate_content_analysis_discord_report(posts_data, data_type)

                discord_success = await self._send_discord_report(discord_report)
                logger.info(
                    f"[DISCORD] {'✅ Sent' if discord_success else '❌ Failed'}")

            # Step 5: Save Results
            await self._save_analysis_results(analysis_results, posts_data)

            # Calculate final metrics
            processing_time = (datetime.now(timezone.utc) -
                               start_time).total_seconds()
            analyzed_count = len(analysis_results.get("analyzed_posts", []))

            result = {
                "status": "success",
                "batch_id": self.batch_id,
                "processing_time_seconds": processing_time,
                "total_posts_collected": len(posts_data),
                "posts_analyzed": analyzed_count,
                "discord_sent": discord_success,
                "analysis_summary": {
                    "avg_readability": analysis_results.get("aggregate_metrics", {}).get("avg_readability", 0),
                    "avg_content_quality": analysis_results.get("aggregate_metrics", {}).get("avg_content_quality", 0),
                    "dominant_sentiment": analysis_results.get("aggregate_metrics", {}).get("dominant_sentiment", "unknown"),
                    "top_emotions": analysis_results.get("aggregate_metrics", {}).get("top_emotions", [])
                }
            }

            logger.info(f"[CONTENT] Completed in {processing_time:.1f}s")
            return result

        except Exception as e:
            processing_time = (datetime.now(timezone.utc) -
                               start_time).total_seconds()
            logger.error(
                f"[ERROR] Content analysis workflow failed after {processing_time:.1f}s: {e}")

            return {
                "status": "error",
                "batch_id": self.batch_id,
                "error": str(e),
                "processing_time_seconds": processing_time
            }

    async def _collect_posts_data(self, data_source: str, data_type: str, num_posts: int) -> List[Dict]:
        """Collect posts data from specified source"""
        try:
            if data_source == "mock":
                logger.info("[MOCK] Using mock data for content analysis")
                mock_data = generate_mock_trending_data(num_posts)
                return mock_data.get("data", [])
            else:
                logger.info(
                    f"[API] Collecting real data from API - Type: {data_type.upper()} Posts")
                # Collect data based on specified type (latest or trending)

                def collect_data():
                    # Calculate pages needed to get at least 40 items (minimum 2 pages, up to 5 pages max)
                    # Each page typically has ~20 items
                    min_items = max(40, num_posts)  # Ensure at least 40 items
                    # Round up, min 2 pages, max 5 pages
                    pages_needed = max(2, min(5, (min_items + 19) // 20))
                    logger.info(
                        f"[DATA_COLLECTION] Requesting {pages_needed} pages to collect minimum {min_items} items")
                    return collect_trending_data(num_pages=pages_needed, key=data_type)

                loop = asyncio.get_event_loop()
                collection_result = await loop.run_in_executor(None, collect_data)

                # Check if we got S3 cloud storage result
                if collection_result and isinstance(collection_result, dict) and collection_result.get('s3_key'):
                    from worker.features.data_collector import load_data_from_s3

                    # Load data directly from S3 cloud storage
                    data = load_data_from_s3(collection_result['s3_key'])

                    if data and data.get('data'):
                        posts = data['data']
                        logger.info(
                            f"[SUCCESS] Collected {len(posts)} posts from S3 cloud storage")
                        return posts[:num_posts]  # Limit to requested number

                # Fallback to mock data if API fails
                logger.warning("[FALLBACK] API failed, using mock data")
                mock_data = generate_mock_trending_data(num_posts)
                return mock_data.get("data", [])

        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            # Final fallback to mock data
            try:
                mock_data = generate_mock_trending_data(num_posts)
                return mock_data.get("data", [])
            except:
                return []

    async def _send_discord_report(self, discord_report: str) -> bool:
        """Send full content analysis report to Discord using rich embeds"""
        try:
            if not discord_report:
                logger.warning("[DISCORD] No report content to send")
                return False

            # Import Discord webhook sender for rich embeds
            from notifiers.discord_webhook_sender import DiscordWebhookSender
            discord_sender = DiscordWebhookSender()

            # Split long reports into multiple embed fields if needed
            max_description_length = 4000  # Discord embed description limit

            if len(discord_report) <= max_description_length:
                # Send as single embed
                success = await discord_sender.send_rich_embed(
                    title="🔍 AI Content Analysis Report",
                    description=discord_report,
                    color=0x00FF88,  # Green color
                    footer={
                        "text": f"Report ID: {self.batch_id} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                )
            else:
                # Split into multiple fields for very long reports
                # First send title and summary
                summary_section = discord_report[:max_description_length]
                remaining_content = discord_report[max_description_length:]

                # Find a good break point (end of line)
                if '\n' in summary_section[-200:]:
                    break_point = summary_section.rfind('\n', -200)
                    if break_point > max_description_length - 300:
                        remaining_content = summary_section[break_point:] + \
                            remaining_content
                        summary_section = summary_section[:break_point]

                # Send main report
                success = await discord_sender.send_rich_embed(
                    title="🔍 AI Content Analysis Report (Full)",
                    description=summary_section,
                    color=0x00FF88,
                    footer={
                        "text": f"Report ID: {self.batch_id} • Full report (continued below)"}
                )

                # Send continuation if there's remaining content
                if remaining_content.strip() and success:
                    # Split remaining content into 1000-char chunks for fields
                    chunk_size = 1000
                    chunks = [remaining_content[i:i+chunk_size]
                              for i in range(0, len(remaining_content), chunk_size)]

                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            await discord_sender.send_rich_embed(
                                title=f"📋 Report Continuation {i+1}",
                                description=chunk,
                                color=0x00AA66,
                                footer={
                                    "text": f"Report ID: {self.batch_id} • Part {i+2}"}
                            )

            if success:
                logger.info(
                    "[DISCORD] Full content analysis report sent successfully")
                return True
            else:
                logger.error(
                    "[DISCORD] Failed to send content analysis report")
                return False

        except Exception as e:
            logger.error(f"Discord sending failed: {e}")
            return False

    async def _save_analysis_results(self, analysis_results: Dict, posts_data: List[Dict]):
        """Save analysis results to S3 storage"""
        try:
            from data_access.s3_store import s3_write_json, build_key

            now = datetime.now(timezone.utc)
            year = now.strftime('%Y')
            month = now.strftime('%m')

            # Prepare comprehensive report
            report_data = {
                "batch_id": self.batch_id,
                "analysis_type": "content_analysis",
                "timestamp": now.isoformat(),
                "metadata": {
                    "total_posts": len(posts_data),
                    "analyzed_posts": len(analysis_results.get("analyzed_posts", [])),
                    "analysis_success_rate": len(analysis_results.get("analyzed_posts", [])) / max(1, len(posts_data))
                },
                "analysis_results": analysis_results,
                "raw_posts_sample": posts_data[:5]  # Save sample for reference
            }

            # Save to S3 with partitioned structure
            s3_key = build_key("reports", "content_analysis", year,
                               month, f"{self.batch_id}_content_analysis.json")
            result = s3_write_json(s3_key, report_data, compress=True)

            if result['success']:
                logger.info(
                    f"[SAVED] S3 analysis results saved: {result['s3_url']}")
            else:
                logger.error(
                    f"[ERROR] Failed to save S3 analysis results: {result.get('error')}")

        except Exception as e:
            logger.warning(f"Failed to save S3 analysis results: {e}")

    async def run_sentiment_analysis_only(self, posts_data: List[Dict]) -> Dict:
        """Run only sentiment analysis for quick insights"""
        try:
            logger.info(
                f"[SENTIMENT] Running sentiment analysis on {len(posts_data)} posts")

            # Use the content analyzer for sentiment analysis
            analysis_results = await self.content_analyzer.analyze_content_batch(posts_data)

            # Extract sentiment-specific insights
            sentiment_summary = {
                "total_posts": len(posts_data),
                "sentiment_distribution": analysis_results.get("aggregate_metrics", {}).get("sentiment_distribution", {}),
                "dominant_sentiment": analysis_results.get("aggregate_metrics", {}).get("dominant_sentiment", "unknown"),
                "top_emotions": analysis_results.get("aggregate_metrics", {}).get("top_emotions", []),
                "avg_emotional_impact": analysis_results.get("aggregate_metrics", {}).get("avg_emotional_impact", 0)
            }

            # Generate specialized sentiment report
            sentiment_report = await self.prompt_handler.generate_sentiment_analysis_prompt(posts_data)

            return {
                "status": "success",
                "sentiment_summary": sentiment_summary,
                "llm_sentiment_analysis": sentiment_report,
                "batch_id": self.batch_id
            }

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"status": "error", "error": str(e)}


# Task runner function for scheduler integration
async def run_content_analysis_task(worker):
    """Main content analysis task runner for scheduler"""
    task_id = f"content_analysis_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)

    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info(f"[START] CONTENT ANALYSIS TASK STARTED")
    logger.info(f"[TASK] Task ID: {task_id}")
    logger.info(f"[TIME] Start time: {start_time.isoformat()}")
    logger.info("=" * 60)

    try:
        task = ContentAnalysisTask()

        # Run content analysis workflow with real data
        result = await task.run_content_analysis_workflow(data_source="api", num_posts=20)

        execution_time = (datetime.now(timezone.utc) -
                          start_time).total_seconds()

        if result["status"] == "success":
            logger.info("[SUCCESS]" * 6)
            logger.info(f"[SUCCESS] CONTENT ANALYSIS COMPLETED")
            logger.info(f"[TIME] Total execution time: {execution_time:.2f}s")
            logger.info(
                f"[ANALYZED] Posts analyzed: {result.get('posts_analyzed', 0)}")
            logger.info(
                f"[DISCORD] Discord sent: {result.get('discord_sent', False)}")
            logger.info("[SUCCESS]" * 6)
        else:
            logger.error(
                f"[FAILED] Content analysis failed: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        execution_time = (datetime.now(timezone.utc) -
                          start_time).total_seconds()
        logger.error("[ERROR]" * 6)
        logger.error(f"[FAILED] CONTENT ANALYSIS TASK FAILED")
        logger.error(f"[TIME] Failed after: {execution_time:.2f}s")
        logger.error(f"[ERROR] Error: {str(e)}")
        logger.error("[ERROR]" * 6)

        return {"status": "error", "error": str(e), "task_id": task_id}

    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)
            logger.info(f"[REMOVED] Removed {task_id} from active tasks")


# Direct trigger functions for manual execution
async def trigger_content_analysis_latest():
    """Trigger content analysis for latest posts"""
    logger.info("🚀 TRIGGERING CONTENT ANALYSIS - LATEST POSTS")

    try:
        task = ContentAnalysisTask()
        result = await task.run_content_analysis_workflow(data_source="api", data_type="latest", num_posts=20)

        if result["status"] == "success":
            logger.info(
                f"✅ Latest posts analysis completed: {result.get('posts_analyzed', 0)} posts")
            return result
        else:
            logger.error(
                f"❌ Latest posts analysis failed: {result.get('error', 'Unknown error')}")
            return result

    except Exception as e:
        logger.error(f"❌ Latest posts analysis error: {str(e)}")
        return {"status": "error", "error": str(e)}


async def trigger_content_analysis_trending():
    """Trigger content analysis for trending posts"""
    logger.info("🔥 TRIGGERING CONTENT ANALYSIS - TRENDING POSTS")

    try:
        task = ContentAnalysisTask()
        # Use trending data type with higher post count for trending analysis
        result = await task.run_content_analysis_workflow(data_source="api", data_type="trending", num_posts=50)

        if result["status"] == "success":
            logger.info(
                f"✅ Trending posts analysis completed: {result.get('posts_analyzed', 0)} posts")
            return result
        else:
            logger.error(
                f"❌ Trending posts analysis failed: {result.get('error', 'Unknown error')}")
            return result

    except Exception as e:
        logger.error(f"❌ Trending posts analysis error: {str(e)}")
        return {"status": "error", "error": str(e)}
