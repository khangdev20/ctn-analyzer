"""
Meta-Trend Intelligence Task - Weekly Analysis Workflow

This module integrates the Meta-Trend Intelligence system into the main worker architecture,
providing automated weekly analysis with 7-day data aggregation and Discord notifications.

Features:
- 7-day data collection from all analysis engines
- Comprehensive trend and pattern analysis
- Strategic posting calendar generation
- Discord notifications with weekly intelligence summaries
- Structured weekly report persistence

Author: AI Assistant
Date: October 7, 2025
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Import meta-trend intelligence engine
from worker.features.meta_trend_intelligence import MetaTrendIntelligenceAgent, analyze_weekly_intelligence

# Import notification system
try:
    from notifiers.discord_webhook_sender import DiscordWebhookSender
except ImportError:
    DiscordWebhookSender = None
    logging.warning("Discord webhook sender not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetaTrendIntelligenceTask:
    """
    Meta-trend intelligence task workflow for weekly analysis automation.

    This class orchestrates the complete weekly intelligence workflow including:
    - 7-day data aggregation from all analysis engines
    - Comprehensive pattern and trend analysis
    - Strategic posting calendar generation
    - Discord notification with weekly summaries
    - Structured report persistence and archiving
    """

    def __init__(self):
        """Initialize the meta-trend intelligence task."""
        self.agent = MetaTrendIntelligenceAgent()
        self.discord_sender = DiscordWebhookSender() if DiscordWebhookSender else None

        # Configuration
        self.analysis_engines = [
            'content_analysis',
            'engagement_intelligence',
            'network_intelligence',
            'temporal_analytics',
            'strategic_intelligence',
            'trending_prediction'
        ]

        # Data paths
        self.base_data_path = Path("data")
        self.reports_path = self.base_data_path / "reports" / "meta_trend_intelligence"
        self.weekly_archives_path = self.reports_path / "weekly_archives"
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.weekly_archives_path.mkdir(parents=True, exist_ok=True)

    async def run_weekly_intelligence_workflow(self, batch_id: str = None) -> Dict:
        """
        Execute complete weekly meta-trend intelligence workflow.

        Args:
            batch_id: Optional batch identifier for tracking

        Returns:
            Dictionary containing workflow results and weekly analysis
        """
        if not batch_id:
            batch_id = f"weekly_meta_trend_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"📆 Starting weekly meta-trend intelligence workflow for batch {batch_id}")

        try:
            # Step 1: Validate analysis timing (should run weekly)
            if not await self._should_run_weekly_analysis():
                logger.info(
                    "⏭️ Weekly analysis already completed recently, skipping...")
                return {
                    'status': 'skipped',
                    'batch_id': batch_id,
                    'reason': 'Recent analysis already exists',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            # Step 2: Run comprehensive weekly intelligence analysis
            intelligence_results = await self.agent.analyze_weekly_intelligence(batch_id)

            if not intelligence_results or intelligence_results.get('total_posts', 0) == 0:
                logger.warning("No data available for weekly analysis")
                return {
                    'status': 'no_data',
                    'batch_id': batch_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            logger.info(
                f"📊 Completed weekly analysis of {intelligence_results.get('total_posts', 0)} posts")

            # Step 3: Save comprehensive weekly analysis results
            await self._save_weekly_analysis_results(intelligence_results, batch_id)

            # Step 4: Generate and save strategic recommendations
            strategic_recommendations = await self._generate_strategic_recommendations(intelligence_results)
            await self._save_strategic_recommendations(strategic_recommendations, batch_id)

            # Step 5: Send Discord notification with weekly summary
            discord_success = await self._send_weekly_discord_notification(intelligence_results)

            # Step 6: Archive previous week's data
            await self._archive_previous_week_data()

            # Step 7: Generate comprehensive workflow summary
            workflow_results = {
                'status': 'success',
                'batch_id': batch_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis_period': intelligence_results.get('analysis_period', {}),
                'total_posts_analyzed': intelligence_results.get('total_posts', 0),
                'top_tags_identified': len(intelligence_results.get('consistent_patterns', {}).get('top_tags', [])),
                'emerging_trends': len(intelligence_results.get('trend_analysis', {}).get('emerging_trends', [])),
                'calendar_generated': bool(intelligence_results.get('calendar_recommendations')),
                'discord_notification': discord_success,
                'intelligence_results': intelligence_results,
                'strategic_recommendations': strategic_recommendations,
                'workflow_insights': await self._generate_workflow_insights(intelligence_results)
            }

            logger.info(
                f"✅ Weekly meta-trend intelligence workflow completed successfully")
            return workflow_results

        except Exception as e:
            logger.error(
                f"❌ Error in weekly meta-trend intelligence workflow: {str(e)}")
            return {
                'status': 'error',
                'batch_id': batch_id,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _should_run_weekly_analysis(self) -> bool:
        """Check if weekly analysis should run based on last execution time."""
        try:
            # Check for recent weekly analysis files
            cutoff_time = datetime.now(
                timezone.utc) - timedelta(days=6)  # Allow some overlap

            recent_files = []
            if self.reports_path.exists():
                for file_path in self.reports_path.rglob("weekly_intelligence_*.json"):
                    if file_path.stat().st_mtime > cutoff_time.timestamp():
                        recent_files.append(file_path)

            # If no recent files, should run
            if not recent_files:
                return True

            # Check if the most recent file is older than 5 days
            most_recent = max(recent_files, key=lambda f: f.stat().st_mtime)
            file_age_hours = (datetime.now(
                timezone.utc).timestamp() - most_recent.stat().st_mtime) / 3600

            return file_age_hours > 120  # Run if last analysis was more than 5 days ago

        except Exception as e:
            logger.warning(f"Error checking analysis timing: {str(e)}")
            return True  # Default to running if check fails

    async def _save_weekly_analysis_results(self, analysis_results: Dict, batch_id: str):
        """Save comprehensive weekly analysis results with structured organization."""
        try:
            # Create timestamped directory for this week's analysis
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            week_dir = self.reports_path / f"week_{timestamp}"
            week_dir.mkdir(parents=True, exist_ok=True)

            # Save main weekly intelligence analysis
            main_analysis_file = week_dir / "weekly_intelligence_analysis.json"
            with open(main_analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2,
                          ensure_ascii=False, default=str)

            # Save consistent patterns separately for easy access
            if analysis_results.get('consistent_patterns'):
                patterns_file = week_dir / "consistent_patterns.json"
                with open(patterns_file, 'w', encoding='utf-8') as f:
                    json.dump(
                        analysis_results['consistent_patterns'], f, indent=2, ensure_ascii=False)

            # Save trend analysis separately
            if analysis_results.get('trend_analysis'):
                trends_file = week_dir / "trend_analysis.json"
                with open(trends_file, 'w', encoding='utf-8') as f:
                    json.dump(
                        analysis_results['trend_analysis'], f, indent=2, ensure_ascii=False)

            # Save calendar recommendations
            if analysis_results.get('calendar_recommendations'):
                calendar_file = week_dir / "posting_calendar.json"
                with open(calendar_file, 'w', encoding='utf-8') as f:
                    json.dump(
                        analysis_results['calendar_recommendations'], f, indent=2, ensure_ascii=False)

            # Save Discord message for reference
            discord_file = week_dir / "discord_message.txt"
            with open(discord_file, 'w', encoding='utf-8') as f:
                f.write(analysis_results.get(
                    'discord_message', 'No Discord message generated'))

            # Create weekly summary file
            summary_file = week_dir / "weekly_summary.json"
            weekly_summary = {
                'batch_id': batch_id,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_posts': analysis_results.get('total_posts', 0),
                'analysis_period': analysis_results.get('analysis_period', {}),
                'key_metrics': {
                    'top_tags_count': len(analysis_results.get('consistent_patterns', {}).get('top_tags', [])),
                    'consistent_authors_count': len(analysis_results.get('consistent_patterns', {}).get('consistent_authors', [])),
                    'emerging_trends_count': len(analysis_results.get('trend_analysis', {}).get('emerging_trends', [])),
                    'fading_trends_count': len(analysis_results.get('trend_analysis', {}).get('fading_trends', []))
                },
                'file_locations': {
                    'main_analysis': str(main_analysis_file),
                    'patterns': str(patterns_file) if analysis_results.get('consistent_patterns') else None,
                    'trends': str(trends_file) if analysis_results.get('trend_analysis') else None,
                    'calendar': str(calendar_file) if analysis_results.get('calendar_recommendations') else None
                }
            }

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(weekly_summary, f, indent=2,
                          ensure_ascii=False, default=str)

            logger.info(f"💾 Weekly analysis results saved to {week_dir}")

        except Exception as e:
            logger.error(f"❌ Error saving weekly analysis results: {str(e)}")

    async def _generate_strategic_recommendations(self, analysis_results: Dict) -> Dict:
        """Generate strategic recommendations based on weekly analysis."""
        recommendations = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'content_strategy': [],
            'timing_strategy': [],
            'hashtag_strategy': [],
            'author_strategy': [],
            'trend_strategy': []
        }

        try:
            # Content strategy recommendations
            performance_metrics = analysis_results.get(
                'performance_metrics', {})
            if performance_metrics:
                viral_rate = performance_metrics.get(
                    'performance_distribution', {}).get('viral', 0)
                total_posts = analysis_results.get('total_posts', 1)

                if viral_rate / total_posts < 0.1:  # Less than 10% viral rate
                    recommendations['content_strategy'].append(
                        "📈 Increase viral content production - current viral rate below optimal threshold"
                    )

                avg_engagement = performance_metrics.get(
                    'avg_engagement_score', 0)
                if avg_engagement < 60:
                    recommendations['content_strategy'].append(
                        "🎯 Focus on engagement optimization - current average below performance target"
                    )

            # Timing strategy recommendations
            calendar = analysis_results.get('calendar_recommendations', {})
            if calendar.get('weekly_schedule'):
                best_times = []
                for day, config in calendar['weekly_schedule'].items():
                    if config.get('expected_performance', 0) > 70:
                        best_times.append(
                            f"{day} at {config['recommended_time']}")

                if best_times:
                    recommendations['timing_strategy'].append(
                        f"⏰ Prioritize posting during high-performance windows: {', '.join(best_times[:3])}"
                    )

            # Hashtag strategy recommendations
            patterns = analysis_results.get('consistent_patterns', {})
            if patterns.get('top_tags'):
                top_tags = [tag['tag'] for tag in patterns['top_tags'][:3]]
                recommendations['hashtag_strategy'].append(
                    f"🏷️ Continue leveraging high-performing tags: {', '.join(top_tags)}"
                )

            # Trend strategy recommendations
            trends = analysis_results.get('trend_analysis', {})
            if trends.get('emerging_trends'):
                emerging = trends['emerging_trends'][0]
                recommendations['trend_strategy'].append(
                    f"📈 Capitalize on emerging trend: {emerging['tag']} shows {emerging['growth_percentage']} growth"
                )

            if trends.get('fading_trends'):
                fading = trends['fading_trends'][0]
                recommendations['trend_strategy'].append(
                    f"📉 Reduce focus on declining trend: {fading['tag']} showing {fading['decline_percentage']} decline"
                )

            # Author strategy recommendations
            if patterns.get('consistent_authors'):
                top_author = patterns['consistent_authors'][0]
                recommendations['author_strategy'].append(
                    f"👤 Maintain collaboration with top performer: @{top_author['author']} (avg {top_author['avg_engagement']} engagement)"
                )

        except Exception as e:
            logger.error(
                f"Error generating strategic recommendations: {str(e)}")

        return recommendations

    async def _save_strategic_recommendations(self, recommendations: Dict, batch_id: str):
        """Save strategic recommendations to dedicated file."""
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            recommendations_file = self.reports_path / \
                f"strategic_recommendations_{timestamp}.json"

            with open(recommendations_file, 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, indent=2,
                          ensure_ascii=False, default=str)

            logger.info(
                f"📋 Strategic recommendations saved to {recommendations_file}")

        except Exception as e:
            logger.error(f"❌ Error saving strategic recommendations: {str(e)}")

    async def _send_weekly_discord_notification(self, analysis_results: Dict) -> bool:
        """Send Discord notification with weekly intelligence summary."""
        if not self.discord_sender:
            logger.warning(
                "Discord sender not available, skipping notification")
            return False

        try:
            discord_message = analysis_results.get(
                'discord_message', 'Weekly intelligence analysis completed')

            # Try to send as rich embed
            try:
                success = await self.discord_sender.send_rich_embed(
                    title="📆 Weekly Intelligence Summary",
                    description=discord_message,
                    color=0x7B68EE,  # Medium slate blue for weekly reports
                    fields=[
                        {
                            "name": "📊 Analysis Overview",
                            "value": f"Posts: {analysis_results.get('total_posts', 0)}\nPeriod: 7 days\nEngines: 6 analysis systems",
                            "inline": True
                        },
                        {
                            "name": "🏷️ Pattern Analysis",
                            "value": f"Tags: {len(analysis_results.get('consistent_patterns', {}).get('top_tags', []))}\nAuthors: {len(analysis_results.get('consistent_patterns', {}).get('consistent_authors', []))}",
                            "inline": True
                        },
                        {
                            "name": "📈 Trend Analysis",
                            "value": f"Emerging: {len(analysis_results.get('trend_analysis', {}).get('emerging_trends', []))}\nFading: {len(analysis_results.get('trend_analysis', {}).get('fading_trends', []))}",
                            "inline": True
                        }
                    ]
                )

                if success:
                    logger.info(
                        "✅ Weekly Discord notification sent successfully")
                    return True

            except Exception as e:
                logger.warning(
                    f"Rich embed failed, trying simple message: {str(e)}")

            # Fallback to simple message
            success = await self.discord_sender.send_message(discord_message)
            if success:
                logger.info(
                    "✅ Weekly Discord notification sent (simple format)")
            return success

        except Exception as e:
            logger.error(
                f"❌ Error sending weekly Discord notification: {str(e)}")
            return False

    async def _archive_previous_week_data(self):
        """Archive data from previous weeks to maintain organization."""
        try:
            # Archive data older than 2 weeks
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)

            archived_count = 0
            if self.reports_path.exists():
                for item in self.reports_path.iterdir():
                    if item.is_dir() and item.name.startswith('week_'):
                        if item.stat().st_mtime < cutoff_date.timestamp():
                            # Move to archives
                            archive_dest = self.weekly_archives_path / item.name
                            if not archive_dest.exists():
                                item.rename(archive_dest)
                                archived_count += 1

            if archived_count > 0:
                logger.info(
                    f"📦 Archived {archived_count} previous week directories")

        except Exception as e:
            logger.warning(f"Error archiving previous week data: {str(e)}")

    async def _generate_workflow_insights(self, analysis_results: Dict) -> List[str]:
        """Generate workflow-specific insights and performance metrics."""
        insights = []

        try:
            total_posts = analysis_results.get('total_posts', 0)
            analysis_period = analysis_results.get('analysis_period', {})

            # Data collection insights
            insights.append(
                f"📊 Analyzed {total_posts} posts across {analysis_period.get('days_analyzed', 7)} days")

            # Pattern insights
            patterns = analysis_results.get('consistent_patterns', {})
            if patterns.get('top_tags'):
                tag_count = len(patterns['top_tags'])
                insights.append(
                    f"🏷️ Identified {tag_count} consistent hashtag patterns")

            if patterns.get('consistent_authors'):
                author_count = len(patterns['consistent_authors'])
                insights.append(
                    f"👥 Tracked {author_count} consistent content creators")

            # Trend insights
            trends = analysis_results.get('trend_analysis', {})
            emerging_count = len(trends.get('emerging_trends', []))
            fading_count = len(trends.get('fading_trends', []))

            if emerging_count > 0:
                insights.append(
                    f"📈 Detected {emerging_count} emerging trends for strategic focus")

            if fading_count > 0:
                insights.append(
                    f"📉 Identified {fading_count} declining trends to deprioritize")

            # Calendar insights
            calendar = analysis_results.get('calendar_recommendations', {})
            if calendar.get('weekly_schedule'):
                schedule_count = len(calendar['weekly_schedule'])
                insights.append(
                    f"🗓️ Generated {schedule_count}-day strategic posting calendar")

            # Performance insights
            strategic_insights = analysis_results.get('strategic_insights', [])
            if strategic_insights:
                insights.append(
                    f"💡 Provided {len(strategic_insights)} strategic recommendations")

            return insights

        except Exception as e:
            logger.error(f"Error generating workflow insights: {str(e)}")
            return ['Weekly analysis workflow completed successfully']


# Standalone task execution function
async def run_weekly_meta_trend_task(batch_id: str = None) -> Dict:
    """
    Standalone function to execute weekly meta-trend intelligence task.

    Args:
        batch_id: Optional batch identifier for tracking

    Returns:
        Dictionary containing task execution results
    """
    task = MetaTrendIntelligenceTask()
    return await task.run_weekly_intelligence_workflow(batch_id)


# Task configuration and scheduling utilities
def get_meta_trend_task_config() -> Dict:
    """Get meta-trend intelligence task configuration for scheduler integration."""
    return {
        'task_name': 'meta_trend_intelligence',
        'function': run_weekly_meta_trend_task,
        'schedule': {
            'trigger': 'cron',
            'day_of_week': 'sunday',  # Run every Sunday
            'hour': 2,                # At 2 AM UTC
            'minute': 0,
            'misfire_grace_time': 3600  # 1 hour grace period
        },
        'description': 'Weekly Meta-Trend Intelligence - 7-day pattern and trend analysis',
        'dependencies': [
            'content_analysis',
            'engagement_intelligence',
            'network_intelligence',
            'temporal_analytics',
            'strategic_intelligence',
            'trending_prediction'
        ],
        'outputs': [
            'weekly_intelligence_summary',
            'consistent_patterns',
            'trend_analysis',
            'posting_calendar',
            'strategic_recommendations'
        ]
    }


if __name__ == "__main__":
    # Demo execution
    async def demo():
        print("📆 Meta-Trend Intelligence Task Demo")
        print("=" * 50)

        task = MetaTrendIntelligenceTask()
        result = await task.run_weekly_intelligence_workflow("demo_weekly_meta_trend")

        print(f"📊 Task Results:")
        print(f"Status: {result.get('status')}")
        print(f"Posts Analyzed: {result.get('total_posts_analyzed', 0)}")
        print(f"Top Tags: {result.get('top_tags_identified', 0)}")
        print(f"Emerging Trends: {result.get('emerging_trends', 0)}")
        print(f"Calendar Generated: {result.get('calendar_generated', False)}")
        print(
            f"Discord Notification: {result.get('discord_notification', False)}")

        if result.get('workflow_insights'):
            print("\n💡 Workflow Insights:")
            for insight in result['workflow_insights']:
                print(f"  • {insight}")

    asyncio.run(demo())
