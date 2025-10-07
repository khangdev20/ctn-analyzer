"""
Network Intelligence Task - Social Network Analysis Workflow
Integrates with the worker system to provide automated network relationship analysis
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from worker.features.network_intelligence import NetworkIntelligenceAgent
from worker.features.data_collector import collect_trending_data
from notifiers.discord_webhook_sender import DiscordWebhookSender

logger = logging.getLogger(__name__)


class NetworkIntelligenceTask:
    """
    Network Intelligence Task for Worker System

    Provides automated network relationship analysis:
    1. Collects social media data with author and hashtag information
    2. Analyzes hashtag co-occurrence clusters and relationships
    3. Detects author communities and identifies influencers
    4. Calculates cross-tag influence and connectivity patterns
    5. Sends Discord notifications with network insights
    """

    def __init__(self):
        self.agent = NetworkIntelligenceAgent()
        self.discord_sender = DiscordWebhookSender()

    async def run_network_analysis_workflow(self,
                                            batch_id: str = None,
                                            send_discord: bool = True,
                                            save_results: bool = True) -> Dict:
        """
        Run complete network intelligence workflow

        Args:
            batch_id: Optional batch identifier
            send_discord: Whether to send Discord notification
            save_results: Whether to save results to disk

        Returns:
            Dict with network analysis results and execution status
        """

        if not batch_id:
            batch_id = f"network_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')}"

        logger.info(
            f"🌐 Starting network intelligence workflow - Batch: {batch_id}")

        try:
            # Step 1: Collect current data snapshot
            logger.info("📊 Step 1: Collecting social media data...")
            current_data = await self._collect_network_data()

            if not current_data or not current_data.get("posts"):
                logger.warning("⚠️ No data available for network analysis")
                return self._generate_no_data_response(batch_id)

            posts = current_data["posts"]
            logger.info(f"📊 Collected {len(posts)} posts for network analysis")

            # Step 2: Run network intelligence analysis
            logger.info("🧠 Step 2: Running network intelligence analysis...")
            analysis_results = await self.agent.analyze_network_intelligence(posts, batch_id)

            if analysis_results.get("error"):
                logger.error(
                    f"❌ Network analysis failed: {analysis_results.get('error_message')}")
                return analysis_results

            # Step 3: Save results if requested
            if save_results:
                logger.info("💾 Step 3: Saving network analysis results...")
                await self._save_analysis_results(analysis_results, batch_id)

            # Step 4: Send Discord notification if requested
            if send_discord:
                logger.info("📢 Step 4: Sending Discord notification...")
                discord_success = await self._send_discord_notification(analysis_results)
                analysis_results["discord_sent"] = discord_success

            # Step 5: Generate execution summary
            execution_summary = self._generate_execution_summary(
                analysis_results)

            logger.info(
                f"✅ Network intelligence workflow completed successfully")
            logger.info(f"🌐 Summary: {execution_summary['summary_text']}")

            return {
                **analysis_results,
                "workflow_status": "success",
                "execution_summary": execution_summary
            }

        except Exception as e:
            logger.error(f"❌ Network intelligence workflow failed: {e}")
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

    async def _collect_network_data(self) -> Optional[Dict]:
        """Collect data with focus on network relationships (authors and hashtags)"""
        try:
            # Try to get recent processed data first
            recent_data = await self._load_most_recent_processed_data()
            if recent_data:
                return recent_data

            # Fallback: use mock data for testing
            from mock_data_provider import generate_mock_trending_data
            mock_data = generate_mock_trending_data(25)

            # Add collection timestamp and normalize data structure
            if mock_data:
                mock_data["collected_at"] = datetime.now(
                    timezone.utc).isoformat()

                # Normalize data structure - convert 'data' key to 'posts' key for compatibility
                if "data" in mock_data and "posts" not in mock_data:
                    mock_data["posts"] = mock_data["data"]

            return mock_data

        except Exception as e:
            logger.error(f"Failed to collect network data: {e}")
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
                            f"📊 Using recent processed data: {latest_file}")
                        return recent_data

            return None

        except Exception as e:
            logger.warning(f"Failed to load recent processed data: {e}")
            return None

    async def _save_analysis_results(self, results: Dict, batch_id: str) -> str:
        """Save network analysis results to structured directory"""
        try:
            now = datetime.now(timezone.utc)
            dir_path = f"data/reports/network/{now.year:04d}/{now.month:02d}/{now.day:02d}"
            os.makedirs(dir_path, exist_ok=True)

            filepath = f"{dir_path}/network_analysis_{batch_id}.json"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 Network results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save network results: {e}")
            raise

    async def _send_discord_notification(self, results: Dict) -> bool:
        """Send Discord notification with network analysis results"""
        try:
            discord_message = results.get("discord_message", "")
            if not discord_message:
                logger.warning("No Discord message to send")
                return False

            success = await self.discord_sender.send_message(discord_message)

            if success:
                logger.info("📢 Discord notification sent successfully")
            else:
                logger.warning("⚠️ Discord notification failed to send")

            return success

        except Exception as e:
            logger.error(f"Discord notification error: {e}")
            return False

    async def _send_error_notification(self, batch_id: str, error_message: str):
        """Send error notification to Discord"""
        try:
            error_msg = f"❌ **Network Intelligence Error**\n\n"
            error_msg += f"**Batch:** {batch_id}\n"
            error_msg += f"**Error:** {error_message[:500]}\n\n"
            error_msg += f"📅 *{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"

            await self.discord_sender.send_message(error_msg)

        except:
            pass  # Don't raise errors for error notifications

    def _generate_execution_summary(self, results: Dict) -> Dict:
        """Generate execution summary"""
        network_summary = results.get("network_summary", {})
        hashtag_clusters = results.get("hashtag_clusters", {})
        author_communities = results.get("author_communities", {})

        total_authors = network_summary.get("total_authors", 0)
        total_hashtags = network_summary.get("total_hashtags", 0)
        cluster_count = hashtag_clusters.get("cluster_count", 0)
        community_count = author_communities.get("community_count", 0)

        summary_text = f"Analyzed {total_authors} authors, {total_hashtags} hashtags, found {cluster_count} clusters, {community_count} communities"

        return {
            "total_authors": total_authors,
            "total_hashtags": total_hashtags,
            "hashtag_clusters": cluster_count,
            "author_communities": community_count,
            "discord_sent": results.get("discord_sent", False),
            "summary_text": summary_text
        }

    def _generate_no_data_response(self, batch_id: str) -> Dict:
        """Generate response when no data is available"""
        return {
            "batch_id": batch_id,
            "workflow_status": "no_data",
            "error": True,
            "error_message": "No data available for network analysis",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "discord_message": f"⚠️ **Network Analysis Skipped**\n\nReason: No data available\n\n📅 *{batch_id}*"
        }

    async def quick_network_check(self) -> str:
        """Quick network check for real-time monitoring"""
        try:
            logger.info("⚡ Running quick network check...")

            current_data = await self._collect_network_data()
            if not current_data:
                return "⚠️ **Quick Network Check Failed** - No data available"

            posts = current_data.get("posts", [])
            if not posts:
                return "🌐 **Quick Network Check** - No posts to analyze"

            # Quick network metrics
            authors = set()
            hashtags = set()

            for post in posts:
                author_data = post.get("author", {})
                username = author_data.get("username", "").strip()
                if username:
                    authors.add(username)

                post_tags = post.get("tags", [])
                if isinstance(post_tags, str):
                    post_tags = [post_tags]

                for tag in post_tags:
                    if isinstance(tag, str) and tag.strip():
                        clean_tag = tag.strip().lower()
                        if clean_tag.startswith('#'):
                            clean_tag = clean_tag[1:]
                        if len(clean_tag) > 1:
                            hashtags.add(clean_tag)

            # Find most active author
            author_post_counts = {}
            for post in posts:
                username = post.get("author", {}).get("username", "").strip()
                if username:
                    author_post_counts[username] = author_post_counts.get(
                        username, 0) + 1

            top_author = max(author_post_counts.items(
            ), key=lambda x: x[1]) if author_post_counts else ("unknown", 0)

            message = f"⚡ **Quick Network Check**\n"
            message += f"👥 **{len(authors)} authors** | 🏷️ **{len(hashtags)} hashtags**\n"
            message += f"📊 **{len(posts)} posts** analyzed\n"
            message += f"🏆 Most active: @{top_author[0]} ({top_author[1]} posts)"

            return message

        except Exception as e:
            logger.error(f"Quick network check failed: {e}")
            return f"❌ **Quick Network Check Error:** {str(e)[:100]}"


# Utility function for standalone task execution
async def run_network_intelligence_task(batch_id: str = None,
                                        send_discord: bool = True,
                                        save_results: bool = True) -> Dict:
    """
    Standalone function to run network intelligence task

    Args:
        batch_id: Optional batch identifier
        send_discord: Whether to send Discord notification
        save_results: Whether to save results to disk

    Returns:
        Dict with complete task execution results
    """
    task = NetworkIntelligenceTask()
    return await task.run_network_analysis_workflow(batch_id, send_discord, save_results)
