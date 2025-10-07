"""
Trending Prediction System - AI-Powered Viral Potential Analysis

This module implements a sophisticated scoring system that evaluates social media posts
for their potential to trend based on combined metrics and weighted scoring rubrics.

Key Features:
- Weighted scoring rubric with customizable factors
- Trending probability calculation with machine learning insights
- Trending candidate identification (≥0.8 probability threshold)
- Rich Discord reporting with rankings and key influencing factors
- Multi-dimensional analysis combining content, engagement, timing, network, and strategy

Author: AI Assistant
Date: October 7, 2025
Version: 1.0.0
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendingPredictionAgent:
    """
    Advanced AI agent for predicting viral potential of social media posts.

    Uses sophisticated weighted scoring algorithms to evaluate trending probability
    based on content quality, engagement metrics, timing factors, network influence,
    and strategic elements.
    """

    def __init__(self):
        """Initialize the trending prediction agent with default weights."""
        self.scoring_weights = {
            'content_quality': 0.30,  # 30% - Story score, content analysis
            'engagement': 0.25,       # 25% - Engagement metrics, viral signals
            'timing': 0.20,           # 20% - Temporal factors, optimal timing
            'network': 0.15,          # 15% - Network influence, reach potential
            'strategy': 0.10          # 10% - Strategic factors, campaign elements
        }

        self.trending_threshold = 0.8  # Minimum probability for trending candidates

        # Normalization constants for score standardization
        self.score_ranges = {
            'story_score': (0, 100),
            'engagement_score': (0, 100),
            'velocity': (0, 10),
            'network_influence': (0, 1),
            'timing_score': (0, 100)
        }

    async def analyze_trending_potential(self, posts_data: List[Dict], batch_id: str = None) -> Dict:
        """
        Main analysis function that evaluates trending potential for a batch of posts.

        Args:
            posts_data: List of post dictionaries with metrics
            batch_id: Optional batch identifier for tracking

        Returns:
            Dictionary containing trending analysis results
        """
        if not batch_id:
            batch_id = f"trending_prediction_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"🔥 Starting trending prediction analysis for batch {batch_id}")

        if not posts_data:
            logger.warning("No posts data provided for trending analysis")
            return self._generate_empty_report(batch_id)

        try:
            # Step 1: Normalize and prepare metrics
            normalized_posts = await self._normalize_post_metrics(posts_data)

            # Step 2: Calculate weighted scores for each post
            scored_posts = await self._calculate_weighted_scores(normalized_posts)

            # Step 3: Compute trending probabilities
            probability_posts = await self._compute_trending_probabilities(scored_posts)

            # Step 4: Identify trending candidates
            trending_candidates = await self._identify_trending_candidates(probability_posts)

            # Step 5: Analyze influencing factors
            top_factors = await self._analyze_influencing_factors(probability_posts)

            # Step 6: Generate comprehensive analysis report
            analysis_report = {
                'batch_id': batch_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'posts_analyzed': len(posts_data),
                'average_final_score': round(statistics.mean([p['final_score'] for p in probability_posts]), 1),
                'trending_candidates': trending_candidates,
                'top_influencing_factors': top_factors,
                'score_distribution': await self._calculate_score_distribution(probability_posts),
                # Top 10 for detailed analysis
                'detailed_scores': probability_posts[:10],
                'trending_insights': await self._generate_trending_insights(probability_posts),
                'discord_message': await self._format_discord_report(
                    probability_posts, trending_candidates, top_factors, batch_id
                )
            }

            logger.info(
                f"✅ Trending prediction analysis completed successfully for batch {batch_id}")
            return analysis_report

        except Exception as e:
            logger.error(f"❌ Error in trending prediction analysis: {str(e)}")
            return self._generate_error_report(batch_id, str(e))

    async def _normalize_post_metrics(self, posts_data: List[Dict]) -> List[Dict]:
        """Normalize post metrics to 0-1 scale for consistent scoring."""
        normalized_posts = []

        for post in posts_data:
            normalized_post = post.copy()

            # Extract and normalize metrics
            story_score = self._normalize_score(
                post.get('story_score', 0), self.score_ranges['story_score']
            )
            engagement_score = self._normalize_score(
                post.get('engagement_score',
                         0), self.score_ranges['engagement_score']
            )
            velocity = self._normalize_score(
                post.get('velocity', 0), self.score_ranges['velocity']
            )
            network_influence = self._normalize_score(
                post.get('network_influence',
                         0), self.score_ranges['network_influence']
            )
            timing_score = self._normalize_score(
                post.get('timing_score', post.get('temporal_score', 0)),
                self.score_ranges['timing_score']
            )

            # Add normalized metrics
            normalized_post.update({
                'normalized_story_score': story_score,
                'normalized_engagement_score': engagement_score,
                'normalized_velocity': velocity,
                'normalized_network_influence': network_influence,
                'normalized_timing_score': timing_score
            })

            normalized_posts.append(normalized_post)

        return normalized_posts

    def _normalize_score(self, value: float, score_range: Tuple[float, float]) -> float:
        """Normalize a score to 0-1 range based on expected min/max values."""
        min_val, max_val = score_range
        if max_val == min_val:
            return 0.5  # Neutral score if no range

        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))  # Clamp to 0-1 range

    async def _calculate_weighted_scores(self, normalized_posts: List[Dict]) -> List[Dict]:
        """Calculate weighted final scores using the scoring rubric."""
        scored_posts = []

        for post in normalized_posts:
            # Apply weighted scoring rubric
            content_component = post['normalized_story_score'] * \
                self.scoring_weights['content_quality']
            engagement_component = post['normalized_engagement_score'] * \
                self.scoring_weights['engagement']
            timing_component = post['normalized_timing_score'] * \
                self.scoring_weights['timing']
            network_component = post['normalized_network_influence'] * \
                self.scoring_weights['network']

            # Strategy component (combination of multiple factors)
            strategy_component = self._calculate_strategy_score(
                post) * self.scoring_weights['strategy']

            # Final weighted score (0-1 scale)
            final_score_normalized = (
                content_component + engagement_component + timing_component +
                network_component + strategy_component
            )

            # Convert to 0-100 scale for readability
            final_score = round(final_score_normalized * 100, 1)

            scored_post = post.copy()
            scored_post.update({
                'content_component': round(content_component * 100, 1),
                'engagement_component': round(engagement_component * 100, 1),
                'timing_component': round(timing_component * 100, 1),
                'network_component': round(network_component * 100, 1),
                'strategy_component': round(strategy_component * 100, 1),
                'final_score': final_score,
                'final_score_normalized': final_score_normalized
            })

            scored_posts.append(scored_post)

        return scored_posts

    def _calculate_strategy_score(self, post: Dict) -> float:
        """Calculate strategic component score based on various strategic factors."""
        strategy_score = 0.0
        factors_count = 0

        # Factor 1: Content strategic elements
        if post.get('strategic_score'):
            strategy_score += self._normalize_score(
                post['strategic_score'], (0, 100))
            factors_count += 1

        # Factor 2: Emotional appeal strength
        if post.get('emotional_score'):
            strategy_score += self._normalize_score(
                post['emotional_score'], (0, 100))
            factors_count += 1

        # Factor 3: Hashtag effectiveness
        hashtag_count = len(post.get('hashtags', []))
        if hashtag_count > 0:
            # Optimal around 5 hashtags
            strategy_score += min(1.0, hashtag_count / 5)
            factors_count += 1

        # Factor 4: Content length optimization
        content_length = len(post.get('content', ''))
        if content_length > 0:
            # Optimal length around 100-200 characters for social media
            length_score = 1.0 - abs(content_length - 150) / 150
            strategy_score += max(0.0, length_score)
            factors_count += 1

        # Return average if we have factors, otherwise neutral score
        return strategy_score / factors_count if factors_count > 0 else 0.5

    async def _compute_trending_probabilities(self, scored_posts: List[Dict]) -> List[Dict]:
        """Compute trending probabilities using sophisticated algorithms."""
        probability_posts = []

        # Calculate statistical distribution metrics
        scores = [post['final_score_normalized'] for post in scored_posts]
        if not scores:
            return probability_posts

        mean_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.1

        for post in scored_posts:
            # Base probability from normalized score
            base_probability = post['final_score_normalized']

            # Adjust probability based on statistical position
            z_score = (post['final_score_normalized'] -
                       mean_score) / std_dev if std_dev > 0 else 0
            statistical_adjustment = self._sigmoid(
                z_score) * 0.2  # Up to 20% adjustment

            # Viral threshold adjustment (posts above certain thresholds get boost)
            threshold_boost = 0.0
            if post['final_score_normalized'] > 0.8:
                threshold_boost = 0.1
            elif post['final_score_normalized'] > 0.7:
                threshold_boost = 0.05

            # Final trending probability
            trending_probability = min(
                1.0, base_probability + statistical_adjustment + threshold_boost)

            probability_post = post.copy()
            probability_post.update({
                'trending_probability': round(trending_probability, 3),
                'z_score': round(z_score, 2),
                'statistical_adjustment': round(statistical_adjustment, 3),
                'threshold_boost': threshold_boost,
                'ranking_score': trending_probability  # Used for sorting
            })

            probability_posts.append(probability_post)

        # Sort by trending probability (highest first)
        probability_posts.sort(key=lambda x: x['ranking_score'], reverse=True)

        return probability_posts

    def _sigmoid(self, x: float) -> float:
        """Sigmoid function for smooth probability adjustments."""
        return 1 / (1 + np.exp(-x))

    async def _identify_trending_candidates(self, probability_posts: List[Dict]) -> List[Dict]:
        """Identify posts that meet the trending candidate threshold."""
        trending_candidates = []

        for i, post in enumerate(probability_posts):
            if post['trending_probability'] >= self.trending_threshold:
                candidate = {
                    'rank': i + 1,
                    'post_id': post.get('id', f"post_{i+1}"),
                    'trending_probability': post['trending_probability'],
                    'final_score': post['final_score'],
                    'key_strengths': self._identify_post_strengths(post),
                    'content_preview': post.get('content', '')[:100] + '...' if len(post.get('content', '')) > 100 else post.get('content', ''),
                    'author': post.get('author', 'Unknown')
                }
                trending_candidates.append(candidate)

        return trending_candidates

    def _identify_post_strengths(self, post: Dict) -> List[str]:
        """Identify the key strengths contributing to a post's trending potential."""
        strengths = []

        if post['content_component'] > 25:  # Above average content quality
            strengths.append('Strong Content')
        if post['engagement_component'] > 20:  # Above average engagement
            strengths.append('High Engagement')
        if post['timing_component'] > 15:  # Good timing
            strengths.append('Optimal Timing')
        if post['network_component'] > 10:  # Network influence
            strengths.append('Network Reach')
        if post['strategy_component'] > 8:  # Strategic elements
            strengths.append('Strategic Appeal')

        return strengths[:3]  # Return top 3 strengths

    async def _analyze_influencing_factors(self, probability_posts: List[Dict]) -> List[str]:
        """Analyze which factors are most influential in trending potential."""
        if not probability_posts:
            return ['No data available']

        # Calculate average component scores
        avg_components = {
            'content_quality': statistics.mean([p['content_component'] for p in probability_posts]),
            'engagement': statistics.mean([p['engagement_component'] for p in probability_posts]),
            'timing': statistics.mean([p['timing_component'] for p in probability_posts]),
            'network': statistics.mean([p['network_component'] for p in probability_posts]),
            'strategy': statistics.mean([p['strategy_component'] for p in probability_posts])
        }

        # Sort factors by influence (highest average scores)
        sorted_factors = sorted(avg_components.items(),
                                key=lambda x: x[1], reverse=True)

        # Map factor names to display names
        factor_names = {
            'content_quality': 'Content Quality',
            'engagement': 'Engagement Metrics',
            'timing': 'Optimal Timing',
            'network': 'Network Influence',
            'strategy': 'Strategic Elements'
        }

        # Return top influencing factors
        top_factors = []
        for factor, score in sorted_factors[:3]:
            display_name = factor_names.get(factor, factor.title())
            top_factors.append(f"{display_name} ({score:.1f})")

        return top_factors

    async def _calculate_score_distribution(self, probability_posts: List[Dict]) -> Dict:
        """Calculate distribution statistics for scoring analysis."""
        if not probability_posts:
            return {}

        scores = [post['final_score'] for post in probability_posts]
        probabilities = [post['trending_probability']
                         for post in probability_posts]

        return {
            'score_mean': round(statistics.mean(scores), 1),
            'score_median': round(statistics.median(scores), 1),
            'score_std': round(statistics.stdev(scores) if len(scores) > 1 else 0, 1),
            'score_min': round(min(scores), 1),
            'score_max': round(max(scores), 1),
            'probability_mean': round(statistics.mean(probabilities), 3),
            'high_potential_count': len([p for p in probabilities if p >= 0.7]),
            'trending_candidate_count': len([p for p in probabilities if p >= self.trending_threshold])
        }

    async def _generate_trending_insights(self, probability_posts: List[Dict]) -> List[str]:
        """Generate actionable insights from trending analysis."""
        insights = []

        if not probability_posts:
            return ['No posts analyzed - unable to generate insights']

        trending_count = len(
            [p for p in probability_posts if p['trending_probability'] >= self.trending_threshold])
        high_potential_count = len(
            [p for p in probability_posts if p['trending_probability'] >= 0.7])

        # Insight 1: Overall trending potential
        if trending_count > 0:
            insights.append(
                f"🔥 {trending_count} posts show strong trending potential (≥{self.trending_threshold} probability)")
        else:
            insights.append(
                "📊 No posts currently meet trending threshold - consider content optimization")

        # Insight 2: High potential content
        if high_potential_count > trending_count:
            near_trending = high_potential_count - trending_count
            insights.append(
                f"⚡ {near_trending} additional posts show high potential (≥0.7) - minor optimization could push them to trending")

        # Insight 3: Component analysis
        avg_scores = {
            'content': statistics.mean([p['content_component'] for p in probability_posts]),
            'engagement': statistics.mean([p['engagement_component'] for p in probability_posts]),
            'timing': statistics.mean([p['timing_component'] for p in probability_posts])
        }

        strongest_component = max(avg_scores, key=avg_scores.get)
        weakest_component = min(avg_scores, key=avg_scores.get)

        insights.append(
            f"💪 Strongest factor: {strongest_component.title()} ({avg_scores[strongest_component]:.1f})")
        insights.append(
            f"⚠️ Improvement opportunity: {weakest_component.title()} ({avg_scores[weakest_component]:.1f})")

        return insights

    async def _format_discord_report(self, probability_posts: List[Dict], trending_candidates: List[Dict],
                                     top_factors: List[str], batch_id: str) -> str:
        """Format the comprehensive Discord trending prediction report."""
        if not probability_posts:
            return "🔥 **Trending Prediction Report**\n• No data available for analysis"

        avg_final_score = statistics.mean(
            [p['final_score'] for p in probability_posts])

        # Build Discord message
        discord_message = "🔥 **Trending Prediction Report**\n"
        discord_message += f"• **Avg Final Score:** {avg_final_score:.1f}\n"

        # Trending candidates section
        if trending_candidates:
            discord_message += "• **Trending Candidates:**\n"
            for i, candidate in enumerate(trending_candidates[:3]):  # Top 3
                rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
                post_id = candidate['post_id']
                probability = candidate['trending_probability']
                discord_message += f"   {rank_emoji} Post #{post_id} — {probability:.2f} probability\n"
        else:
            discord_message += "• **Trending Candidates:** None detected (threshold ≥0.8)\n"

        # Top influencing factors
        if top_factors:
            factors_text = " + ".join(top_factors[:2])  # Top 2 factors
            discord_message += f"• **Top Influencing Factors:** {factors_text}\n"

        # Additional insights
        total_posts = len(probability_posts)
        high_potential = len(
            [p for p in probability_posts if p['trending_probability'] >= 0.7])
        discord_message += f"• **Analysis Summary:** {total_posts} posts analyzed, {high_potential} high-potential detected\n"
        discord_message += f"• **Batch ID:** {batch_id}"

        return discord_message

    def _generate_empty_report(self, batch_id: str) -> Dict:
        """Generate report for empty data scenario."""
        return {
            'batch_id': batch_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'posts_analyzed': 0,
            'average_final_score': 0.0,
            'trending_candidates': [],
            'top_influencing_factors': ['No data available'],
            'score_distribution': {},
            'detailed_scores': [],
            'trending_insights': ['No posts provided for analysis'],
            'discord_message': "🔥 **Trending Prediction Report**\n• No data available for analysis"
        }

    def _generate_error_report(self, batch_id: str, error_message: str) -> Dict:
        """Generate report for error scenarios."""
        return {
            'batch_id': batch_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': error_message,
            'posts_analyzed': 0,
            'average_final_score': 0.0,
            'trending_candidates': [],
            'top_influencing_factors': ['Error in analysis'],
            'score_distribution': {},
            'detailed_scores': [],
            'trending_insights': [f'Analysis failed: {error_message}'],
            'discord_message': f"🔥 **Trending Prediction Report**\n• ❌ Analysis Error: {error_message}"
        }


# Standalone function for external usage
async def analyze_trending_potential(posts_data: List[Dict], batch_id: str = None) -> Dict:
    """
    Standalone function to analyze trending potential of posts.

    Args:
        posts_data: List of post dictionaries with metrics
        batch_id: Optional batch identifier

    Returns:
        Trending analysis results dictionary
    """
    agent = TrendingPredictionAgent()
    return await agent.analyze_trending_potential(posts_data, batch_id)


# Configuration and utility functions
def get_trending_config() -> Dict:
    """Get trending prediction system configuration."""
    return {
        'scoring_weights': {
            'content_quality': 0.30,
            'engagement': 0.25,
            'timing': 0.20,
            'network': 0.15,
            'strategy': 0.10
        },
        'trending_threshold': 0.8,
        'high_potential_threshold': 0.7,
        'max_candidates_display': 3,
        'score_ranges': {
            'story_score': (0, 100),
            'engagement_score': (0, 100),
            'velocity': (0, 10),
            'network_influence': (0, 1),
            'timing_score': (0, 100)
        }
    }


def get_trending_metrics() -> Dict:
    """Get trending prediction performance metrics."""
    return {
        'analysis_engine': 'Trending Prediction',
        'version': '1.0.0',
        'features': [
            'Weighted Scoring Rubric',
            'Trending Probability Calculation',
            'Candidate Identification',
            'Influencing Factor Analysis',
            'Discord Rich Reporting'
        ],
        'scoring_components': [
            'Content Quality (30%)',
            'Engagement Metrics (25%)',
            'Timing Optimization (20%)',
            'Network Influence (15%)',
            'Strategic Elements (10%)'
        ],
        'thresholds': {
            'trending_candidate': 0.8,
            'high_potential': 0.7,
            'moderate_potential': 0.5
        }
    }


if __name__ == "__main__":
    # Demo usage
    async def demo():
        print("🔥 Trending Prediction System Demo")
        print("=" * 50)

        # Sample post data
        sample_posts = [
            {
                'id': '584721',
                'content': 'Breaking: Major policy announcement expected today!',
                'story_score': 85,
                'engagement_score': 92,
                'velocity': 8.5,
                'network_influence': 0.75,
                'timing_score': 88,
                'author': 'political_insider'
            },
            {
                'id': '584512',
                'content': 'This new healthcare initiative could change everything',
                'story_score': 78,
                'engagement_score': 84,
                'velocity': 7.2,
                'network_influence': 0.68,
                'timing_score': 82,
                'author': 'health_advocate'
            },
            {
                'id': '584330',
                'content': 'Emotional story about community resilience',
                'story_score': 82,
                'engagement_score': 79,
                'velocity': 6.8,
                'network_influence': 0.71,
                'timing_score': 85,
                'author': 'community_voice'
            }
        ]

        # Run analysis
        result = await analyze_trending_potential(sample_posts, "demo_batch")

        print(f"📊 Analysis Results:")
        print(f"Posts Analyzed: {result['posts_analyzed']}")
        print(f"Average Final Score: {result['average_final_score']}")
        print(f"Trending Candidates: {len(result['trending_candidates'])}")
        print(f"Top Factors: {', '.join(result['top_influencing_factors'])}")
        print("\n📱 Discord Message:")
        print("-" * 40)
        print(result['discord_message'])
        print("-" * 40)

    asyncio.run(demo())
