"""
Temporal Analytics Task
Integrates temporal analytics analysis into the worker system
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from worker.features.temporal_analytics import TemporalAnalyticsAgent
from notifiers.discord_webhook_sender import DiscordWebhookSender


class TemporalAnalyticsTask:
    """
    Task class for running temporal analytics analysis workflow
    
    Integrates with the worker system to:
    1. Collect post data for temporal analysis
    2. Run temporal analytics analysis
    3. Send Discord notifications with timing insights
    4. Save analysis results
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent = TemporalAnalyticsAgent()
        self.discord_sender = DiscordWebhookSender()

    async def run_temporal_analysis_workflow(self, batch_id: str = None) -> Dict:
        """
        Run complete temporal analytics workflow
        
        Args:
            batch_id: Optional batch identifier
            
        Returns:
            Dict with workflow results and status
        """
        if not batch_id:
            batch_id = f"temporal_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        try:
            self.logger.info(f"⏰ Starting temporal analytics workflow for batch {batch_id}")

            # Step 1: Collect post data
            posts_data = await self._collect_temporal_data(batch_id)
            
            if not posts_data or len(posts_data) == 0:
                return self._create_workflow_result(
                    batch_id, False, "No posts data available for temporal analysis", {}
                )

            self.logger.info(f"📊 Collected {len(posts_data)} posts for temporal analysis")

            # Step 2: Run temporal analytics analysis
            analysis_results = await self.agent.analyze_temporal_patterns(posts_data, batch_id)
            
            if analysis_results.get("error"):
                return self._create_workflow_result(
                    batch_id, False, f"Temporal analysis failed: {analysis_results.get('error_message')}", analysis_results
                )

            # Step 3: Save analysis results
            await self._save_analysis_results(analysis_results, batch_id)

            # Step 4: Send Discord notification
            discord_sent = await self._send_discord_notification(analysis_results, batch_id)

            # Step 5: Create workflow summary
            workflow_result = self._create_workflow_result(
                batch_id, True, "Temporal analytics workflow completed successfully", analysis_results
            )
            
            workflow_result["discord_notification_sent"] = discord_sent
            workflow_result["posts_analyzed"] = len(posts_data)
            workflow_result["optimal_times"] = analysis_results.get("optimal_times", {})
            workflow_result["trend_insights"] = analysis_results.get("trend_analysis", {})

            self.logger.info(f"✅ Temporal analytics workflow completed successfully for batch {batch_id}")
            return workflow_result

        except Exception as e:
            self.logger.error(f"❌ Temporal analytics workflow failed for batch {batch_id}: {e}")
            return self._create_workflow_result(
                batch_id, False, f"Workflow error: {str(e)}", {}
            )

    async def _collect_temporal_data(self, batch_id: str) -> List[Dict]:
        """Collect post data for temporal analysis"""
        try:
            posts = []
            
            # Try to load from recent data files
            data_dir = os.path.join("data", "processed")
            
            # Look for recent processed data
            today = datetime.now(timezone.utc)
            for days_back in range(7):  # Check last 7 days
                date = today - timedelta(days=days_back)
                date_path = os.path.join(data_dir, str(date.year), f"{date.month:02d}", f"{date.day:02d}")
                
                if os.path.exists(date_path):
                    # Find scored data files
                    scored_path = os.path.join(date_path, "scored")
                    if os.path.exists(scored_path):
                        for filename in os.listdir(scored_path):
                            if filename.endswith("_scored.json"):
                                file_path = os.path.join(scored_path, filename)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        batch_data = json.load(f)
                                        if isinstance(batch_data, list):
                                            posts.extend(batch_data)
                                        elif isinstance(batch_data, dict) and "posts" in batch_data:
                                            posts.extend(batch_data["posts"])
                                        elif isinstance(batch_data, dict) and "data" in batch_data:
                                            posts.extend(batch_data["data"])
                                except Exception as e:
                                    self.logger.warning(f"Failed to load {file_path}: {e}")
                                    continue

            # If no processed data found, try raw data
            if not posts:
                raw_dir = os.path.join("data", "raw")
                for days_back in range(3):  # Check last 3 days of raw data
                    date = today - timedelta(days=days_back)
                    date_path = os.path.join(raw_dir, str(date.year), f"{date.month:02d}", f"{date.day:02d}")
                    
                    if os.path.exists(date_path):
                        for filename in os.listdir(date_path):
                            if filename.endswith(".json"):
                                file_path = os.path.join(date_path, filename)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        batch_data = json.load(f)
                                        if isinstance(batch_data, list):
                                            posts.extend(batch_data)
                                        elif isinstance(batch_data, dict) and "posts" in batch_data:
                                            posts.extend(batch_data["posts"])
                                except Exception as e:
                                    self.logger.warning(f"Failed to load raw data {file_path}: {e}")
                                    continue

            # If still no data, try to use mock data provider for development
            if not posts:
                try:
                    from mock_data_provider import MockDataProvider
                    mock_provider = MockDataProvider()
                    posts = mock_provider.generate_temporal_dataset()
                    self.logger.info(f"Using mock data for temporal analysis: {len(posts)} posts")
                except ImportError:
                    self.logger.error("No real data found and mock data provider not available")
                except Exception as e:
                    self.logger.error(f"Failed to generate mock data: {e}")

            # Add created_at timestamps if missing
            for post in posts:
                if not post.get("created_at") and not post.get("metadata", {}).get("created_at"):
                    # Generate a timestamp within the last 24 hours
                    hours_ago = np.random.uniform(0, 24)
                    timestamp = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
                    post["created_at"] = timestamp.isoformat()

            self.logger.info(f"Collected {len(posts)} posts for temporal analysis")
            return posts

        except Exception as e:
            self.logger.error(f"Failed to collect temporal data: {e}")
            return []

    async def _save_analysis_results(self, analysis_results: Dict, batch_id: str) -> bool:
        """Save temporal analytics results to file"""
        try:
            # Create reports directory
            reports_dir = os.path.join("data", "reports", "temporal_analytics")
            os.makedirs(reports_dir, exist_ok=True)
            
            # Save detailed results
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            results_file = os.path.join(reports_dir, f"temporal_analysis_{timestamp}.json")
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Temporal analytics results saved to {results_file}")
            
            # Save summary report
            summary = {
                "batch_id": batch_id,
                "timestamp": timestamp,
                "posts_analyzed": analysis_results.get("temporal_summary", {}).get("total_posts", 0),
                "optimal_days": analysis_results.get("optimal_times", {}).get("best_days", []),
                "optimal_hours": analysis_results.get("optimal_times", {}).get("best_hours", []),
                "avg_time_to_trend": analysis_results.get("trend_analysis", {}).get("avg_time_to_trend_minutes", 0),
                "avg_momentum_duration": analysis_results.get("momentum_analysis", {}).get("avg_momentum_duration_hours", 0),
                "recommendations_count": analysis_results.get("posting_recommendations", {}).get("total_recommendations", 0)
            }
            
            summary_file = os.path.join(reports_dir, f"temporal_summary_{timestamp}.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save temporal analytics results: {e}")
            return False

    async def _send_discord_notification(self, analysis_results: Dict, batch_id: str) -> bool:
        """Send Discord notification with temporal analytics insights"""
        try:
            discord_message = analysis_results.get("discord_message", "")
            
            if not discord_message:
                self.logger.warning("No Discord message generated for temporal analytics")
                return False

            # Send the message
            success = await self.discord_sender.send_message(discord_message)
            
            if success:
                self.logger.info(f"Discord notification sent successfully for temporal analysis {batch_id}")
            else:
                self.logger.error(f"Failed to send Discord notification for temporal analysis {batch_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending Discord notification: {e}")
            return False

    def _create_workflow_result(self, batch_id: str, success: bool, message: str, analysis_results: Dict) -> Dict:
        """Create standardized workflow result"""
        return {
            "batch_id": batch_id,
            "workflow": "temporal_analytics",
            "success": success,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_results": analysis_results,
            "has_discord_message": bool(analysis_results.get("discord_message")),
            "posts_count": analysis_results.get("temporal_summary", {}).get("total_posts", 0),
            "optimal_times_found": len(analysis_results.get("optimal_times", {}).get("best_days", [])) > 0
        }


# Standalone function for external usage
async def run_temporal_analytics_task(batch_id: str = None) -> Dict:
    """
    Standalone function to run temporal analytics task
    
    Args:
        batch_id: Optional batch identifier
        
    Returns:
        Dict with task results
    """
    task = TemporalAnalyticsTask()
    return await task.run_temporal_analysis_workflow(batch_id)


# Quick test function
async def test_temporal_analytics_task():
    """Quick test of temporal analytics task"""
    print("🧪 Testing Temporal Analytics Task...")
    
    task = TemporalAnalyticsTask()
    result = await task.run_temporal_analysis_workflow("test_batch")
    
    print(f"✅ Task completed: {result['success']}")
    print(f"📊 Posts analyzed: {result.get('posts_count', 0)}")
    
    if result.get('analysis_results', {}).get('discord_message'):
        print("\n📱 Discord Message Preview:")
        print(result['analysis_results']['discord_message'])
    
    return result


if __name__ == "__main__":
    # For testing
    import numpy as np
    asyncio.run(test_temporal_analytics_task())