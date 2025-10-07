"""
Enhanced Scheduler with Main Flow Orchestrator Integration
Combines orchestrated 7-engine pipeline with individual engine scheduling

PRIMARY: Main Flow Orchestrator (every 15 minutes)
SECONDARY: Individual engines (specialized intervals)
WEEKLY: Meta-trend analysis (Sundays 2 AM UTC)

Author: AI Assistant  
Date: October 7, 2025
Version: 2.0.0 - Main Flow Integration
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .features.trending_config import get_config
from .tasks.meta_trend_intelligence_task import get_meta_trend_task_config

logger = logging.getLogger(__name__)


async def run_scheduler_loop(worker):
    """
    Enhanced async scheduler loop with Main Flow Orchestrator + individual engines

    Scheduling Strategy:
    - Main Flow (all 7 engines sequential): Every 15 minutes
    - Individual engines: Specialized intervals for targeted analysis
    - Weekly meta-analysis: Comprehensive weekly reports
    """
    scheduler = AsyncIOScheduler()

    # Load configuration
    config = get_config()

    logger.info(
        "🚀 ENHANCED SCHEDULER: Main Flow Orchestrator + Individual Engines")
    logger.info("=" * 80)
    logger.info("🎯 PRIMARY: Main Flow (7-engine pipeline) - Every 15 minutes")
    logger.info("⚡ SECONDARY: Individual engines - Specialized intervals")
    logger.info("📅 WEEKLY: Meta-trend analysis - Sundays 2 AM UTC")
    logger.info("=" * 80)

    # === PRIMARY SCHEDULER: Main Flow Orchestrator ===

    # Main Intelligence Flow - Every 15 minutes (Complete 7-engine pipeline)
    scheduler.add_job(
        worker._run_main_flow_orchestrator,
        'interval',
        minutes=15,
        id='main_intelligence_flow',
        max_instances=1,
        misfire_grace_time=600,  # 10 minutes grace period
        name='Main Intelligence Flow (7-Engine Pipeline)'
    )
    logger.info("🚀 Main Intelligence Flow scheduled (15min intervals)")

    # === SECONDARY SCHEDULER: Individual Engines ===

    # Content Analysis Engine (every 12 minutes)
    scheduler.add_job(
        worker._run_content_analysis_task,
        'interval',
        minutes=12,
        id='content_analysis_engine',
        max_instances=1,
        misfire_grace_time=300,
        name='Content Analysis Engine (Standalone)'
    )
    logger.info("✅ Content Analysis Engine scheduled (12min intervals)")

    # Engagement Intelligence Engine (every 18 minutes)
    scheduler.add_job(
        worker._run_engagement_intelligence_task,
        'interval',
        minutes=18,
        id='engagement_intelligence_engine',
        max_instances=1,
        misfire_grace_time=300,
        name='Engagement Intelligence Engine (Standalone)'
    )
    logger.info("✅ Engagement Intelligence Engine scheduled (18min intervals)")

    # Network Intelligence Engine (every 20 minutes)
    scheduler.add_job(
        worker._run_network_intelligence_task,
        'interval',
        minutes=20,
        id='network_intelligence_engine',
        max_instances=1,
        misfire_grace_time=300,
        name='Network Intelligence Engine (Standalone)'
    )
    logger.info("✅ Network Intelligence Engine scheduled (20min intervals)")

    # Temporal Analytics Engine (every 22 minutes)
    scheduler.add_job(
        worker._run_temporal_analytics_task,
        'interval',
        minutes=22,
        id='temporal_analytics_engine',
        max_instances=1,
        misfire_grace_time=300,
        name='Temporal Analytics Engine (Standalone)'
    )
    logger.info("✅ Temporal Analytics Engine scheduled (22min intervals)")

    # Strategic Intelligence Engine (every 25 minutes)
    scheduler.add_job(
        worker._run_strategic_intelligence_task,
        'interval',
        minutes=25,
        id='strategic_intelligence_engine',
        max_instances=1,
        misfire_grace_time=300,
        name='Strategic Intelligence Engine (Standalone)'
    )
    logger.info("✅ Strategic Intelligence Engine scheduled (25min intervals)")

    # Trending Prediction Engine (every 10 minutes)
    scheduler.add_job(
        worker._run_trending_prediction_task,
        'interval',
        minutes=10,
        id='trending_prediction_engine',
        max_instances=1,
        misfire_grace_time=300,
        name='Trending Prediction Engine (Standalone)'
    )
    logger.info("✅ Trending Prediction Engine scheduled (10min intervals)")

    # === WEEKLY SCHEDULER: Meta-Trend Intelligence ===

    # Meta-Trend Intelligence Engine (weekly - every Sunday at 2 AM UTC)
    meta_config = get_meta_trend_task_config()
    scheduler.add_job(
        worker._run_meta_trend_intelligence_task,
        'cron',
        day_of_week=meta_config['schedule']['day_of_week'],
        hour=meta_config['schedule']['hour'],
        minute=meta_config['schedule']['minute'],
        id='meta_trend_intelligence_engine',
        max_instances=1,
        misfire_grace_time=meta_config['schedule']['misfire_grace_time'],
        name='Meta-Trend Intelligence Engine (Weekly)'
    )
    logger.info(
        "📅 Meta-Trend Intelligence Engine scheduled (Weekly: Sunday 2 AM UTC)")

    # === MAINTENANCE SCHEDULER ===

    # Cleanup task (maintenance)
    scheduler.add_job(
        worker._cleanup_stuck_jobs,
        'interval',
        minutes=30,
        id='cleanup_maintenance',
        max_instances=1,
        name='System Cleanup (Maintenance)'
    )
    logger.info("🧹 System cleanup scheduled (30min intervals)")

    # === SCHEDULER STARTUP ===

    scheduler.start()

    total_jobs = len(scheduler.get_jobs())
    main_flow_jobs = 1
    individual_engine_jobs = 6
    weekly_jobs = 1
    maintenance_jobs = 1

    logger.info("=" * 80)
    logger.info("✅ ENHANCED SCHEDULER STARTED SUCCESSFULLY!")
    logger.info(f"🚀 Main Flow Jobs: {main_flow_jobs}")
    logger.info(f"⚡ Individual Engine Jobs: {individual_engine_jobs}")
    logger.info(f"📅 Weekly Analysis Jobs: {weekly_jobs}")
    logger.info(f"🧹 Maintenance Jobs: {maintenance_jobs}")
    logger.info(f"📊 Total Scheduled Jobs: {total_jobs}")
    logger.info("🎯 Dual-mode scheduling: Orchestrated + Individual execution")
    logger.info("=" * 80)

    try:
        while worker.is_running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("[CANCELLED] Enhanced scheduler loop cancelled")
    finally:
        try:
            scheduler.shutdown(wait=False)
            logger.info("[SHUTDOWN] Enhanced scheduler shutdown complete")
        except Exception as e:
            logger.debug(f"Scheduler shutdown error (ignored): {e}")
