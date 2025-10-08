# Trending Intelligence Pipeline - Main Orchestrator

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import traceback

# Import all pipeline stages
from .stages.stage_01_data_collection import DataCollectionStage
from .stages.stage_02_data_cleaning import DataCleaningStage
from .stages.stage_03_growth_tracking import GrowthTrackingStage
from .stages.stage_04_score_estimation import ScoreEstimationStage
from .stages.stage_05_rubric_evaluation import RubricEvaluationStage
from .stages.stage_06_strategic_analysis import StrategicAnalysisStage
from .stages.stage_07_predictive_modeling import PredictiveModelingStage
from .stages.stage_08_reporting import ReportingStage
from .stages.stage_09_continuous_learning import ContinuousLearningStage
from .stages.stage_10_meta_analysis import MetaAnalysisStage

logger = logging.getLogger(__name__)


class TrendingIntelligencePipeline:
    """
    Main orchestrator for the 10-stage trending intelligence pipeline.

    This class coordinates the execution of all pipeline stages in sequence:
    1. Data Collection -> 2. Data Cleaning -> 3. Growth Tracking -> 4. Score Estimation
    5. Rubric Evaluation -> 6. Strategic Analysis -> 7. Predictive Modeling -> 8. Reporting
    9. Continuous Learning -> 10. Meta Analysis

    Each stage receives input from the previous stage and outputs structured data
    for the next stage, creating a comprehensive intelligence analysis pipeline.
    """

    def __init__(self, config):
        self.config = config
        self.pipeline_timeout = 30 * 60  # 30 minutes total timeout
        self.stage_timeout = 5 * 60      # 5 minutes per stage timeout

        # Initialize all pipeline stages
        self.stages = {
            1: DataCollectionStage(config),
            2: DataCleaningStage(config),
            3: GrowthTrackingStage(config),
            4: ScoreEstimationStage(config),
            5: RubricEvaluationStage(config),
            6: StrategicAnalysisStage(config),
            7: PredictiveModelingStage(config),
            8: ReportingStage(config),
            9: ContinuousLearningStage(config),
            10: MetaAnalysisStage(config)
        }

        self.stage_names = {
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
        }

    async def execute_full_pipeline(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the complete 10-stage pipeline with comprehensive error handling
        and timeout protection.
        """
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"[START] Starting Trending Intelligence Pipeline - Batch: {batch_id}")

        pipeline_start_time = datetime.now(timezone.utc)
        stage_results = {}
        pipeline_summary = {
            "batch_id": batch_id,
            "started_at": pipeline_start_time.isoformat(),
            "completed_stages": [],
            "failed_stages": [],
            "stage_results": {},
            "total_execution_time": 0,
            "status": "running"
        }

        try:
            # Execute pipeline with overall timeout
            pipeline_results = await asyncio.wait_for(
                self._execute_pipeline_stages(
                    batch_id, stage_results, pipeline_summary),
                timeout=self.pipeline_timeout
            )

            pipeline_end_time = datetime.now(timezone.utc)
            total_execution_time = (
                pipeline_end_time - pipeline_start_time).total_seconds()

            # Update final summary
            pipeline_summary.update({
                "completed_at": pipeline_end_time.isoformat(),
                "total_execution_time": total_execution_time,
                "status": "completed" if len(pipeline_summary["failed_stages"]) == 0 else "completed_with_errors",
                "success_rate": len(pipeline_summary["completed_stages"]) / 10,
                "final_results": pipeline_results
            })

            # Save pipeline summary
            summary_path = await self._save_pipeline_summary(pipeline_summary, batch_id)
            pipeline_summary["summary_path"] = summary_path

            logger.info(f"[SUCCESS] Pipeline completed - Batch: {batch_id}")
            logger.info(
                f"[METRICS] Success rate: {pipeline_summary['success_rate']:.1%}")
            logger.info(
                f"[TIMER]  Total execution time: {total_execution_time:.1f}s")

            return pipeline_summary

        except asyncio.TimeoutError:
            logger.error(
                f"[TIMEOUT] Pipeline timeout after {self.pipeline_timeout}s - Batch: {batch_id}")
            pipeline_summary.update({
                "status": "timeout",
                "error": f"Pipeline exceeded {self.pipeline_timeout}s timeout",
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            return pipeline_summary

        except Exception as e:
            logger.error(f"[ERROR] Pipeline error - Batch: {batch_id}: {e}")
            logger.error(traceback.format_exc())
            pipeline_summary.update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            return pipeline_summary

    async def _execute_pipeline_stages(self, batch_id: str, stage_results: Dict, pipeline_summary: Dict) -> Dict:
        """Execute all pipeline stages in sequence"""

        previous_stage_data = None

        for stage_num in range(1, 11):  # Stages 1-10
            stage_name = self.stage_names[stage_num]
            stage_instance = self.stages[stage_num]

            logger.info(f"[REFRESH] Stage {stage_num}: {stage_name} - Starting...")
            stage_start_time = datetime.now(timezone.utc)

            try:
                # Execute stage with timeout
                stage_result = await asyncio.wait_for(
                    self._execute_single_stage(
                        stage_num,
                        stage_instance,
                        batch_id,
                        previous_stage_data
                    ),
                    timeout=self.stage_timeout
                )

                stage_end_time = datetime.now(timezone.utc)
                execution_time = (
                    stage_end_time - stage_start_time).total_seconds()

                if stage_result:
                    # Stage succeeded
                    stage_results[stage_num] = stage_result
                    pipeline_summary["completed_stages"].append(stage_num)
                    pipeline_summary["stage_results"][stage_num] = {
                        "stage_name": stage_name,
                        "status": "success",
                        "execution_time": execution_time,
                        "result_summary": self._create_stage_summary(stage_result)
                    }

                    # Pass result to next stage
                    previous_stage_data = stage_result

                    logger.info(
                        f"[STAGE] Stage {stage_num}: {stage_name} - Completed ({execution_time:.1f}s)")

                else:
                    # Stage failed but pipeline can continue
                    logger.warning(
                        f"[WARNING] Stage {stage_num}: {stage_name} - Failed but continuing pipeline")
                    pipeline_summary["failed_stages"].append(stage_num)
                    pipeline_summary["stage_results"][stage_num] = {
                        "stage_name": stage_name,
                        "status": "failed",
                        "execution_time": execution_time,
                        "error": "Stage returned None result"
                    }

                    # Continue with previous data or empty dict
                    previous_stage_data = previous_stage_data or {}

            except asyncio.TimeoutError:
                logger.error(
                    f"[TIMEOUT] Stage {stage_num}: {stage_name} - Timeout after {self.stage_timeout}s")
                pipeline_summary["failed_stages"].append(stage_num)
                pipeline_summary["stage_results"][stage_num] = {
                    "stage_name": stage_name,
                    "status": "timeout",
                    "execution_time": self.stage_timeout,
                    "error": f"Stage exceeded {self.stage_timeout}s timeout"
                }

                # Continue with previous data
                previous_stage_data = previous_stage_data or {}

            except Exception as e:
                stage_end_time = datetime.now(timezone.utc)
                execution_time = (
                    stage_end_time - stage_start_time).total_seconds()

                logger.error(
                    f"[ERROR] Stage {stage_num}: {stage_name} - Error: {e}")
                pipeline_summary["failed_stages"].append(stage_num)
                pipeline_summary["stage_results"][stage_num] = {
                    "stage_name": stage_name,
                    "status": "error",
                    "execution_time": execution_time,
                    "error": str(e)
                }

                # Continue with previous data
                previous_stage_data = previous_stage_data or {}

        return stage_results

    async def _execute_single_stage(self, stage_num: int, stage_instance: Any, batch_id: str, previous_data: Any) -> Optional[Dict]:
        """Execute a single pipeline stage with appropriate input parameters"""

        try:
            # Prepare stage-specific inputs
            if stage_num == 1:
                # Stage 1: Data Collection - no input needed
                return await stage_instance.execute(batch_id)

            elif stage_num == 2:
                # Stage 2: Data Cleaning - needs raw data
                raw_data = previous_data or {}
                return await stage_instance.execute(batch_id, raw_data)

            elif stage_num == 3:
                # Stage 3: Growth Tracking - needs clean data
                clean_data = previous_data or {}
                return await stage_instance.execute(batch_id, clean_data)

            elif stage_num == 4:
                # Stage 4: Score Estimation - needs growth data
                growth_data = previous_data or {}
                return await stage_instance.execute(batch_id, growth_data)

            elif stage_num == 5:
                # Stage 5: Rubric Evaluation - needs score data
                score_data = previous_data or {}
                return await stage_instance.execute(batch_id, score_data)

            elif stage_num == 6:
                # Stage 6: Strategic Analysis - needs rubric data
                rubric_data = previous_data or {}
                return await stage_instance.execute(batch_id, rubric_data)

            elif stage_num == 7:
                # Stage 7: Predictive Modeling - needs network data
                network_data = previous_data or {}
                return await stage_instance.execute(batch_id, network_data)

            elif stage_num == 8:
                # Stage 8: Reporting - needs prediction data
                prediction_data = previous_data or {}
                return await stage_instance.execute(batch_id, prediction_data)

            elif stage_num == 9:
                # Stage 9: Continuous Learning - needs report data
                report_data = previous_data or {}
                return await stage_instance.execute(batch_id, report_data)

            elif stage_num == 10:
                # Stage 10: Meta Analysis - needs learning data
                learning_data = previous_data or {}
                return await stage_instance.execute(batch_id, learning_data)

            else:
                logger.error(f"Unknown stage number: {stage_num}")
                return None

        except Exception as e:
            logger.error(f"Error executing stage {stage_num}: {e}")
            return None

    def _create_stage_summary(self, stage_result: Dict) -> Dict:
        """Create a summary of stage results for pipeline tracking"""

        # Extract key metrics from stage result
        summary = {
            "batch_id": stage_result.get("batch_id", "unknown"),
            "status": "success"
        }

        # Add stage-specific summary information
        if "posts_processed" in stage_result:
            summary["posts_processed"] = stage_result["posts_processed"]

        if "trending_posts_count" in stage_result:
            summary["trending_posts"] = stage_result["trending_posts_count"]

        if "accuracy_score" in stage_result:
            summary["accuracy"] = stage_result["accuracy_score"]

        if "weekly_insights" in stage_result:
            summary["insights_count"] = len(stage_result["weekly_insights"])

        # Add output file information
        if "output_path" in stage_result:
            summary["output_file"] = os.path.basename(
                stage_result["output_path"])

        return summary

    async def _save_pipeline_summary(self, summary: Dict, batch_id: str) -> str:
        """Save pipeline execution summary"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/pipeline/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)

        filepath = f"{dir_path}/pipeline_summary_{batch_id}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return filepath

    async def execute_partial_pipeline(self, start_stage: int = 1, end_stage: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Execute a partial pipeline from start_stage to end_stage (inclusive).
        Useful for testing specific stages or resuming from a particular point.
        """
        batch_id = f"partial_{start_stage}_{end_stage}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"[REFRESH] Starting Partial Pipeline (Stages {start_stage}-{end_stage}) - Batch: {batch_id}")

        if start_stage < 1 or end_stage > 10 or start_stage > end_stage:
            raise ValueError(
                "Invalid stage range. Must be 1 <= start_stage <= end_stage <= 10")

        pipeline_start_time = datetime.now(timezone.utc)
        stage_results = {}
        pipeline_summary = {
            "batch_id": batch_id,
            "pipeline_type": "partial",
            "stage_range": f"{start_stage}-{end_stage}",
            "started_at": pipeline_start_time.isoformat(),
            "completed_stages": [],
            "failed_stages": [],
            "stage_results": {},
            "status": "running"
        }

        try:
            previous_stage_data = None

            # If not starting from stage 1, try to load previous data
            if start_stage > 1:
                previous_stage_data = await self._load_previous_stage_data(batch_id, start_stage - 1)

            for stage_num in range(start_stage, end_stage + 1):
                stage_name = self.stage_names[stage_num]
                stage_instance = self.stages[stage_num]

                logger.info(f"[REFRESH] Stage {stage_num}: {stage_name} - Starting...")
                stage_start_time = datetime.now(timezone.utc)

                try:
                    stage_result = await asyncio.wait_for(
                        self._execute_single_stage(
                            stage_num, stage_instance, batch_id, previous_stage_data),
                        timeout=self.stage_timeout
                    )

                    stage_end_time = datetime.now(timezone.utc)
                    execution_time = (
                        stage_end_time - stage_start_time).total_seconds()

                    if stage_result:
                        stage_results[stage_num] = stage_result
                        pipeline_summary["completed_stages"].append(stage_num)
                        pipeline_summary["stage_results"][stage_num] = {
                            "stage_name": stage_name,
                            "status": "success",
                            "execution_time": execution_time,
                            "result_summary": self._create_stage_summary(stage_result)
                        }
                        previous_stage_data = stage_result
                        logger.info(
                            f"[STAGE] Stage {stage_num}: {stage_name} - Completed ({execution_time:.1f}s)")
                    else:
                        logger.warning(
                            f"[WARNING] Stage {stage_num}: {stage_name} - Failed")
                        pipeline_summary["failed_stages"].append(stage_num)
                        pipeline_summary["stage_results"][stage_num] = {
                            "stage_name": stage_name,
                            "status": "failed",
                            "execution_time": execution_time,
                            "error": "Stage returned None result"
                        }

                except Exception as e:
                    stage_end_time = datetime.now(timezone.utc)
                    execution_time = (
                        stage_end_time - stage_start_time).total_seconds()

                    logger.error(
                        f"[ERROR] Stage {stage_num}: {stage_name} - Error: {e}")
                    pipeline_summary["failed_stages"].append(stage_num)
                    pipeline_summary["stage_results"][stage_num] = {
                        "stage_name": stage_name,
                        "status": "error",
                        "execution_time": execution_time,
                        "error": str(e)
                    }

            pipeline_end_time = datetime.now(timezone.utc)
            total_execution_time = (
                pipeline_end_time - pipeline_start_time).total_seconds()

            pipeline_summary.update({
                "completed_at": pipeline_end_time.isoformat(),
                "total_execution_time": total_execution_time,
                "status": "completed" if len(pipeline_summary["failed_stages"]) == 0 else "completed_with_errors",
                "success_rate": len(pipeline_summary["completed_stages"]) / (end_stage - start_stage + 1),
                "final_results": stage_results
            })

            summary_path = await self._save_pipeline_summary(pipeline_summary, batch_id)
            pipeline_summary["summary_path"] = summary_path

            logger.info(
                f"[SUCCESS] Partial Pipeline completed - Batch: {batch_id}")
            logger.info(
                f"[METRICS] Success rate: {pipeline_summary['success_rate']:.1%}")

            return pipeline_summary

        except Exception as e:
            logger.error(
                f"[ERROR] Partial Pipeline error - Batch: {batch_id}: {e}")
            pipeline_summary.update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            return pipeline_summary

    async def _load_previous_stage_data(self, batch_id: str, stage_num: int) -> Optional[Dict]:
        """Load data from a previous stage for partial pipeline execution"""
        # This would load the most recent data from the specified stage
        # For now, return None to indicate no previous data available
        logger.info(
            f"[FOLDER] Attempting to load previous data from stage {stage_num}")
        return None

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline configuration and status"""
        return {
            "pipeline_version": "1.0",
            "total_stages": 10,
            "stage_names": self.stage_names,
            "timeouts": {
                "pipeline_timeout": self.pipeline_timeout,
                "stage_timeout": self.stage_timeout
            },
            "configuration": {
                "stages_initialized": len(self.stages),
                "config_loaded": bool(self.config)
            }
        }

    async def validate_pipeline(self) -> Dict[str, Any]:
        """Validate pipeline configuration and stage readiness"""
        validation_results = {
            "overall_status": "valid",
            "stage_validation": {},
            "issues": [],
            "warnings": []
        }

        # Check each stage
        for stage_num, stage_instance in self.stages.items():
            stage_name = self.stage_names[stage_num]

            try:
                # Basic validation - check if stage has execute method
                if not hasattr(stage_instance, 'execute'):
                    validation_results["issues"].append(
                        f"Stage {stage_num} ({stage_name}) missing execute method")
                    validation_results["stage_validation"][stage_num] = "invalid"
                else:
                    validation_results["stage_validation"][stage_num] = "valid"

            except Exception as e:
                validation_results["issues"].append(
                    f"Stage {stage_num} ({stage_name}) validation error: {e}")
                validation_results["stage_validation"][stage_num] = "error"

        # Check data directories
        required_dirs = ["data/raw", "data/clean", "data/score", "data/rubric",
                         "data/network", "data/predict", "data/report", "config/weights", "data/meta"]

        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                validation_results["warnings"].append(
                    f"Directory {dir_path} does not exist - will be created during execution")

        # Overall status
        if validation_results["issues"]:
            validation_results["overall_status"] = "invalid"
        elif validation_results["warnings"]:
            validation_results["overall_status"] = "valid_with_warnings"

        return validation_results
