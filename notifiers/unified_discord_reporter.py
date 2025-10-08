"""
Unified Discord Report System - Tổng hợp tất cả engine results thành một tin nhắn đẹp mắt

Thay vì gửi nhiều tin nhắn rời rạc từ từng engine, hệ thống này tổng hợp tất cả
thông tin thành một comprehensive report với format professional.

Author: AI Assistant
Date: October 7, 2025
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Import notification system
try:
    from notifiers.discord_webhook_sender import DiscordWebhookSender
except ImportError:
    DiscordWebhookSender = None

logger = logging.getLogger(__name__)


@dataclass
class EngineResult:
    """Structure for individual engine results"""
    engine_name: str
    status: str  # "success", "error", "warning"
    title: str
    summary: str
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time: float = 0.0
    error_message: str = ""


class UnifiedDiscordReporter:
    """
    Unified Discord reporting system that collects results from all engines
    and sends a single, well-formatted comprehensive report
    """

    def __init__(self):
        self.discord_sender = DiscordWebhookSender() if DiscordWebhookSender else None
        self.engine_results: List[EngineResult] = []
        self.batch_id = ""
        self.start_time = datetime.now(timezone.utc)

    def clear_results(self):
        """Clear previous results for new batch"""
        self.engine_results.clear()
        self.start_time = datetime.now(timezone.utc)

    def add_engine_result(self, result: EngineResult):
        """Add result from an individual engine"""
        self.engine_results.append(result)
        logger.debug(
            f"[NOTE] Added result from {result.engine_name}: {result.status}")

    def add_engine_result_dict(self, engine_name: str, result_data: Dict):
        """Add engine result from dictionary format"""
        try:
            # Extract common fields from various result formats
            status = result_data.get("status", "unknown")
            if "error" in result_data:
                status = "error"
            elif status in ["completed", "success", True]:
                status = "success"
            elif status in ["failed", "error", False]:
                status = "error"
            else:
                status = "warning"

            # Create structured result
            engine_result = EngineResult(
                engine_name=engine_name,
                status=status,
                title=result_data.get("title", f"{engine_name} Analysis"),
                summary=result_data.get("summary", result_data.get(
                    "description", "Analysis completed")),
                key_metrics=result_data.get(
                    "metrics", result_data.get("key_metrics", {})),
                insights=result_data.get(
                    "insights", result_data.get("analysis", [])),
                recommendations=result_data.get("recommendations", []),
                execution_time=result_data.get("execution_time", 0.0),
                error_message=result_data.get("error", "")
            )

            self.add_engine_result(engine_result)

        except Exception as e:
            logger.error(f"Failed to add result for {engine_name}: {e}")

            # Add error result
            error_result = EngineResult(
                engine_name=engine_name,
                status="error",
                title=f"{engine_name} - Processing Error",
                summary="Failed to process engine result",
                error_message=str(e)
            )
            self.add_engine_result(error_result)

    async def generate_unified_report(self, batch_id: str = None) -> Dict:
        """Generate comprehensive unified report from all engine results"""

        if batch_id:
            self.batch_id = batch_id
        elif not self.batch_id:
            self.batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        total_time = (datetime.now(timezone.utc) -
                      self.start_time).total_seconds()

        # Analyze results
        total_engines = len(self.engine_results)
        successful_engines = len(
            [r for r in self.engine_results if r.status == "success"])
        failed_engines = len(
            [r for r in self.engine_results if r.status == "error"])
        warning_engines = len(
            [r for r in self.engine_results if r.status == "warning"])

        # Overall status
        if failed_engines == 0:
            overall_status = "success" if warning_engines == 0 else "warning"
        elif successful_engines > failed_engines:
            overall_status = "partial"
        else:
            overall_status = "error"

        # Build comprehensive report
        report = {
            "batch_id": self.batch_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "execution_summary": {
                "total_engines": total_engines,
                "successful": successful_engines,
                "failed": failed_engines,
                "warnings": warning_engines,
                "total_execution_time": total_time
            },
            "engine_results": self.engine_results,
            "key_insights": self._extract_key_insights(),
            "top_recommendations": self._extract_top_recommendations(),
            "performance_metrics": self._calculate_performance_metrics()
        }

        return report

    def _extract_key_insights(self) -> List[str]:
        """Extract top insights from all engines"""
        all_insights = []

        for result in self.engine_results:
            if result.status == "success" and result.insights:
                # Add engine prefix to insights
                engine_insights = [f"**{result.engine_name}**: {insight}"
                                   # Top 2 per engine
                                   for insight in result.insights[:2]]
                all_insights.extend(engine_insights)

        return all_insights[:8]  # Top 8 insights overall

    def _extract_top_recommendations(self) -> List[str]:
        """Extract top recommendations from all engines"""
        all_recommendations = []

        for result in self.engine_results:
            if result.status == "success" and result.recommendations:
                # Add engine prefix to recommendations
                engine_recs = [f"**{result.engine_name}**: {rec}"
                               # Top 2 per engine
                               for rec in result.recommendations[:2]]
                all_recommendations.extend(engine_recs)

        return all_recommendations[:6]  # Top 6 recommendations overall

    def _calculate_performance_metrics(self) -> Dict:
        """Calculate aggregated performance metrics"""
        total_metrics = {}

        for result in self.engine_results:
            if result.status == "success" and result.key_metrics:
                for key, value in result.key_metrics.items():
                    if isinstance(value, (int, float)):
                        if key not in total_metrics:
                            total_metrics[key] = []
                        total_metrics[key].append(value)

        # Calculate aggregates
        aggregated_metrics = {}
        for key, values in total_metrics.items():
            if values:
                aggregated_metrics[key] = {
                    "avg": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                }

        return aggregated_metrics

    async def send_unified_discord_report(self, batch_id: str = None) -> bool:
        """Send comprehensive unified report to Discord"""

        if not self.discord_sender:
            logger.warning("Discord sender not available")
            return False

        if not self.engine_results:
            logger.warning("No engine results to report")
            return False

        try:
            # Generate comprehensive report
            report = await self.generate_unified_report(batch_id)

            # Create Discord embed
            embed_data = await self._create_discord_embed(report)

            # Send to Discord
            success = await self.discord_sender.send_rich_embed(**embed_data)

            if success:
                logger.info(
                    f"[OK] Unified Discord report sent successfully for batch {self.batch_id}")
            else:
                logger.error(
                    f"[ERROR] Failed to send unified Discord report for batch {self.batch_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to send unified Discord report: {e}")
            return False

    async def _create_discord_embed(self, report: Dict) -> Dict:
        """Create professional Discord embed from report data"""

        overall_status = report["overall_status"]
        execution_summary = report["execution_summary"]

        # Status emoji and colors
        status_config = {
            "success": {"emoji": "[OK]", "color": 0x00ff00, "title_suffix": "All Systems Operational"},
            "warning": {"emoji": "[WARNING]", "color": 0xff9900, "title_suffix": "Minor Issues Detected"},
            "partial": {"emoji": "🔶", "color": 0xff6600, "title_suffix": "Partial Success"},
            "error": {"emoji": "[ERROR]", "color": 0xff0000, "title_suffix": "Critical Issues"}
        }

        config = status_config.get(overall_status, status_config["warning"])

        # Main title and description
        title = f"{config['emoji']} Trending Intelligence Report - {config['title_suffix']}"

        description = f"""
**Batch ID**: `{report['batch_id']}`
**Execution Time**: {execution_summary['total_execution_time']:.1f}s
**Engines**: {execution_summary['successful']}/{execution_summary['total_engines']} successful
"""

        # Build fields
        fields = []

        # 1. Engine Status Overview
        engine_status_value = ""
        for result in report["engine_results"]:
            status_emoji = "[OK]" if result.status == "success" else "[ERROR]" if result.status == "error" else "[WARNING]"
            engine_status_value += f"{status_emoji} **{result.engine_name}** ({result.execution_time:.1f}s)\n"

        fields.append({
            "name": "[TOOLS] Engine Status",
            "value": engine_status_value[:1024] if engine_status_value else "No engines executed",
            "inline": True
        })

        # 2. Performance Metrics
        if report["performance_metrics"]:
            metrics_value = ""
            # Top 3 metrics
            for metric, data in list(report["performance_metrics"].items())[:3]:
                metrics_value += f"**{metric.title()}**: {data['avg']:.1f} (avg)\n"

            fields.append({
                "name": "[ANALYTICS] Key Metrics",
                "value": metrics_value or "No metrics available",
                "inline": True
            })

        # 3. Top Insights
        if report["key_insights"]:
            insights_value = ""
            # Top 4 insights
            for i, insight in enumerate(report["key_insights"][:4], 1):
                insights_value += f"{i}. {insight[:100]}...\n" if len(
                    insight) > 100 else f"{i}. {insight}\n"

            fields.append({
                "name": "[IDEA] Key Insights",
                "value": insights_value[:1024],
                "inline": False
            })

        # 4. Top Recommendations
        if report["top_recommendations"]:
            recs_value = ""
            # Top 4 recommendations
            for i, rec in enumerate(report["top_recommendations"][:4], 1):
                recs_value += f"{i}. {rec[:100]}...\n" if len(
                    rec) > 100 else f"{i}. {rec}\n"

            fields.append({
                "name": "[TARGET] Recommendations",
                "value": recs_value[:1024],
                "inline": False
            })

        # 5. Detailed Engine Results (if errors)
        if execution_summary["failed"] > 0:
            error_details = ""
            for result in report["engine_results"]:
                if result.status == "error":
                    error_details += f"**{result.engine_name}**: {result.error_message[:50]}...\n"

            if error_details:
                fields.append({
                    "name": "[ERROR] Error Details",
                    "value": error_details[:1024],
                    "inline": False
                })

        # Footer
        footer = {
            "text": f"Trending Intelligence System • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "icon_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }

        return {
            "title": title,
            "description": description,
            "color": config["color"],
            "fields": fields,
            "footer": footer,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_status_summary(self) -> str:
        """Get quick status summary for logging"""
        if not self.engine_results:
            return "No results available"

        total = len(self.engine_results)
        successful = len(
            [r for r in self.engine_results if r.status == "success"])

        return f"{successful}/{total} engines successful"


# Global unified reporter instance
_unified_reporter = None


def get_unified_reporter() -> UnifiedDiscordReporter:
    """Get or create global unified reporter instance"""
    global _unified_reporter

    if not _unified_reporter:
        _unified_reporter = UnifiedDiscordReporter()

    return _unified_reporter


async def add_engine_result(engine_name: str, result_data: Dict):
    """Convenience function to add engine result to unified reporter"""
    reporter = get_unified_reporter()
    reporter.add_engine_result_dict(engine_name, result_data)
    logger.debug(f"[NOTE] Added {engine_name} result to unified reporter")


async def send_unified_report(batch_id: str = None) -> bool:
    """Convenience function to send unified report"""
    reporter = get_unified_reporter()
    success = await reporter.send_unified_discord_report(batch_id)

    # Clear results after sending
    reporter.clear_results()

    return success


async def clear_reporter():
    """Clear unified reporter for new batch"""
    reporter = get_unified_reporter()
    reporter.clear_results()


if __name__ == "__main__":
    # Test unified reporter
    async def test_unified_reporter():
        print("[TEST] Testing Unified Discord Reporter...")

        reporter = UnifiedDiscordReporter()

        # Add mock engine results
        test_results = [
            {
                "engine": "Content Analysis",
                "data": {
                    "status": "success",
                    "summary": "Analyzed 150 trending posts with high engagement patterns",
                    "metrics": {"avg_engagement": 85.5, "viral_score": 92.3},
                    "insights": ["Visual content performs 3x better", "Peak posting time: 2-4 PM"],
                    "recommendations": ["Increase visual content ratio", "Schedule posts at optimal times"]
                }
            },
            {
                "engine": "Engagement Intelligence",
                "data": {
                    "status": "success",
                    "summary": "Identified optimal engagement strategies",
                    "metrics": {"response_rate": 67.8, "interaction_quality": 78.2},
                    "insights": ["Question-based posts drive 2x engagement", "Community responses increase retention"],
                    "recommendations": ["Use more interactive formats", "Respond promptly to comments"]
                }
            },
            {
                "engine": "Trend Prediction",
                "data": {
                    "status": "warning",
                    "summary": "Partial analysis due to API limits",
                    "metrics": {"prediction_confidence": 72.1},
                    "insights": ["Emerging trend: Sustainability content"],
                    "recommendations": ["Monitor sustainability hashtags"]
                }
            }
        ]

        # Add results to reporter
        for result in test_results:
            reporter.add_engine_result_dict(result["engine"], result["data"])

        # Generate report
        report = await reporter.generate_unified_report("test_batch_123")

        print(f"Report generated: {report['overall_status']}")
        print(f"Engines: {report['execution_summary']}")
        print(f"Insights: {len(report['key_insights'])}")
        print(f"Recommendations: {len(report['top_recommendations'])}")

        # Test Discord embed creation
        embed_data = await reporter._create_discord_embed(report)
        print(f"Discord embed created: {embed_data['title']}")

        print("[OK] Unified reporter test completed!")

    asyncio.run(test_unified_reporter())
