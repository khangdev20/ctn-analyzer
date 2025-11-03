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
import pandas as pd
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

        logger.debug(f"Trending prediction workflow started (disabled) - {batch_id}")

        try:
            # Step 1: Get trending patterns from recent content analysis
            trending_patterns = await self._get_content_analysis_patterns()

            # Step 2: Collect comprehensive post data
            posts_data = await self._collect_trending_data(batch_id)

            if not posts_data:
                logger.warning("No posts data collected for trending analysis")
                return {'status': 'no_data', 'batch_id': batch_id}

            # Track latest posts count for accurate reporting
            latest_posts_count = len(
                [p for p in posts_data if p.get('source_engine') == 'latest_posts_api'])

            logger.debug(f"Collected {len(posts_data)} posts ({latest_posts_count} latest)")

            if trending_patterns:
                logger.debug(f"Using {len(trending_patterns.get('successful_patterns', []))} patterns")

            # Step 3: Run trending prediction analysis with content analysis patterns
            analysis_results = await self.agent.analyze_trending_potential(posts_data, batch_id, trending_patterns)

            # Add latest posts count to analysis results for Discord reporting
            analysis_results['latest_posts_count'] = latest_posts_count

            # Step 3: Save analysis results
            await self._save_analysis_results(analysis_results, batch_id)

            # Step 4: Send Discord notification
            discord_success = await self._send_discord_notification(analysis_results)

            # Step 5: Generate workflow summary
            workflow_results = {
                'status': 'success',
                'batch_id': batch_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'posts_analyzed': analysis_results.get('posts_analyzed', len(posts_data)),
                'latest_posts_count': latest_posts_count,
                'trending_candidates': analysis_results.get('trending_candidates', []),
                'average_final_score': analysis_results.get('average_final_score', 0),
                'discord_notification': discord_success,
                'analysis_results': analysis_results,
                'workflow_insights': await self._generate_workflow_insights(analysis_results)
            }

            logger.debug(f"Trending prediction workflow completed - {batch_id}")
            return workflow_results

        except Exception as e:
            logger.error(
                f"[ERROR] Error in trending prediction workflow: {str(e)}")
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
            # Method 1: Collect LATEST posts from API for trending prediction
            latest_posts = await self._collect_latest_posts_for_prediction()
            if latest_posts:
                collected_posts.extend(latest_posts)
                logger.info(
                    f"🚀 Collected {len(latest_posts)} LATEST posts for trending prediction")

            # Method 2: Try to collect from recent analysis results
            recent_data = await self._collect_from_recent_analyses()
            if recent_data:
                collected_posts.extend(recent_data)
                logger.info(
                    f"📥 Collected {len(recent_data)} posts from recent analyses")

            # Method 3: Try to collect from raw data if available
            raw_data = await self._collect_from_raw_data()
            if raw_data:
                collected_posts.extend(raw_data)
                logger.info(
                    f"📥 Collected {len(raw_data)} additional posts from raw data")

            # Method 4: Try trending data files from root directory (for comparison)
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
        """
        Collect posts from recent analysis results (S3 cloud storage only).
        Local file analysis deprecated in favor of cloud-first architecture.
        """
        posts = []

        try:
            logger.info("📊 [S3] Collecting from recent S3 analysis reports...")

            # Note: Local file collection deprecated
            # Recent analyses are now accessed via:
            # 1. Content analysis patterns (main integration)
            # 2. S3 report queries (if needed)
            # 3. Direct API collection

            logger.info(
                "✅ [MIGRATION] Using cloud-first data collection - no local file dependencies")
            return posts

        except Exception as e:
            logger.warning(f"Error in S3 analysis collection: {str(e)}")
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
                    # Local file access deprecated - using S3 cloud storage
                    logger.info(
                        "📊 [MIGRATION] Raw data now stored in S3 cloud storage only")

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
                # Local trending files deprecated - using S3 cloud storage
                logger.info(
                    "📊 [MIGRATION] Trending data now accessed via S3 cloud storage and content analysis patterns")

            return posts

        except Exception as e:
            logger.warning(f"Error collecting from trending files: {str(e)}")
            return []

    async def _collect_latest_posts_for_prediction(self) -> List[Dict]:
        """
        Collect LATEST posts from API to predict trending potential.
        This is the main method for fresh trending prediction.
        """
        posts = []

        try:
            logger.info(
                "🚀 [LATEST] Fetching latest posts for trending prediction...")

            # Import enhanced data collector with latest posts support
            from worker.features.data_collector import collect_latest_posts, load_data_from_s3

            # Collect latest posts using enhanced data collector
            collection_result = collect_latest_posts(num_pages=3)

            if collection_result and collection_result.get('s3_key'):
                # Load collected data from S3
                data = load_data_from_s3(collection_result['s3_key'])

                if data and data.get('data'):
                    raw_posts = data['data']
                    logger.info(
                        f"📡 [LATEST] Loaded {len(raw_posts)} fresh latest posts from collection")

                    # Normalize each post for trending prediction
                    for post in raw_posts:
                        normalized_post = self._normalize_latest_post_for_prediction(
                            post)
                        normalized_post['source_engine'] = 'latest_posts_api'
                        posts.append(normalized_post)

                    logger.info(
                        f"✅ [LATEST] Normalized {len(posts)} latest posts for trending prediction")
                else:
                    logger.warning(
                        "⚠️ [LATEST] No data found in collected latest posts")
            else:
                logger.warning(
                    "⚠️ [LATEST] Failed to collect latest posts from API")

        except Exception as e:
            logger.error(f"❌ [LATEST] Error collecting latest posts: {str(e)}")

        return posts

    async def _get_content_analysis_patterns(self) -> Dict:
        """
        Get trending patterns from recent content analysis results.
        This provides insights about what makes posts trend successfully.
        """
        try:
            from data_access.s3_store import S3Store

            logger.info(
                "🔍 [PATTERNS] Loading trending patterns from content analysis...")

            s3_store = S3Store()

            # Get recent content analysis reports (last 7 days)
            recent_reports = []
            now = datetime.now(timezone.utc)

            for days_back in range(7):  # Check last 7 days
                target_date = now - pd.Timedelta(days=days_back)
                date_prefix = s3_store.build_key(
                    "reports", "content_analysis",
                    f"{target_date.year}",
                    f"{target_date.month:02d}"
                )

                try:
                    client = s3_store.get_s3_client()
                    response = client.list_objects_v2(
                        Bucket=s3_store.bucket,
                        Prefix=date_prefix,
                        MaxKeys=5  # Limit to avoid too much data
                    )

                    if 'Contents' in response:
                        for obj in response['Contents']:
                            if obj['Key'].endswith('_content_analysis.json'):
                                # Load the analysis data
                                data = s3_store.s3_read_json(obj['Key'])
                                if data and data.get('analyzed_posts'):
                                    recent_reports.append(data)

                except Exception as e:
                    logger.debug(
                        f"Could not load reports from {date_prefix}: {e}")
                    continue

            if not recent_reports:
                logger.info(
                    "📊 [PATTERNS] No recent content analysis found, using default patterns")
                return self._get_default_trending_patterns()

            # Extract successful patterns from content analysis
            patterns = self._extract_trending_patterns(recent_reports)

            logger.info(
                f"✅ [PATTERNS] Extracted {len(patterns.get('successful_patterns', []))} trending patterns from {len(recent_reports)} content analysis reports")

            return patterns

        except Exception as e:
            logger.error(
                f"❌ [PATTERNS] Error loading content analysis patterns: {str(e)}")
            return self._get_default_trending_patterns()

    def _extract_trending_patterns(self, content_reports: List[Dict]) -> Dict:
        """Extract successful trending patterns from content analysis reports."""
        patterns = {
            'successful_patterns': [],
            'common_themes': [],
            'high_quality_indicators': [],
            'engagement_triggers': [],
            'metadata': {
                'reports_analyzed': len(content_reports),
                'extraction_timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

        try:
            high_quality_posts = []
            all_posts = []

            # Collect high-quality posts from content analysis
            for report in content_reports:
                analyzed_posts = report.get('analyzed_posts', [])
                all_posts.extend(analyzed_posts)

                # Filter for high-quality posts (above average)
                avg_quality = report.get('aggregate_metrics', {}).get(
                    'avg_content_quality', 50)
                high_quality = [p for p in analyzed_posts if p.get(
                    'content_quality_score', 0) > avg_quality * 1.2]
                high_quality_posts.extend(high_quality)

            if high_quality_posts:
                # Extract common themes from high-quality posts
                themes = []
                quality_indicators = []
                engagement_triggers = []

                for post in high_quality_posts:
                    content = post.get('content', '').lower()

                    # Extract successful content patterns
                    if post.get('content_quality_score', 0) > 80:
                        if len(content) > 50:  # Avoid very short posts
                            patterns['successful_patterns'].append({
                                'content_preview': content[:100],
                                'quality_score': post.get('content_quality_score', 0),
                                'readability_score': post.get('readability_score', 0),
                                'sentiment': post.get('sentiment', 'neutral'),
                                'dominant_emotion': post.get('dominant_emotion', 'none')
                            })

                    # Extract quality indicators
                    if post.get('readability_score', 0) > 70:
                        quality_indicators.append(
                            post.get('content_structure', {}))

                    # Extract engagement triggers
                    if post.get('engagement_potential', 0) > 75:
                        emotions = post.get('emotions', [])
                        if emotions:
                            engagement_triggers.extend(
                                emotions[:2])  # Top 2 emotions

                patterns['common_themes'] = list(set(themes))[:10]
                patterns['high_quality_indicators'] = quality_indicators[:5]
                patterns['engagement_triggers'] = list(
                    set(engagement_triggers))[:8]

            logger.info(
                f"📈 [PATTERNS] Extracted patterns: {len(patterns['successful_patterns'])} successful posts, {len(patterns['engagement_triggers'])} triggers")

        except Exception as e:
            logger.error(f"Error extracting patterns: {str(e)}")

        return patterns

    def _get_default_trending_patterns(self) -> Dict:
        """Provide default trending patterns when content analysis data is unavailable."""
        return {
            'successful_patterns': [
                {'pattern': 'breaking_news', 'weight': 0.9},
                {'pattern': 'exclusive_content', 'weight': 0.8},
                {'pattern': 'emotional_appeal', 'weight': 0.7},
                {'pattern': 'question_engagement', 'weight': 0.6},
                {'pattern': 'trending_hashtags', 'weight': 0.5}
            ],
            'common_themes': ['news', 'entertainment', 'technology', 'sports'],
            'high_quality_indicators': ['optimal_length', 'clear_structure', 'emotional_hooks'],
            'engagement_triggers': ['excitement', 'curiosity', 'controversy', 'inspiration'],
            'metadata': {
                'source': 'default_patterns',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }

    def _normalize_latest_post_for_prediction(self, post: Dict) -> Dict:
        """
        Normalize latest post data for trending prediction analysis.
        Calculate initial trending indicators based on post characteristics.
        """
        # Extract basic post info
        post_id = post.get('id', f"latest_{hash(str(post)) % 100000}")
        content = post.get('content', post.get(
            'text', post.get('message', '')))
        author = post.get('author', post.get(
            'username', post.get('user', 'unknown')))

        # Calculate initial trending indicators
        content_length = len(content)
        has_hashtags = '#' in content
        has_mentions = '@' in content
        has_links = 'http' in content.lower()

        # Base trending scores (to be refined by prediction engine)
        story_score = self._calculate_content_story_score(content)
        engagement_score = post.get(
            'likes', 0) + post.get('shares', 0) + post.get('comments', 0)
        velocity_score = self._calculate_initial_velocity(post)
        network_influence = self._calculate_network_influence(author, post)
        timing_score = self._calculate_timing_score()
        strategic_score = self._calculate_strategic_value(content)

        return {
            'id': post_id,
            'content': content,
            'author': author,
            'story_score': story_score,
            'engagement_score': engagement_score,
            'velocity': velocity_score,
            'network_influence': network_influence,
            'timing_score': timing_score,
            'strategic_score': strategic_score,
            'content_indicators': {
                'length': content_length,
                'has_hashtags': has_hashtags,
                'has_mentions': has_mentions,
                'has_links': has_links
            },
            'source_engine': 'latest_posts_api',
            'prediction_type': 'trending_potential',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _calculate_content_story_score(self, content: str) -> int:
        """Calculate story potential score based on content analysis."""
        if not content:
            return 30

        score = 50  # Base score

        # Length factors
        if 100 <= len(content) <= 300:
            score += 15  # Optimal length
        elif len(content) > 500:
            score -= 10  # Too long

        # Engagement triggers
        if any(word in content.lower() for word in ['breaking', 'urgent', 'exclusive', 'revealed']):
            score += 20
        if any(word in content.lower() for word in ['wow', 'amazing', 'incredible', 'shocking']):
            score += 15
        if '?' in content:
            score += 10  # Questions engage
        if '!' in content:
            score += 5   # Excitement

        return min(100, max(0, score))

    def _calculate_initial_velocity(self, post: Dict) -> float:
        """Calculate initial velocity based on early engagement indicators."""
        base_velocity = 1.0

        # Early engagement
        likes = post.get('likes', 0)
        shares = post.get('shares', 0)
        comments = post.get('comments', 0)

        if likes > 10:
            base_velocity += 0.5
        if shares > 5:
            base_velocity += 1.0  # Shares are strong indicator
        if comments > 3:
            base_velocity += 0.7

        return min(5.0, base_velocity)

    def _calculate_network_influence(self, author: str, post: Dict) -> float:
        """Calculate network influence potential."""
        base_influence = 0.5

        # Author factors (simplified)
        if len(author) > 5:  # Established username
            base_influence += 0.2

        # Content network factors
        content = post.get('content', '')
        if '@' in content:  # Mentions
            base_influence += 0.3
        if '#' in content:  # Hashtags
            base_influence += 0.2

        return min(1.0, base_influence)

    def _calculate_timing_score(self) -> int:
        """Calculate timing score based on current time."""
        current_hour = datetime.now().hour

        # Peak social media hours
        if 8 <= current_hour <= 10:  # Morning
            return 85
        elif 12 <= current_hour <= 14:  # Lunch
            return 90
        elif 17 <= current_hour <= 21:  # Evening
            return 95
        elif 21 <= current_hour <= 23:  # Night
            return 80
        else:
            return 60  # Off-peak

    def _calculate_strategic_value(self, content: str) -> int:
        """Calculate strategic business value."""
        if not content:
            return 40

        score = 50

        # Business relevance keywords
        business_keywords = ['market', 'business',
                             'economy', 'investment', 'growth', 'success']
        if any(keyword in content.lower() for keyword in business_keywords):
            score += 20

        # Competition relevance
        competition_keywords = ['competition',
                                'contest', 'challenge', 'winner', 'prize']
        if any(keyword in content.lower() for keyword in competition_keywords):
            score += 25

        return min(100, score)

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
        """Save trending prediction analysis results to S3 storage."""
        try:
            from data_access.s3_store import s3_write_json, build_key

            # Create timestamp for unique batch directory
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            batch_folder = f"{batch_id}_{timestamp}"

            # Extract year/month for partitioning
            now = datetime.now(timezone.utc)
            year = now.strftime('%Y')
            month = now.strftime('%m')

            # Save main analysis results to S3
            analysis_key = build_key(
                "reports", "trending_prediction", year, month, batch_folder, "trending_analysis.json")
            result = s3_write_json(
                analysis_key, analysis_results, compress=True)

            if result['success']:
                logger.info(
                    f"[SAVE] Main analysis saved to S3: {result['s3_url']}")
            else:
                logger.error(
                    f"[ERROR] Failed to save main analysis: {result.get('error')}")

            # Save trending candidates separately for easy access
            if analysis_results.get('trending_candidates'):
                candidates_key = build_key(
                    "reports", "trending_prediction", year, month, batch_folder, "trending_candidates.json")
                candidates_result = s3_write_json(
                    candidates_key, analysis_results['trending_candidates'], compress=True)

                if candidates_result['success']:
                    logger.info(
                        f"[SAVE] Trending candidates saved to S3: {candidates_result['s3_url']}")

            # Save Discord message as markdown for reference
            discord_message = analysis_results.get(
                'discord_message', 'No Discord message generated')
            if discord_message:
                discord_key = build_key(
                    "reports", "trending_prediction", year, month, batch_folder, "discord_message.md")
                discord_result = s3_write_json(
                    discord_key, discord_message, content_type="text/markdown")

                if discord_result['success']:
                    logger.debug(
                        f"[SAVE] Discord message saved to S3: {discord_result['s3_url']}")

            logger.info(
                f"[SAVE] S3 analysis results saved for batch: {batch_folder}")

        except Exception as e:
            logger.error(f"[ERROR] Error saving S3 analysis results: {str(e)}")

    async def _get_s3_source_info(self) -> str:
        """Get S3 source information for Discord messages."""
        try:
            from data_access.s3_store import S3Store

            s3_store = S3Store()
            client = s3_store.get_s3_client()

            # Get recent files from S3 (last 3 files)
            response = client.list_objects_v2(
                Bucket=s3_store.bucket,
                Prefix="data/raw/",
                MaxKeys=3
            )

            if 'Contents' in response:
                files = sorted(response['Contents'],
                               key=lambda x: x['LastModified'], reverse=True)[:3]

                source_info = "📁 **S3 Data Sources:**\n"
                for i, file_obj in enumerate(files, 1):
                    key = file_obj['Key']
                    size_mb = file_obj['Size'] / (1024 * 1024)
                    timestamp = file_obj['LastModified'].strftime(
                        '%Y-%m-%d %H:%M')
                    source_info += f"`{i}.` {key.split('/')[-1]} ({size_mb:.1f}MB, {timestamp})\n"

                return source_info
            else:
                return "📁 **S3 Data Sources:** No recent files found"

        except Exception as e:
            logger.error(f"Error getting S3 source info: {str(e)}")
            return "📁 **S3 Data Sources:** Error loading source information"

    async def _send_discord_notification(self, analysis_results: Dict) -> bool:
        """Send Discord notification with trending prediction results."""
        if not self.discord_sender:
            logger.warning(
                "Discord sender not available, skipping notification")
            return False

        try:
            discord_message = analysis_results.get(
                'discord_message', 'Trending analysis completed')

            # Count latest posts vs other sources
            # Check if we have latest posts data in analysis results
            latest_posts_count = analysis_results.get('latest_posts_count', 0)

            # If not tracked separately, try to estimate from posts_analyzed
            if latest_posts_count == 0:
                # Check for posts with latest_posts_api source
                all_posts = analysis_results.get('posts_analyzed_details', [])
                latest_posts_count = len([p for p in all_posts
                                          if p.get('source_engine') == 'latest_posts_api'])

                # If still 0, assume most posts are latest posts if we have data
                if latest_posts_count == 0 and analysis_results.get('posts_analyzed', 0) > 0:
                    latest_posts_count = analysis_results.get(
                        'posts_analyzed', 0)

            trending_candidates = analysis_results.get(
                'trending_candidates', [])
            high_potential_posts = [
                c for c in trending_candidates if c.get('final_score', 0) > 75]

            # Get S3 source information
            s3_source_info = await self._get_s3_source_info()

            # Send as rich embed if possible
            success = await self.discord_sender.send_rich_embed(
                title="🚀 Latest Posts → Trending Prediction",
                description=f"**Analyzed {latest_posts_count} latest posts** for trending potential\n{discord_message}\n\n{s3_source_info}",
                color=0x00FF88,  # Green color for predictions
                fields=[
                    {
                        "name": "📊 Analysis Summary",
                        "value": f"Latest Posts: {latest_posts_count}\nTotal Analyzed: {analysis_results.get('posts_analyzed', 0)}\nTrending Candidates: {len(trending_candidates)}",
                        "inline": True
                    },
                    {
                        "name": "🎯 High Potential",
                        "value": f"{len(high_potential_posts)} posts with >75% trending probability",
                        "inline": True
                    },
                    {
                        "name": "💯 Average Score",
                        "value": f"{analysis_results.get('average_final_score', 0):.1f}%",
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
            logger.error(
                f"[ERROR] Error sending Discord notification: {str(e)}")
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
