# 🔄 Pipeline Integration - Connect New Pipeline with Existing Worker System

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import new pipeline
from pipeline import TrendingIntelligencePipeline

# Import existing config
from worker.features.trending_config import get_config

logger = logging.getLogger(__name__)


class PipelineIntegration:
    """
    Integration layer to connect the new 10-stage pipeline with the existing
    BackgroundWorker system. This class provides a bridge between the old
    monolithic approach and the new modular pipeline architecture.
    """

    def __init__(self):
        self.config = get_config()
        self.pipeline = TrendingIntelligencePipeline(self.config)

    async def execute_trending_intelligence_task(self, worker=None) -> Dict[str, Any]:
        """
        Main entry point for the trending intelligence task.
        This replaces the existing trending_intelligence_task.py functionality
        with the new 10-stage pipeline architecture.

        This method is designed to be called by the BackgroundWorker scheduler.
        """

        task_id = f"trending_intelligence_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(f"[START] Starting Trending Intelligence Task: {task_id}")
        logger.info("🔄 Using new 10-stage modular pipeline architecture")

        # Update worker task tracking if worker is provided
        if worker:
            worker.task_count += 1
            worker.active_tasks.append(task_id)

        try:
            # Execute the full 10-stage pipeline
            pipeline_result = await self.pipeline.execute_full_pipeline()

            # Extract results for backward compatibility
            task_result = await self._format_task_result(pipeline_result, task_id)

            logger.info(
                f"[SUCCESS] Trending Intelligence Task completed: {task_id}")
            logger.info(
                f"[METRICS] Pipeline success rate: {pipeline_result.get('success_rate', 0):.1%}")

            return task_result

        except Exception as e:
            logger.error(
                f"[ERROR] Trending Intelligence Task failed: {task_id} - {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }

        finally:
            # Clean up worker task tracking
            if worker and task_id in worker.active_tasks:
                worker.active_tasks.remove(task_id)

    async def _format_task_result(self, pipeline_result: Dict, task_id: str) -> Dict[str, Any]:
        """
        Format pipeline results for backward compatibility with existing
        worker system expectations.
        """

        # Extract key metrics from pipeline stages
        stage_results = pipeline_result.get("stage_results", {})
        final_results = pipeline_result.get("final_results", {})

        # Get reporting stage results for Discord notifications
        reporting_results = final_results.get(8, {})  # Stage 8: Reporting
        meta_results = final_results.get(10, {})      # Stage 10: Meta Analysis

        # Format for existing Discord notification system
        task_result = {
            "task_id": task_id,
            "batch_id": pipeline_result.get("batch_id", task_id),
            "status": pipeline_result.get("status", "unknown"),
            "started_at": pipeline_result.get("started_at"),
            "completed_at": pipeline_result.get("completed_at"),
            "execution_time": pipeline_result.get("total_execution_time", 0),

            # Pipeline-specific metrics
            "pipeline_metrics": {
                "total_stages": 10,
                "completed_stages": len(pipeline_result.get("completed_stages", [])),
                "failed_stages": len(pipeline_result.get("failed_stages", [])),
                "success_rate": pipeline_result.get("success_rate", 0)
            },

            # Stage summaries
            "stage_summaries": {
                stage_num: result.get("result_summary", {})
                for stage_num, result in stage_results.items()
            },

            # Discord notification data
            "discord_data": self._extract_discord_data(reporting_results, meta_results),

            # Legacy compatibility fields
            "posts_processed": self._get_posts_processed_count(stage_results),
            "trending_posts": self._get_trending_posts_count(stage_results),
            "insights_generated": self._get_insights_count(meta_results)
        }

        return task_result

    def _extract_discord_data(self, reporting_results: Dict, meta_results: Dict) -> Dict:
        """Extract data formatted for Discord notifications"""

        discord_data = {
            "has_embed": False,
            "has_strategic_analysis": False,
            "summary_text": "Trending intelligence analysis completed"
        }

        # Extract Discord embed from reporting stage
        if reporting_results and "discord_embed" in reporting_results:
            discord_data["embed"] = reporting_results["discord_embed"]
            discord_data["has_embed"] = True

        # Extract strategic analysis text
        if reporting_results and "strategic_analysis" in reporting_results:
            discord_data["strategic_analysis"] = reporting_results["strategic_analysis"]
            discord_data["has_strategic_analysis"] = True

        # Extract weekly insights from meta analysis
        if meta_results and "weekly_insights" in meta_results:
            insights = meta_results["weekly_insights"]
            if insights:
                discord_data["weekly_insights"] = insights
                discord_data["summary_text"] = f"Generated {len(insights)} strategic insights"

        return discord_data

    def _get_posts_processed_count(self, stage_results: Dict) -> int:
        """Extract total posts processed across all stages"""

        # Check data collection stage (Stage 1)
        if 1 in stage_results:
            summary = stage_results[1].get("result_summary", {})
            return summary.get("posts_processed", 0)

        return 0

    def _get_trending_posts_count(self, stage_results: Dict) -> int:
        """Extract trending posts count from pipeline stages"""

        # Check rubric evaluation stage (Stage 5) or prediction stage (Stage 7)
        for stage_num in [7, 5, 4]:  # Try prediction, rubric, then score stages
            if stage_num in stage_results:
                summary = stage_results[stage_num].get("result_summary", {})
                if "trending_posts" in summary:
                    return summary["trending_posts"]

        return 0

    def _get_insights_count(self, meta_results: Dict) -> int:
        """Extract insights count from meta analysis stage"""

        if meta_results and "insights_count" in meta_results:
            return meta_results["insights_count"]

        return 0

    async def execute_partial_pipeline(self, start_stage: int = 1, end_stage: int = 10) -> Dict[str, Any]:
        """
        Execute a partial pipeline for testing or debugging purposes.
        This can be useful for development and troubleshooting specific stages.
        """

        task_id = f"partial_pipeline_{start_stage}_{end_stage}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"🔄 Starting Partial Pipeline (Stages {start_stage}-{end_stage}): {task_id}")

        try:
            pipeline_result = await self.pipeline.execute_partial_pipeline(start_stage, end_stage)
            task_result = await self._format_task_result(pipeline_result, task_id)

            logger.info(f"[SUCCESS] Partial Pipeline completed: {task_id}")
            return task_result

        except Exception as e:
            logger.error(f"[ERROR] Partial Pipeline failed: {task_id} - {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }

    async def validate_pipeline_setup(self) -> Dict[str, Any]:
        """
        Validate that the pipeline is properly configured and ready to run.
        This should be called during system startup.
        """

        logger.info("[VALIDATE] Validating pipeline setup...")

        try:
            # Validate pipeline configuration
            validation_result = await self.pipeline.validate_pipeline()

            # Check pipeline status
            status_result = await self.pipeline.get_pipeline_status()

            combined_result = {
                "validation": validation_result,
                "status": status_result,
                "integration_status": "ready" if validation_result["overall_status"] == "valid" else "issues_detected",
                "checked_at": datetime.now(timezone.utc).isoformat()
            }

            if validation_result["overall_status"] == "valid":
                logger.info(
                    "[SUCCESS] Pipeline validation successful - system ready")
            else:
                logger.warning(
                    f"[WARNING] Pipeline validation issues detected: {len(validation_result['issues'])} issues")

            return combined_result

        except Exception as e:
            logger.error(f"[ERROR] Pipeline validation failed: {e}")
            return {
                "validation": {"overall_status": "error", "error": str(e)},
                "integration_status": "error",
                "checked_at": datetime.now(timezone.utc).isoformat()
            }

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """
        Get pipeline metrics for monitoring and debugging.
        This provides information about the current pipeline configuration.
        """

        return {
            "pipeline_version": "1.0.0",
            "architecture": "10-stage modular pipeline",
            "stages": {
                1: "Data Collection",
                2: "Data Cleaning",
                3: "Growth Tracking",
                4: "Score Estimation",
                5: "Rubric Evaluation",
                6: "Strategic Analysis",
                7: "Predictive Modeling",
                8: "Reporting",
                9: "Continuous Learning",
                10: "Meta Analysis"
            },
            "config_loaded": bool(self.config),
            "pipeline_initialized": bool(self.pipeline),
            "integration_ready": True
        }


# Create global instance for easy import
pipeline_integration = PipelineIntegration()


# Convenience functions for existing worker integration
async def run_trending_intelligence_task(worker=None) -> Dict[str, Any]:
    """
    Convenience function to maintain compatibility with existing scheduler setup.
    This function can be imported and used as a drop-in replacement for the
    existing trending intelligence task.
    """
    return await pipeline_integration.execute_trending_intelligence_task(worker)


async def validate_system_setup() -> Dict[str, Any]:
    """
    Convenience function for system validation during startup.
    """
    return await pipeline_integration.validate_pipeline_setup()


async def run_partial_pipeline(start_stage: int = 1, end_stage: int = 10) -> Dict[str, Any]:
    """
    Convenience function for running partial pipeline during development/testing.
    """
    return await pipeline_integration.execute_partial_pipeline(start_stage, end_stage)
