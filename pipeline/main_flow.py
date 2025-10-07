"""
Main Intelligence Flow Orchestrator - Seven-Engine Pipeline
Integrates all 7 analysis engines into a sequential workflow with Discord reporting

Execution Order:
1. Data Collection
2. Content Analysis Engine
3. Engagement Intelligence Engine
4. Network Intelligence Engine
5. Temporal Analytics Engine
6. Strategic Intelligence Engine
7. Trending Prediction Engine
8. Meta-Trend Intelligence Engine (Weekly)

Author: AI Assistant
Date: October 7, 2025
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import all 7 analysis engines (classes and functions)
from worker.tasks.content_analysis_task import ContentAnalysisTask
from worker.tasks.engagement_intelligence_task import EngagementIntelligenceTask
from worker.tasks.network_intelligence_task import NetworkIntelligenceTask
from worker.tasks.temporal_analytics_task import TemporalAnalyticsTask
from worker.tasks.strategic_intelligence_task import StrategicIntelligenceTask
from worker.tasks.trending_prediction_task import TrendingPredictionTask
from worker.tasks.meta_trend_intelligence_task import MetaTrendIntelligenceTask

# Import shared utilities
from worker.features.data_collector import collect_trending_data
from notifiers.discord_webhook_sender import DiscordWebhookSender
from notifiers.unified_discord_reporter import UnifiedDiscordReporter, EngineResult
from mock_data_provider import generate_mock_trending_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainFlowOrchestrator:
    """
    Main intelligence flow orchestrator that coordinates all 7 analysis engines
    in a sequential pipeline with comprehensive Discord reporting.
    """

    def __init__(self, unified_reporting: bool = True):
        """Initialize the main flow orchestrator."""
        self.batch_id = None
        self.discord_sender = DiscordWebhookSender()
        self.start_time = None
        self.engine_results = []
        # Use unified Discord reporting instead of individual messages
        self.unified_reporting = unified_reporting

        # Initialize unified reporter if enabled
        if self.unified_reporting:
            self.unified_reporter = UnifiedDiscordReporter()
        else:
            self.unified_reporter = None

        # Engine configuration with Discord formatting
        self.engines = [
            {
                'name': 'Content Analysis',
                'emoji': '🎯',
                'class': ContentAnalysisTask,
                'description': 'Content quality and topic analysis'
            },
            {
                'name': 'Engagement Intelligence',
                'emoji': '📊',
                'class': EngagementIntelligenceTask,
                'description': 'Audience interaction patterns'
            },
            {
                'name': 'Network Intelligence',
                'emoji': '🌐',
                'class': NetworkIntelligenceTask,
                'description': 'Social network influence mapping'
            },
            {
                'name': 'Temporal Analytics',
                'emoji': '⏰',
                'class': TemporalAnalyticsTask,
                'description': 'Time-based performance optimization'
            },
            {
                'name': 'Strategic Intelligence',
                'emoji': '🧭',
                'class': StrategicIntelligenceTask,
                'description': 'Campaign effectiveness analysis'
            },
            {
                'name': 'Trending Prediction',
                'emoji': '🔥',
                'class': TrendingPredictionTask,
                'description': 'Viral content forecasting'
            }
        ]

        # Weekly meta-trend engine (separate scheduling)
        self.meta_engine = {
            'name': 'Meta-Trend Intelligence',
            'emoji': '📅',
            'class': MetaTrendIntelligenceTask,
            'description': 'Weekly cross-engine analysis'
        }

        # Setup data paths
        self.data_path = Path("data")
        self.reports_path = self.data_path / "reports"
        self.logs_path = Path("logs") / "flow"
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

    def generate_batch_id(self) -> str:
        """Generate unique batch ID for this flow execution."""
        return f"main_flow_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    async def collect_data(self) -> Dict:
        """Stage 0: Collect trending data for analysis."""
        logger.info(f"[STAGE 0] 🔄 Data Collection - Batch: {self.batch_id}")

        try:
            # Try to collect real data first (5 pages)
            # Note: collect_trending_data returns a filename, not data directly
            data_filename = collect_trending_data(5)

            if data_filename:
                # Load the data from the saved file
                import json
                from pathlib import Path

                data_file = Path(data_filename)
                if data_file.exists():
                    with open(data_file, 'r', encoding='utf-8') as f:
                        raw_data = json.load(f)

                    posts_count = len(raw_data.get("data", []))
                    logger.info(
                        f"[SUCCESS] Loaded {posts_count} posts from {data_filename}")

                    # Log data collection success (Discord notification in final summary)
                    logger.info(
                        f"✅ Successfully collected {posts_count} posts from API")

                    return raw_data
                else:
                    logger.warning(
                        f"[WARNING] Data file {data_filename} not found")
                    raise FileNotFoundError(
                        f"Data file {data_filename} not found")
            else:
                logger.warning("[WARNING] No data filename returned")
                raise ValueError("No data filename returned from collector")

        except Exception as e:
            logger.error(f"[ERROR] Data collection failed: {str(e)}")
            # Use mock data as fallback
            mock_data = generate_mock_trending_data(20)
            posts_count = len(mock_data.get('data', []))

            # Log fallback usage (Discord notification in final summary)
            logger.warning(
                f"⚠️ Using fallback mock data - API Error: {str(e)[:100]}")

            logger.info(f"[FALLBACK] Using mock data with {posts_count} posts")
            return mock_data

    async def run_main_flow(self) -> Dict:
        """
        Execute the complete 7-engine analysis pipeline with unified Discord reporting.

        Returns:
            Dict containing execution results and summary
        """
        self.batch_id = self.generate_batch_id()
        self.start_time = datetime.now(timezone.utc)

        logger.info("🚀 STARTING MAIN INTELLIGENCE FLOW")
        logger.info("=" * 60)
        logger.info(f"📋 Batch ID: {self.batch_id}")
        logger.info(
            f"🕐 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"🔧 Engines: {len(self.engines)} sequential engines")
        logger.info("=" * 60)

        try:
            # Clear unified reporter for new batch
            if self.unified_reporting:
                self.unified_reporter.clear_results()

            # Log flow start (Discord notification only at completion)
            logger.info(
                "🚀 Intelligence Flow Started - 7-Engine Analysis Pipeline")

            # Stage 0: Data Collection
            batch_data = await self.collect_data()

            # Execute engines sequentially (1-6) and collect results for unified report
            for i, engine in enumerate(self.engines, 1):
                result = await self._run_engine(i, engine, batch_data)
                self.engine_results.append(result)

                # Add result to unified reporter instead of sending individual Discord messages
                if self.unified_reporting and result:
                    engine_result = EngineResult(
                        engine_name=result.get('engine_name', f'Engine {i}'),
                        status="success" if result.get('success') else "error",
                        title=f"{result.get('engine_name', f'Engine {i}')
                                 } Complete",
                        summary=result.get('summary', 'Analysis completed'),
                        execution_time=result.get('execution_time', 0),
                        key_metrics={
                            "data_points": result.get('data_points', 0),
                            "insights_count": result.get('insights_count', 0)
                        },
                        insights=result.get('key_findings', []),
                        recommendations=result.get('recommendations', [])
                    )
                    self.unified_reporter.add_engine_result(engine_result)

                # Small delay between engines for system stability
                await asyncio.sleep(1)

            # Calculate execution summary
            execution_time = (datetime.now(timezone.utc) -
                              self.start_time).total_seconds()
            successful_engines = sum(
                1 for r in self.engine_results if r['success'])

            # Send unified Discord report instead of individual messages
            if self.unified_reporting:
                logger.info("📤 Sending unified Discord report...")
                report_sent = await self.unified_reporter.send_unified_discord_report(self.batch_id)

                if report_sent:
                    logger.info("✅ Unified Discord report sent successfully")
                else:
                    logger.warning("⚠️ Failed to send unified Discord report")
                    # Fallback to basic completion summary
                    await self._send_completion_summary(execution_time, successful_engines)
            else:
                # Send individual completion summary if not using unified reporting
                await self._send_completion_summary(execution_time, successful_engines)

            # Save flow results
            await self._save_flow_results(execution_time)

            logger.info("✅ MAIN INTELLIGENCE FLOW COMPLETED SUCCESSFULLY")
            logger.info(
                f"⏱️ Total Execution Time: {execution_time:.2f} seconds")
            logger.info(
                f"✅ Successful Engines: {successful_engines}/{len(self.engines)}")

            return {
                'status': 'success',
                'batch_id': self.batch_id,
                'execution_time_seconds': execution_time,
                'successful_engines': successful_engines,
                'total_engines': len(self.engines),
                'engine_results': self.engine_results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            error_time = (datetime.now(timezone.utc) -
                          self.start_time).total_seconds()
            logger.error(
                f"❌ MAIN FLOW FAILED after {error_time:.2f}s: {str(e)}")

            # Send error notification
            await self._send_discord_notification(
                "❌ **Flow Error**",
                f"🚨 **Pipeline Failed**\n"
                f"📋 Batch: `{self.batch_id}`\n"
                f"⏱️ Runtime: {error_time:.1f}s\n"
                f"❌ Error: {str(e)}"
            )

            return {
                'status': 'error',
                'batch_id': self.batch_id,
                'error': str(e),
                'execution_time_seconds': error_time,
                'successful_engines': sum(1 for r in self.engine_results if r['success']),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def run_weekly_meta_analysis(self) -> Dict:
        """
        Execute weekly meta-trend intelligence analysis (Engine 7).
        Runs independently on a weekly schedule.
        """
        batch_id = f"meta_weekly_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        try:
            logger.info(
                f"📅 Starting Weekly Meta-Trend Analysis - Batch: {batch_id}")

            # Run meta-trend intelligence
            meta_instance = self.meta_engine['class']()
            result = await meta_instance.run_weekly_intelligence_workflow(batch_id)

            # Format Discord message
            if result.get('status') == 'success':
                total_posts = result.get('total_posts_analyzed', 0)
                emerging_trends = result.get('emerging_trends', 0)

                discord_message = (
                    f"📅 **Weekly Meta-Trend Intelligence**\n"
                    f"✅ Analysis Complete\n"
                    f"📊 Posts Analyzed: **{total_posts}**\n"
                    f"📈 Emerging Trends: **{emerging_trends}**\n"
                    f"🗓️ Calendar Generated: {'✅' if result.get('calendar_generated') else '❌'}\n"
                    f"⏰ Completed: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                )
            else:
                discord_message = (
                    f"📅 **Weekly Meta-Trend Intelligence**\n"
                    f"❌ Analysis Failed\n"
                    f"📋 Batch: `{batch_id}`\n"
                    f"⏰ Attempted: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                )

            if not self.unified_reporting:
                await self._send_discord_notification("📅 **Weekly Meta-Trend**", discord_message)
            else:
                # Add to unified report if available
                if hasattr(self, 'unified_reporter') and self.unified_reporter:
                    engine_result = EngineResult(
                        engine_name="Meta-Trend Intelligence",
                        status="success" if result.get(
                            'status') == 'success' else "error",
                        title="Meta-Trend Intelligence Complete",
                        summary=f"Weekly analysis of {result.get('total_posts_analyzed', 0)} posts",
                        execution_time=result.get('execution_time', 0),
                        key_metrics={
                            "data_points": result.get('total_posts_analyzed', 0),
                            "insights_count": result.get('emerging_trends', 0)
                        },
                        insights=result.get('key_findings', []),
                        recommendations=result.get('recommendations', [])
                    )
                    self.unified_reporter.add_engine_result(engine_result)

            return result

        except Exception as e:
            logger.error(f"❌ Weekly meta-analysis failed: {str(e)}")

            await self._send_discord_notification(
                "❌ **Meta-Trend Error**",
                f"🚨 Weekly analysis failed\n"
                f"📋 Batch: `{batch_id}`\n"
                f"❌ Error: {str(e)}"
            )

            return {
                'status': 'error',
                'batch_id': batch_id,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _run_engine(self, stage_num: int, engine: Dict, batch_data: Dict) -> Dict:
        """Run a single analysis engine with error handling and Discord reporting."""
        engine_start = datetime.now(timezone.utc)
        engine_name = engine['name']

        logger.info(
            f"[STAGE {stage_num}] {engine['emoji']} {engine_name} - Starting...")

        try:
            # Create engine instance and call appropriate workflow method
            engine_instance = engine['class']()

            # Call the appropriate workflow method based on engine type
            # All engines run with send_discord=False for unified reporting
            if engine_name == "Content Analysis":
                result = await engine_instance.run_content_analysis_workflow(
                    data_source=f"data/raw/{self.batch_id[:4]}/{self.batch_id[4:6]}/{self.batch_id[6:8]}/",
                    num_posts=50,
                    send_discord=not self.unified_reporting
                )
            elif engine_name == "Engagement Intelligence":
                result = await engine_instance.run_engagement_analysis_workflow(
                    batch_id=self.batch_id,
                    send_discord=not self.unified_reporting,
                    save_results=True
                )
            elif engine_name == "Network Intelligence":
                result = await engine_instance.run_network_analysis_workflow(
                    batch_id=self.batch_id,
                    send_discord=not self.unified_reporting,
                    save_results=True
                )
            elif engine_name == "Temporal Analytics":
                result = await engine_instance.run_temporal_analysis_workflow(
                    batch_id=self.batch_id,
                    send_discord=not self.unified_reporting
                )
            elif engine_name == "Strategic Intelligence":
                result = await engine_instance.run_strategic_analysis_workflow(
                    batch_id=self.batch_id,
                    send_discord=not self.unified_reporting
                )
            elif engine_name == "Trending Prediction":
                result = await engine_instance.run_trending_prediction_workflow(
                    batch_id=self.batch_id,
                    send_discord=not self.unified_reporting
                )
            else:
                raise ValueError(f"Unknown engine: {engine_name}")

            execution_time = (datetime.now(timezone.utc) -
                              engine_start).total_seconds()

            if result and result.get('status') == 'success':
                logger.info(
                    f"[STAGE {stage_num}] ✅ {engine_name} completed in {execution_time:.2f}s")

                # Store metrics for final summary (no individual Discord messages)
                metrics = self._extract_engine_metrics(result, engine_name)

                return {
                    'stage': stage_num,
                    'engine': engine_name,
                    'success': True,
                    'execution_time': execution_time,
                    'result': result
                }
            else:
                logger.warning(
                    f"[STAGE {stage_num}] ⚠️ {engine_name} returned no results")

                return {
                    'stage': stage_num,
                    'engine': engine_name,
                    'success': False,
                    'execution_time': execution_time,
                    'error': 'No results returned'
                }

        except Exception as e:
            execution_time = (datetime.now(timezone.utc) -
                              engine_start).total_seconds()
            logger.error(
                f"[STAGE {stage_num}] ❌ {engine_name} failed after {execution_time:.2f}s: {str(e)}")

            return {
                'stage': stage_num,
                'engine': engine_name,
                'success': False,
                'execution_time': execution_time,
                'error': str(e)
            }

    def _extract_engine_metrics(self, result: Dict, engine_name: str) -> str:
        """Extract key metrics from engine results for Discord display."""
        try:
            metrics = []

            # Common metrics across engines
            if 'total_posts_analyzed' in result:
                metrics.append(
                    f"📊 Posts: **{result['total_posts_analyzed']}**")

            if 'posts_analyzed' in result:
                metrics.append(f"📊 Posts: **{result['posts_analyzed']}**")

            # Engine-specific metrics
            if engine_name == 'Content Analysis':
                if 'avg_quality_score' in result:
                    metrics.append(
                        f"🎯 Avg Quality: **{result['avg_quality_score']:.1f}/100**")
                if 'top_topics' in result and result['top_topics']:
                    top_topic = result['top_topics'][0] if isinstance(
                        result['top_topics'], list) else "General"
                    metrics.append(f"📝 Top Topic: **{top_topic}**")

            elif engine_name == 'Engagement Intelligence':
                if 'avg_engagement_score' in result:
                    metrics.append(
                        f"📈 Avg Engagement: **{result['avg_engagement_score']:.1f}/100**")
                if 'viral_posts' in result:
                    metrics.append(
                        f"🔥 Viral Posts: **{result['viral_posts']}**")

            elif engine_name == 'Network Intelligence':
                if 'network_strength' in result:
                    metrics.append(
                        f"🌐 Network Strength: **{result['network_strength']:.1f}/100**")
                if 'top_influencers' in result and result['top_influencers']:
                    influencer_count = len(result['top_influencers']) if isinstance(
                        result['top_influencers'], list) else 0
                    metrics.append(f"👑 Influencers: **{influencer_count}**")

            elif engine_name == 'Temporal Analytics':
                if 'optimal_posting_time' in result:
                    metrics.append(
                        f"⏰ Best Time: **{result['optimal_posting_time']}**")
                if 'performance_trend' in result:
                    metrics.append(
                        f"📊 Trend: **{result['performance_trend']}**")

            elif engine_name == 'Strategic Intelligence':
                if 'strategic_score' in result:
                    metrics.append(
                        f"🧭 Strategy Score: **{result['strategic_score']:.1f}/100**")
                if 'campaign_effectiveness' in result:
                    metrics.append(
                        f"🎯 Campaign: **{result['campaign_effectiveness']}**")

            elif engine_name == 'Trending Prediction':
                if 'trending_probability' in result:
                    metrics.append(
                        f"🔥 Trending: **{result['trending_probability']:.1%}**")
                if 'viral_candidates' in result:
                    metrics.append(
                        f"🚀 Viral Candidates: **{result['viral_candidates']}**")

            return '\n'.join(metrics) if metrics else "📊 Analysis completed successfully"

        except Exception as e:
            logger.warning(
                f"Error extracting metrics for {engine_name}: {str(e)}")
            return "📊 Analysis completed"

    async def _send_completion_summary(self, execution_time: float, successful_engines: int):
        """Send final completion summary to Discord."""
        total_engines = len(self.engines)
        success_rate = (successful_engines / total_engines) * 100

        # Choose emoji based on success rate
        if success_rate == 100:
            status_emoji = "🎉"
            status_text = "Perfect Execution"
        elif success_rate >= 80:
            status_emoji = "✅"
            status_text = "Mostly Successful"
        elif success_rate >= 50:
            status_emoji = "⚠️"
            status_text = "Partial Success"
        else:
            status_emoji = "❌"
            status_text = "Multiple Failures"

        # Build detailed results for each engine
        engine_details = []
        for result in self.engine_results:
            if result['success']:
                # Extract key metrics for successful engines
                engine_name = result['engine']
                metrics = self._extract_engine_metrics(
                    result.get('result', {}), engine_name)
                engine_details.append(
                    f"✅ **{engine_name}**: {result['execution_time']:.1f}s\n{metrics}"
                )
            else:
                engine_details.append(
                    f"❌ **{result['engine']}**: {result['execution_time']:.1f}s - {result.get('error', 'Unknown error')}"
                )

        summary_message = (
            f"{status_emoji} **Intelligence Flow Complete**\n"
            f"📊 **{status_text}**\n"
            f"✅ Successful: **{successful_engines}/{total_engines}** engines\n"
            f"📈 Success Rate: **{success_rate:.1f}%**\n"
            f"⏱️ Total Runtime: **{execution_time:.1f}s**\n\n"
            f"📋 **Engine Results:**\n" + "\n\n".join(engine_details) + "\n\n"
            f"🆔 Batch ID: `{self.batch_id}`\n"
            f"⏰ Completed: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
        )

        await self._send_discord_notification("🎉 **Flow Complete**", summary_message)

    async def _send_discord_notification(self, title: str, message: str):
        """Send notification to Discord with error handling."""
        try:
            if self.discord_sender:
                success = await self.discord_sender.send_message(f"**{title}**\n{message}")
                if success:
                    logger.debug(f"Discord notification sent: {title}")
                else:
                    logger.warning(
                        f"Failed to send Discord notification: {title}")
            else:
                logger.warning("Discord sender not available")
        except Exception as e:
            logger.error(f"Error sending Discord notification: {str(e)}")

    async def _save_flow_results(self, execution_time: float):
        """Save complete flow results to JSON file."""
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            results_file = self.reports_path / f"main_flow_{timestamp}.json"

            flow_results = {
                'batch_id': self.batch_id,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'execution_time_seconds': execution_time,
                'total_engines': len(self.engines),
                'successful_engines': sum(1 for r in self.engine_results if r['success']),
                'engine_results': self.engine_results,
                'flow_metadata': {
                    'version': '1.0.0',
                    'orchestrator': 'MainFlowOrchestrator',
                    'engines_executed': [engine['name'] for engine in self.engines]
                }
            }

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(flow_results, f, indent=2,
                          ensure_ascii=False, default=str)

            logger.info(f"💾 Flow results saved to: {results_file}")

        except Exception as e:
            logger.error(f"❌ Error saving flow results: {str(e)}")


# Standalone functions for direct execution
async def run_main_flow() -> Dict:
    """Standalone function to execute the main intelligence flow."""
    orchestrator = MainFlowOrchestrator()
    return await orchestrator.run_main_flow()


async def run_weekly_meta_analysis() -> Dict:
    """Standalone function to execute weekly meta-trend analysis."""
    orchestrator = MainFlowOrchestrator()
    return await orchestrator.run_weekly_meta_analysis()


# Main execution for testing
if __name__ == "__main__":
    async def demo():
        print("🚀 Main Intelligence Flow - Demo Execution")
        print("=" * 60)

        # Run main flow
        result = await run_main_flow()

        print(f"\n📊 Demo Results:")
        print(f"Status: {result.get('status')}")
        print(f"Batch ID: {result.get('batch_id')}")
        print(
            f"Execution Time: {result.get('execution_time_seconds', 0):.1f}s")
        print(
            f"Successful Engines: {result.get('successful_engines', 0)}/{result.get('total_engines', 0)}")

        if result.get('status') == 'success':
            print("✅ Main intelligence flow completed successfully!")
        else:
            print(f"❌ Flow failed: {result.get('error', 'Unknown error')}")

    asyncio.run(demo())
