"""
Trending Prediction Task - Workflow Integration

This module integrates the Trending Prediction system into the main worker architecture,
providing automated trending analysis with data collection, processing, and Discord notifications.

Features:
- Automated data collection from multiple analysis engines
- Comprehensive trending probability scoring
- Trending candidate identification and ranking
- Discord notifications with rich embed formatting
- Structured data persistence and reporting

Author: AI Assistant
Date: October 7, 2025
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

# Import trending prediction engine
from worker.features.trending_prediction import TrendingPredictionAgent, analyze_trending_potential

# Import notification system
try:
    from notifiers.discord_webhook_sender import DiscordWebhookSender
except ImportError:
    DiscordWebhookSender = None
    logging.warning("Discord webhook sender not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendingPredictionTask:
    """
    Trending prediction task workflow that integrates with the main worker system.

    This class orchestrates the complete trending prediction workflow including:
    - Data collection from various analysis engines
    - Trending probability calculation and scoring
    - Candidate identification and ranking
    - Discord notification with rich formatting
    - Results persistence and reporting
    """

    def __init__(self):
        """Initialize the trending prediction task."""
        self.agent = TrendingPredictionAgent()
        self.discord_sender = DiscordWebhookSender() if DiscordWebhookSender else None

        # Configuration
        self.data_sources = [
            'content_analysis',
            'engagement_intelligence',
            'network_intelligence',
            'temporal_analytics',
            'strategic_intelligence'
        ]

        # Data paths
        self.base_data_path = Path("data")
        self.reports_path = self.base_data_path / "reports" / "trending_prediction"
        self.reports_path.mkdir(parents=True, exist_ok=True)

    async def run_trending_prediction_workflow(self, batch_id: str = None, send_discord: bool = True) -> Dict:
        """
        Execute complete trending prediction workflow.

        Args:
            batch_id: Optional batch identifier for tracking
            send_discord: Whether to send Discord notifications (default True)

        Returns:
            Dictionary containing workflow results and analysis
        """
        if not batch_id:
            batch_id = f"trending_prediction_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"[HOT] Starting trending prediction workflow for batch {batch_id}")

        try:
            # Step 1: Collect comprehensive post data
            posts_data = await self._collect_trending_data(batch_id)

            if not posts_data:
                logger.warning("No posts data collected for trending analysis")
                return {'status': 'no_data', 'batch_id': batch_id}

            logger.info(
                f"[ANALYTICS] Collected {len(posts_data)} posts for trending analysis")

            # Step 2: Run trending prediction analysis
            analysis_results = await self.agent.analyze_trending_potential(posts_data, batch_id)

            # Step 3: Save analysis results
            await self._save_analysis_results(analysis_results, batch_id)

            # Step 4: Send Discord notification
            discord_success = await self._send_discord_notification(analysis_results)

            # Step 5: Generate workflow summary
            workflow_results = {
                'status': 'success',
                'batch_id': batch_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'posts_processed': len(posts_data),
                'trending_candidates': len(analysis_results.get('trending_candidates', [])),
                'average_score': analysis_results.get('average_final_score', 0),
                'discord_notification': discord_success,
                'analysis_results': analysis_results,
                'workflow_insights': await self._generate_workflow_insights(analysis_results)
            }

            logger.info(
                f"[OK] Trending prediction workflow completed successfully for batch {batch_id}")
            return workflow_results

        except Exception as e:
            logger.error(f"[ERROR] Error in trending prediction workflow: {str(e)}")
            return {
                'status': 'error',
                'batch_id': batch_id,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _collect_trending_data(self, batch_id: str) -> List[Dict]:
        """
        Collect comprehensive post data from all available analysis engines.

        This method aggregates data from multiple sources to provide complete
        metrics for trending prediction analysis.
        """
        collected_posts = []

        try:
            # Method 1: Try to collect from recent analysis results
            recent_data = await self._collect_from_recent_analyses()
            if recent_data:
                collected_posts.extend(recent_data)
                logger.info(
                    f"📥 Collected {len(recent_data)} posts from recent analyses")

            # Method 2: Try to collect from raw data if available
            raw_data = await self._collect_from_raw_data()
            if raw_data:
                collected_posts.extend(raw_data)
                logger.info(
                    f"📥 Collected {len(raw_data)} additional posts from raw data")

            # Method 3: Try trending data files from root directory
            trending_files_data = await self._collect_from_trending_files()
            if trending_files_data:
                collected_posts.extend(trending_files_data)
                logger.info(
                    f"📥 Collected {len(trending_files_data)} posts from trending data files")

            # Method 4: Generate mock data if insufficient real data
            if len(collected_posts) < 5:
                mock_data = await self._generate_mock_trending_data()
                collected_posts.extend(mock_data)
                logger.info(
                    f"� Generated {len(mock_data)} mock posts for trending analysis")

            # Remove duplicates based on post ID
            unique_posts = []
            seen_ids = set()

            for post in collected_posts:
                post_id = post.get('id', post.get(
                    'post_id', f"post_{len(unique_posts)}"))
                if post_id not in seen_ids:
                    post['id'] = post_id  # Ensure consistent ID field
                    unique_posts.append(post)
                    seen_ids.add(post_id)

            logger.info(
                f"[ANALYTICS] Final dataset: {len(unique_posts)} unique posts for trending analysis")
            return unique_posts[:50]  # Limit to 50 posts for performance

        except Exception as e:
            logger.error(f"[ERROR] Error collecting trending data: {str(e)}")
            return await self._generate_mock_trending_data()

    async def _collect_from_recent_analyses(self) -> List[Dict]:
        """Collect posts from recent analysis results."""
        posts = []

        try:
            # Look for recent analysis results in reports directory
            reports_base = Path("data/reports")
            if reports_base.exists():
                for engine_dir in self.data_sources:
                    engine_path = reports_base / engine_dir
                    if engine_path.exists():
                        # Find most recent analysis file
                        analysis_files = list(engine_path.glob("*.json"))
                        if analysis_files:
                            latest_file = max(
                                analysis_files, key=lambda f: f.stat().st_mtime)
                            try:
                                with open(latest_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)

                                # Extract posts from different analysis formats
                                engine_posts = self._extract_posts_from_analysis(
                                    data, engine_dir)
                                posts.extend(engine_posts)

                            except Exception as e:
                                logger.warning(
                                    f"Could not read {latest_file}: {str(e)}")

            return posts

        except Exception as e:
            logger.warning(f"Error collecting from recent analyses: {str(e)}")
            return []

    def _extract_posts_from_analysis(self, analysis_data: Dict, engine_type: str) -> List[Dict]:
        """Extract and normalize posts from different analysis engine formats."""
        posts = []

        try:
            # Different engines store posts in different formats
            if engine_type == 'content_analysis':
                # Try different possible structures
                post_sources = [
                    analysis_data.get('analyzed_posts', []),
                    analysis_data.get('posts', []),
                    analysis_data.get('content_analysis', {}).get('posts', [])
                ]
                
                for source in post_sources:
                    if source:
                        for post in source:
                            normalized_post = {
                                'id': post.get('id', post.get('post_id', f"content_{len(posts)}")),
                                'content': post.get('content', post.get('text', '')),
                                'author': post.get('author', 'unknown'),
                                'story_score': post.get('story_score', post.get('content_score', 60)),
                                'engagement_score': post.get('engagement_score', 55),
                                'velocity': post.get('velocity', 1.2),
                                'network_influence': post.get('network_influence', 0.5),
                                'timing_score': post.get('timing_score', post.get('temporal_score', 55)),
                                'strategic_score': post.get('strategic_score', 50),
                                'source_engine': engine_type
                            }
                            posts.append(normalized_post)
                        break  # Use first non-empty source

            elif engine_type == 'engagement_intelligence':
                # Try different possible structures
                engagement_sources = [
                    analysis_data.get('engagement_analysis', {}),
                    analysis_data.get('analysis', {}),
                    analysis_data
                ]
                
                for source in engagement_sources:
                    if 'post_scores' in source:
                        for post_id, score_data in source['post_scores'].items():
                            normalized_post = {
                                'id': post_id,
                                'content': score_data.get('content', f'Engagement post {post_id}'),
                                'author': score_data.get('author', 'unknown'),
                                'story_score': 60,
                                'engagement_score': score_data.get('engagement_score', score_data.get('viral_score', 60)),
                                'velocity': score_data.get('velocity', 1.5),
                                'network_influence': 0.6,
                                'timing_score': 55,
                                'strategic_score': 50,
                                'source_engine': engine_type
                            }
                            posts.append(normalized_post)
                        break

            elif engine_type == 'temporal_analytics':
                # Try temporal analytics structure
                temporal_sources = [
                    analysis_data.get('temporal_data', []),
                    analysis_data.get('posts', []),
                    analysis_data.get('analysis', {}).get('posts', [])
                ]
                
                for source in temporal_sources:
                    if source:
                        for post in source:
                            normalized_post = {
                                'id': post.get('id', post.get('post_id', f"temporal_{len(posts)}")),
                                'content': post.get('content', post.get('text', f'Temporal post {len(posts)}')),
                                'author': post.get('author', 'unknown'),
                                'story_score': 55,
                                'engagement_score': post.get('engagement_score', 50),
                                'velocity': post.get('velocity', 1.3),
                                'network_influence': 0.5,
                                'timing_score': post.get('timing_score', post.get('temporal_score', 70)),
                                'strategic_score': 45,
                                'source_engine': engine_type
                            }
                            posts.append(normalized_post)
                        break

            elif engine_type == 'strategic_intelligence':
                # Try strategic intelligence structure
                strategic_sources = [
                    analysis_data.get('strategic_data', []),
                    analysis_data.get('posts', []),
                    analysis_data.get('analysis', {}).get('posts', [])
                ]
                
                for source in strategic_sources:
                    if source:
                        for post in source:
                            normalized_post = {
                                'id': post.get('id', post.get('post_id', f"strategic_{len(posts)}")),
                                'content': post.get('content', post.get('text', f'Strategic post {len(posts)}')),
                                'author': post.get('author', 'unknown'),
                                'story_score': 50,
                                'engagement_score': 55,
                                'velocity': 1.1,
                                'network_influence': 0.6,
                                'timing_score': 50,
                                'strategic_score': post.get('strategic_score', post.get('business_value', 65)),
                                'source_engine': engine_type
                            }
                            posts.append(normalized_post)
                        break

            # Generic fallback for any engine type
            if not posts:
                generic_sources = [
                    analysis_data.get('posts', []),
                    analysis_data.get('data', []),
                    analysis_data.get('items', [])
                ]
                
                for source in generic_sources:
                    if isinstance(source, list) and source:
                        for item in source:
                            if isinstance(item, dict):
                                normalized_post = {
                                    'id': item.get('id', f"{engine_type}_{len(posts)}"),
                                    'content': item.get('content', item.get('text', f'{engine_type} post')),
                                    'author': item.get('author', 'unknown'),
                                    'story_score': 55,
                                    'engagement_score': 55,
                                    'velocity': 1.2,
                                    'network_influence': 0.5,
                                    'timing_score': 55,
                                    'strategic_score': 55,
                                    'source_engine': engine_type
                                }
                                posts.append(normalized_post)
                        break

        except Exception as e:
            logger.warning(
                f"Error extracting posts from {engine_type}: {str(e)}")

        return posts

    async def _collect_from_raw_data(self) -> List[Dict]:
        """Collect posts from raw data sources."""
        posts = []

        try:
            # Look for recent raw data
            raw_data_path = Path("data/raw")
            if raw_data_path.exists():
                # Find most recent data directory
                date_dirs = [d for d in raw_data_path.iterdir() if d.is_dir()]
                if date_dirs:
                    latest_date_dir = max(date_dirs, key=lambda d: d.name)

                    # Look for JSON files in the latest date directory
                    json_files = list(latest_date_dir.rglob("*.json"))
                    if json_files:
                        latest_file = max(
                            json_files, key=lambda f: f.stat().st_mtime)

                        try:
                            with open(latest_file, 'r', encoding='utf-8') as f:
                                raw_data = json.load(f)

                            # Extract posts from raw data format
                            if isinstance(raw_data, list):
                                for item in raw_data:
                                    if isinstance(item, dict):
                                        normalized_post = self._normalize_raw_post(
                                            item)
                                        posts.append(normalized_post)
                            elif isinstance(raw_data, dict) and 'posts' in raw_data:
                                for post in raw_data['posts']:
                                    normalized_post = self._normalize_raw_post(
                                        post)
                                    posts.append(normalized_post)

                        except Exception as e:
                            logger.warning(
                                f"Could not read raw data file {latest_file}: {str(e)}")

            return posts

        except Exception as e:
            logger.warning(f"Error collecting from raw data: {str(e)}")
            return []

    async def _collect_from_trending_files(self) -> List[Dict]:
        """Collect posts from trending data files in root directory."""
        posts = []

        try:
            # Look for trending_data_*.json files in root directory
            root_path = Path(".")
            trending_files = list(root_path.glob("trending_data_*.json"))
            
            if trending_files:
                # Use the most recent trending data file
                latest_trending_file = max(trending_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"[ANALYTICS] Using trending data file: {latest_trending_file.name}")
                
                try:
                    with open(latest_trending_file, 'r', encoding='utf-8') as f:
                        trending_data = json.load(f)
                    
                    # Extract posts from trending data format
                    if isinstance(trending_data, list):
                        for item in trending_data:
                            if isinstance(item, dict):
                                normalized_post = self._normalize_trending_post(item)
                                posts.append(normalized_post)
                    elif isinstance(trending_data, dict):
                        if 'posts' in trending_data:
                            for post in trending_data['posts']:
                                normalized_post = self._normalize_trending_post(post)
                                posts.append(normalized_post)
                        elif 'data' in trending_data:
                            for post in trending_data['data']:
                                normalized_post = self._normalize_trending_post(post)
                                posts.append(normalized_post)
                        else:
                            # Try to treat the whole object as a single post
                            normalized_post = self._normalize_trending_post(trending_data)
                            posts.append(normalized_post)
                
                except Exception as e:
                    logger.warning(f"Could not read trending file {latest_trending_file}: {str(e)}")
            
            return posts

        except Exception as e:
            logger.warning(f"Error collecting from trending files: {str(e)}")
            return []

    def _normalize_trending_post(self, trending_post: Dict) -> Dict:
        """Normalize trending post data to trending analysis format."""
        return {
            'id': trending_post.get('id', trending_post.get('post_id', f"trending_{hash(str(trending_post)) % 100000}")),
            'content': trending_post.get('content', trending_post.get('text', trending_post.get('message', ''))),
            'author': trending_post.get('author', trending_post.get('username', trending_post.get('user', 'unknown'))),
            'story_score': trending_post.get('story_score', trending_post.get('content_score', 65)),
            'engagement_score': trending_post.get('engagement_score', trending_post.get('likes', 0) + trending_post.get('shares', 0) + trending_post.get('comments', 0)),
            'velocity': trending_post.get('velocity', trending_post.get('growth_rate', 2.0)),
            'network_influence': trending_post.get('network_influence', trending_post.get('reach', 0.6)),
            'timing_score': trending_post.get('timing_score', trending_post.get('optimal_time', 70)),
            'strategic_score': trending_post.get('strategic_score', trending_post.get('business_value', 60)),
            'source_engine': 'trending_data_file'
        }

    def _normalize_raw_post(self, raw_post: Dict) -> Dict:
        """Normalize raw post data to trending analysis format."""
        return {
            'id': raw_post.get('id', raw_post.get('post_id', f"raw_{hash(str(raw_post)) % 100000}")),
            'content': raw_post.get('content', raw_post.get('text', raw_post.get('message', ''))),
            'author': raw_post.get('author', raw_post.get('username', raw_post.get('user', 'unknown'))),
            'story_score': raw_post.get('story_score', 55),
            'engagement_score': raw_post.get('engagement_score', raw_post.get('likes', 0) + raw_post.get('shares', 0)),
            'velocity': raw_post.get('velocity', 1.5),
            'network_influence': raw_post.get('network_influence', 0.4),
            'timing_score': raw_post.get('timing_score', 60),
            'strategic_score': raw_post.get('strategic_score', 45),
            'source_engine': 'raw_data'
        }

    async def _generate_mock_trending_data(self) -> List[Dict]:
        """Generate mock data for trending analysis testing."""
        try:
            # Try to import mock data provider
            from mock_data_provider import MockDataProvider
            provider = MockDataProvider()

            # Generate trending-focused dataset
            mock_posts = provider.generate_trending_dataset(count=20)

            # Normalize mock posts for trending analysis
            normalized_posts = []
            for post in mock_posts:
                normalized_post = {
                    'id': post.get('id', f"mock_{len(normalized_posts)}"),
                    'content': post.get('content', post.get('text', '')),
                    'author': post.get('author', f"user_{len(normalized_posts)}"),
                    'story_score': post.get('story_score', 60 + (len(normalized_posts) % 40)),
                    'engagement_score': post.get('engagement_score', 50 + (len(normalized_posts) % 50)),
                    'velocity': post.get('velocity', 1.0 + (len(normalized_posts) % 5)),
                    'network_influence': post.get('network_influence', 0.3 + (len(normalized_posts) % 7) / 10),
                    'timing_score': post.get('timing_score', 45 + (len(normalized_posts) % 55)),
                    'strategic_score': post.get('strategic_score', 40 + (len(normalized_posts) % 60)),
                    'source_engine': 'mock_data'
                }
                normalized_posts.append(normalized_post)

            logger.info(
                f"[NOTE] Generated {len(normalized_posts)} mock posts for trending analysis")
            return normalized_posts

        except ImportError:
            logger.warning(
                "Mock data provider not available, generating basic mock data")

            # Generate basic mock posts
            basic_mock_posts = []
            for i in range(15):
                post = {
                    'id': f"trending_mock_{i+1}",
                    'content': f"Mock trending post #{i+1} with engaging content about current events",
                    'author': f"trending_user_{i+1}",
                    'story_score': 60 + (i * 3) % 40,
                    'engagement_score': 55 + (i * 4) % 45,
                    'velocity': 1.2 + (i * 0.3) % 4,
                    'network_influence': 0.4 + (i * 0.05) % 0.6,
                    'timing_score': 50 + (i * 5) % 50,
                    'strategic_score': 45 + (i * 4) % 55,
                    'source_engine': 'basic_mock'
                }
                basic_mock_posts.append(post)

            return basic_mock_posts

    async def _save_analysis_results(self, analysis_results: Dict, batch_id: str):
        """Save trending prediction analysis results to structured files."""
        try:
            # Create timestamped directory
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            results_dir = self.reports_path / f"{batch_id}_{timestamp}"
            results_dir.mkdir(parents=True, exist_ok=True)

            # Save main analysis results
            results_file = results_dir / "trending_analysis.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2,
                          ensure_ascii=False, default=str)

            # Save trending candidates separately for easy access
            if analysis_results.get('trending_candidates'):
                candidates_file = results_dir / "trending_candidates.json"
                with open(candidates_file, 'w', encoding='utf-8') as f:
                    json.dump(
                        analysis_results['trending_candidates'], f, indent=2, ensure_ascii=False)

            # Save Discord message for reference
            discord_file = results_dir / "discord_message.txt"
            with open(discord_file, 'w', encoding='utf-8') as f:
                f.write(analysis_results.get(
                    'discord_message', 'No Discord message generated'))

            logger.info(f"[SAVE] Analysis results saved to {results_dir}")

        except Exception as e:
            logger.error(f"[ERROR] Error saving analysis results: {str(e)}")

    async def _send_discord_notification(self, analysis_results: Dict) -> bool:
        """Send Discord notification with trending prediction results."""
        if not self.discord_sender:
            logger.warning(
                "Discord sender not available, skipping notification")
            return False

        try:
            discord_message = analysis_results.get(
                'discord_message', 'Trending analysis completed')

            # Send as rich embed if possible
            success = await self.discord_sender.send_rich_embed(
                title="[HOT] Trending Prediction Report",
                description=discord_message,
                color=0xFF6B35,  # Orange color for trending
                fields=[
                    {
                        "name": "[ANALYTICS] Analysis Summary",
                        "value": f"Posts: {analysis_results.get('posts_analyzed', 0)}\nCandidates: {len(analysis_results.get('trending_candidates', []))}",
                        "inline": True
                    },
                    {
                        "name": "💯 Average Score",
                        "value": f"{analysis_results.get('average_final_score', 0):.1f}",
                        "inline": True
                    }
                ]
            )

            if success:
                logger.info("[OK] Discord notification sent successfully")
                return True
            else:
                # Fallback to simple message
                success = await self.discord_sender.send_message(discord_message)
                return success

        except Exception as e:
            logger.error(f"[ERROR] Error sending Discord notification: {str(e)}")
            return False

    async def _generate_workflow_insights(self, analysis_results: Dict) -> List[str]:
        """Generate workflow-specific insights and recommendations."""
        insights = []

        try:
            posts_count = analysis_results.get('posts_analyzed', 0)
            candidates_count = len(
                analysis_results.get('trending_candidates', []))
            avg_score = analysis_results.get('average_final_score', 0)

            # Workflow performance insights
            insights.append(
                f"[SEARCH] Processed {posts_count} posts across multiple analysis engines")

            if candidates_count > 0:
                insights.append(
                    f"[TARGET] Identified {candidates_count} high-potential trending candidates")
            else:
                insights.append(
                    "[TRENDING_UP] No posts currently meet trending threshold - consider content strategy review")

            # Score-based insights
            if avg_score >= 80:
                insights.append(
                    "💪 Strong overall content performance detected")
            elif avg_score >= 60:
                insights.append(
                    "[ANALYTICS] Moderate content performance - optimization opportunities available")
            else:
                insights.append(
                    "[FAST] Content performance below average - strategic improvements recommended")

            # Factor-based insights
            top_factors = analysis_results.get('top_influencing_factors', [])
            if top_factors:
                insights.append(
                    f"[CIRCUS] Key success factors: {', '.join(top_factors[:2])}")

            return insights

        except Exception as e:
            logger.error(f"Error generating workflow insights: {str(e)}")
            return ['Workflow completed successfully']


# Standalone task execution function
async def run_trending_prediction_task(batch_id: str = None) -> Dict:
    """
    Standalone function to execute trending prediction task.

    Args:
        batch_id: Optional batch identifier for tracking

    Returns:
        Dictionary containing task execution results
    """
    task = TrendingPredictionTask()
    return await task.run_trending_prediction_workflow(batch_id)


# Task configuration and scheduling utilities
def get_trending_task_config() -> Dict:
    """Get trending prediction task configuration for scheduler integration."""
    return {
        'task_name': 'trending_prediction',
        'function': run_trending_prediction_task,
        'schedule': {
            'trigger': 'interval',
            'minutes': 35,  # Every 35 minutes
            'misfire_grace_time': 300  # 5 minute grace period
        },
        'description': 'Trending Prediction Analysis - AI-powered viral potential scoring',
        'dependencies': [
            'content_analysis',
            'engagement_intelligence',
            'network_intelligence',
            'temporal_analytics',
            'strategic_intelligence'
        ],
        'outputs': [
            'trending_candidates',
            'probability_scores',
            'discord_notifications',
            'analysis_reports'
        ]
    }


if __name__ == "__main__":
    # Demo execution
    async def demo():
        print("[HOT] Trending Prediction Task Demo")
        print("=" * 50)

        task = TrendingPredictionTask()
        result = await task.run_trending_prediction_workflow("demo_trending_task")

        print(f"[ANALYTICS] Task Results:")
        print(f"Status: {result.get('status')}")
        print(f"Posts Processed: {result.get('posts_processed', 0)}")
        print(f"Trending Candidates: {result.get('trending_candidates', 0)}")
        print(f"Average Score: {result.get('average_score', 0)}")
        print(
            f"Discord Notification: {result.get('discord_notification', False)}")

        if result.get('workflow_insights'):
            print("\n[IDEA] Workflow Insights:")
            for insight in result['workflow_insights']:
                print(f"  • {insight}")

    asyncio.run(demo())
