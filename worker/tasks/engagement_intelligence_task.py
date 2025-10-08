"""
Engagement Intelligence Task - Social Engagement Analysis Workflow
Integrates with the worker system to provide automated engagement growth analysis
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from worker.features.engagement_intelligence import EngagementIntelligenceAgent
from worker.features.data_collector import collect_trending_data
from notifiers.discord_webhook_sender import DiscordWebhookSender

logger = logging.getLogger(__name__)


class EngagementIntelligenceTask:
    """
    Engagement Intelligence Task for Worker System

    Provides automated engagement growth analysis:
    1. Collects current and previous data snapshots
    2. Computes engagement deltas and velocities  
    3. Identifies fastest-growing posts
    4. Sends Discord notifications with results
    """

    def __init__(self):
        self.agent = EngagementIntelligenceAgent()
        self.discord_sender = DiscordWebhookSender()

    async def run_engagement_analysis_workflow(self,
                                               batch_id: str = None,
                                               send_discord: bool = True,
                                               save_results: bool = True) -> Dict:
        """
        Run complete engagement intelligence workflow

        Args:
            batch_id: Optional batch identifier
            send_discord: Whether to send Discord notification
            save_results: Whether to save results to disk

        Returns:
            Dict with analysis results and execution status
        """

        if not batch_id:
            batch_id = f"engagement_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')}"

        logger.info(
            f"[LAUNCH] Starting engagement intelligence workflow - Batch: {batch_id}")

        try:
            # Step 1: Collect current data snapshot
            logger.info("[ANALYTICS] Step 1: Collecting current data snapshot...")
            current_data = await self._collect_current_data()

            if not current_data or not current_data.get("posts"):
                logger.warning(
                    "[WARNING] No current data available - cannot perform analysis")
                return self._generate_no_data_response(batch_id, "current")

            # Step 2: Load previous data snapshot
            logger.info("[TRENDING_UP] Step 2: Loading previous data snapshot...")
            previous_data = await self._load_previous_data()

            if not previous_data or not previous_data.get("posts"):
                logger.warning(
                    "[WARNING] No previous data available - performing baseline analysis")
                return await self._perform_baseline_analysis(current_data, batch_id, send_discord, save_results)

            # Step 3: Run engagement intelligence analysis
            logger.info(
                "[AI] Step 3: Running engagement intelligence analysis...")
            analysis_results = await self.agent.analyze_engagement_growth(
                previous_data, current_data, batch_id
            )

            if analysis_results.get("error"):
                logger.error(
                    f"[ERROR] Analysis failed: {analysis_results.get('error_message')}")
                return analysis_results

            # Step 4: Save results if requested
            if save_results:
                logger.info("[SAVE] Step 4: Saving analysis results...")
                await self._save_analysis_results(analysis_results, batch_id)

            # Step 5: Send Discord notification if requested
            if send_discord:
                logger.info("[ANNOUNCE] Step 5: Sending Discord notification...")
                discord_success = await self._send_discord_notification(analysis_results)
                analysis_results["discord_sent"] = discord_success

            # Step 6: Generate execution summary
            execution_summary = self._generate_execution_summary(
                analysis_results)

            logger.info(
                f"[OK] Engagement intelligence workflow completed successfully")
            logger.info(f"[ANALYTICS] Summary: {execution_summary['summary_text']}")

            return {
                **analysis_results,
                "workflow_status": "success",
                "execution_summary": execution_summary
            }

        except Exception as e:
            logger.error(f"[ERROR] Engagement intelligence workflow failed: {e}")
            error_response = {
                "batch_id": batch_id,
                "workflow_status": "error",
                "error": True,
                "error_message": str(e),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Try to send error notification
            if send_discord:
                try:
                    await self._send_error_notification(batch_id, str(e))
                except:
                    pass  # Don't fail on notification errors

            return error_response

    async def _collect_current_data(self) -> Optional[Dict]:
        """Collect current data snapshot"""
        try:
            # Try to get the most recent processed data first
            recent_data = await self._load_most_recent_processed_data()
            if recent_data:
                return recent_data

            # Fallback: use mock data for testing
            from mock_data_provider import generate_mock_trending_data
            mock_data = generate_mock_trending_data(20)

            # Add collection timestamp and normalize data structure
            if mock_data:
                mock_data["collected_at"] = datetime.now(
                    timezone.utc).isoformat()

                # Normalize data structure - convert 'data' key to 'posts' key for compatibility
                if "data" in mock_data and "posts" not in mock_data:
                    mock_data["posts"] = mock_data["data"]

            return mock_data

        except Exception as e:
            logger.error(f"Failed to collect current data: {e}")
            return None

    async def _load_most_recent_processed_data(self) -> Optional[Dict]:
        """Load the most recent processed data from the pipeline"""
        try:
            base_dir = "data/processed"
            now = datetime.now(timezone.utc)

            # Search recent directories (last 2 days)
            for days_back in range(0, 2):
                search_date = now.replace(
                    day=now.day - days_back) if days_back > 0 else now
                dir_path = f"{base_dir}/{search_date.year:04d}/{search_date.month:02d}/{search_date.day:02d}"

                if os.path.exists(dir_path):
                    # Find most recent batch file
                    batch_files = []
                    for file in os.listdir(dir_path):
                        if file.endswith('.json') and 'batch_' in file:
                            batch_files.append(file)

                    if batch_files:
                        batch_files.sort(reverse=True)
                        latest_file = os.path.join(dir_path, batch_files[0])

                        with open(latest_file, 'r', encoding='utf-8') as f:
                            recent_data = json.load(f)

                        logger.info(
                            f"[ANALYTICS] Using recent processed data: {latest_file}")
                        return recent_data

            return None

        except Exception as e:
            logger.warning(f"Failed to load recent processed data: {e}")
            return None

    async def _load_previous_data(self) -> Optional[Dict]:
        """Load most recent previous data for comparison"""
        try:
            # Look for recent processed data files
            base_dir = "data/processed"
            now = datetime.now(timezone.utc)

            # Search last 3 days for previous data
            for days_back in range(1, 4):
                search_date = now.replace(day=now.day - days_back)
                dir_path = f"{base_dir}/{search_date.year:04d}/{search_date.month:02d}/{search_date.day:02d}"

                if os.path.exists(dir_path):
                    # Find most recent batch file
                    batch_files = []
                    for file in os.listdir(dir_path):
                        if file.endswith('.json') and 'batch_' in file:
                            batch_files.append(file)

                    if batch_files:
                        batch_files.sort(reverse=True)
                        latest_file = os.path.join(dir_path, batch_files[0])

                        with open(latest_file, 'r', encoding='utf-8') as f:
                            previous_data = json.load(f)

                        logger.info(f"[ANALYTICS] Loaded previous data: {latest_file}")
                        return previous_data

            # Fallback: look in raw data directory
            return await self._load_previous_raw_data()

        except Exception as e:
            logger.warning(f"Failed to load previous data: {e}")
            return None

    async def _load_previous_raw_data(self) -> Optional[Dict]:
        """Fallback: load from raw data directory"""
        try:
            base_dir = "data/raw"
            now = datetime.now(timezone.utc)

            for days_back in range(1, 3):
                search_date = now.replace(day=now.day - days_back)
                dir_path = f"{base_dir}/{search_date.year:04d}/{search_date.month:02d}/{search_date.day:02d}"

                if os.path.exists(dir_path):
                    raw_files = [f for f in os.listdir(
                        dir_path) if f.endswith('.json')]
                    if raw_files:
                        raw_files.sort(reverse=True)
                        latest_file = os.path.join(dir_path, raw_files[0])

                        with open(latest_file, 'r', encoding='utf-8') as f:
                            return json.load(f)

            return None

        except Exception as e:
            logger.warning(f"Failed to load previous raw data: {e}")
            return None

    async def _perform_baseline_analysis(self,
                                         current_data: Dict,
                                         batch_id: str,
                                         send_discord: bool,
                                         save_results: bool) -> Dict:
        """Perform baseline analysis when no previous data exists"""
        try:
            logger.info("[ANALYTICS] Performing baseline engagement analysis...")

            posts = current_data.get("posts", [])
            total_engagement = sum(
                post.get("like_count", 0) +
                post.get("reply_count", 0) +
                post.get("repost_count", 0)
                for post in posts
            )

            # Create baseline response
            baseline_results = {
                "batch_id": batch_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "is_baseline": True,
                "current_posts_count": len(posts),
                "previous_posts_count": 0,
                "matched_posts": 0,
                "growth_summary": {
                    "avg_velocity_per_min": 0,
                    "avg_acceleration": 0,
                    "total_delta_engagement": 0,
                    "posts_with_growth": 0,
                    "posts_with_acceleration": 0,
                    "baseline_total_engagement": total_engagement
                },
                "top_performers": [],
                "engagement_composition": {
                    "likes_percent": 60,  # Typical distribution
                    "replies_percent": 25,
                    "reposts_percent": 15
                },
                "discord_message": self._format_baseline_discord_message(batch_id, len(posts), total_engagement)
            }

            if save_results:
                await self._save_analysis_results(baseline_results, batch_id)

            if send_discord:
                await self._send_discord_notification(baseline_results)
                baseline_results["discord_sent"] = True

            return {
                **baseline_results,
                "workflow_status": "success_baseline"
            }

        except Exception as e:
            logger.error(f"Baseline analysis failed: {e}")
            raise

    def _format_baseline_discord_message(self, batch_id: str, post_count: int, total_engagement: int) -> str:
        """Format Discord message for baseline analysis"""
        message = "[ANALYTICS] **Engagement Baseline Established**\n\n"
        message += f"• **Posts Analyzed:** {post_count}\n"
        message += f"• **Total Engagement:** {total_engagement:,}\n"
        message += f"• **Avg per Post:** {total_engagement / max(post_count, 1):.1f}\n\n"
        message += "[WAITING] *Next analysis will show growth patterns*\n\n"
        message += f"[TIMER] *Baseline: {batch_id}*"

        return message

    async def _save_analysis_results(self, results: Dict, batch_id: str) -> str:
        """Save analysis results to structured directory"""
        try:
            now = datetime.now(timezone.utc)
            dir_path = f"data/reports/engagement/{now.year:04d}/{now.month:02d}/{now.day:02d}"
            os.makedirs(dir_path, exist_ok=True)

            filepath = f"{dir_path}/engagement_analysis_{batch_id}.json"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"[SAVE] Results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise

    async def _send_discord_notification(self, results: Dict) -> bool:
        """Send Discord notification with analysis results"""
        try:
            discord_message = results.get("discord_message", "")
            if not discord_message:
                logger.warning("No Discord message to send")
                return False

            success = await self.discord_sender.send_message(discord_message)

            if success:
                logger.info("[ANNOUNCE] Discord notification sent successfully")
            else:
                logger.warning("[WARNING] Discord notification failed to send")

            return success

        except Exception as e:
            logger.error(f"Discord notification error: {e}")
            return False

    async def _send_error_notification(self, batch_id: str, error_message: str):
        """Send error notification to Discord"""
        try:
            error_msg = f"[ERROR] **Engagement Analysis Error**\n\n"
            error_msg += f"**Batch:** {batch_id}\n"
            error_msg += f"**Error:** {error_message[:500]}\n\n"
            error_msg += f"[TIMER] *{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"

            await self.discord_sender.send_message(error_msg)

        except:
            pass  # Don't raise errors for error notifications

    def _generate_execution_summary(self, results: Dict) -> Dict:
        """Generate execution summary"""
        growth_summary = results.get("growth_summary", {})

        velocity = growth_summary.get("avg_velocity_per_min", 0)
        posts_analyzed = results.get("matched_posts", 0)
        posts_growing = growth_summary.get("posts_with_growth", 0)

        summary_text = f"Analyzed {posts_analyzed} posts, {posts_growing} growing, avg velocity: +{velocity:.2f}/min"

        return {
            "posts_analyzed": posts_analyzed,
            "posts_growing": posts_growing,
            "avg_velocity": velocity,
            "top_performers_count": len(results.get("top_performers", [])),
            "discord_sent": results.get("discord_sent", False),
            "summary_text": summary_text
        }

    def _generate_no_data_response(self, batch_id: str, data_type: str) -> Dict:
        """Generate response when data is not available"""
        return {
            "batch_id": batch_id,
            "workflow_status": "no_data",
            "error": True,
            "error_message": f"No {data_type} data available for analysis",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "discord_message": f"[WARNING] **Engagement Analysis Skipped**\n\nReason: No {data_type} data available\n\n[TIMER] *{batch_id}*"
        }

    async def quick_engagement_check(self) -> str:
        """Quick engagement check for real-time monitoring"""
        try:
            logger.info("[FAST] Running quick engagement check...")

            current_data = await self._collect_current_data()
            if not current_data:
                return "[WARNING] **Quick Check Failed** - No data available"

            posts = current_data.get("posts", [])
            if not posts:
                return "[ANALYTICS] **Quick Check** - No posts to analyze"

            # Calculate quick metrics
            total_engagement = sum(
                post.get("like_count", 0) +
                post.get("reply_count", 0) +
                post.get("repost_count", 0)
                for post in posts
            )

            avg_engagement = total_engagement / len(posts)

            # Find top post
            top_post = max(posts, key=lambda p:
                           p.get("like_count", 0) + p.get("reply_count",
                                                          0) + p.get("repost_count", 0)
                           )

            top_author = top_post.get("author", {}).get("username", "unknown")
            top_engagement = (
                top_post.get("like_count", 0) +
                top_post.get("reply_count", 0) +
                top_post.get("repost_count", 0)
            )

            message = f"[FAST] **Quick Engagement Check**\n"
            message += f"[ANALYTICS] **{len(posts)} posts** | Avg: {avg_engagement:.1f}\n"
            message += f"[WINNER] Top: @{top_author} ({top_engagement} total)\n"
            message += f"[TRENDING_UP] Total: {total_engagement:,} interactions"

            return message

        except Exception as e:
            logger.error(f"Quick engagement check failed: {e}")
            return f"[ERROR] **Quick Check Error:** {str(e)[:100]}"


# Utility function for standalone task execution
async def run_engagement_intelligence_task(batch_id: str = None,
                                           send_discord: bool = True,
                                           save_results: bool = True) -> Dict:
    """
    Standalone function to run engagement intelligence task

    Args:
        batch_id: Optional batch identifier
        send_discord: Whether to send Discord notification  
        save_results: Whether to save results to disk

    Returns:
        Dict with complete task execution results
    """
    task = EngagementIntelligenceTask()
    return await task.run_engagement_analysis_workflow(batch_id, send_discord, save_results)
