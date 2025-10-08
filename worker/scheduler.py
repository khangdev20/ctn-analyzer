"""
Enhanced Scheduler with Main Flow Orchestrator Integration
Focuses on main flow pipeline with separated weekly analysis

PRIMARY: Main Flow Orchestrator (every 2 hours)
SECONDARY: Individual engines (TEMPORARILY DISABLED)
WEEKLY: Meta-trend analysis (MOVED TO SEPARATE SCHEDULER)

Author: AI Assistant  
Date: October 8, 2025
Version: 2.1.0 - Weekly Engine Separation
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .features.trending_config import get_config
from .tasks.meta_trend_intelligence_task import get_meta_trend_task_config

logger = logging.getLogger(__name__)


async def run_scheduler_loop(worker):
    """
    Enhanced async scheduler loop with Main Flow Orchestrator focus

    Scheduling Strategy:
    - Main Flow (6 engines sequential): Every 2 hours  
    - Individual engines: TEMPORARILY DISABLED
    - Weekly meta-analysis: MOVED TO SEPARATE SCHEDULER (run_weekly_meta_scheduler.py)
    """
    scheduler = AsyncIOScheduler()

    # Load configuration
    config = get_config()

    logger.info(
        "[LAUNCH] ENHANCED SCHEDULER: Main Flow Orchestrator Focus")
    logger.info("=" * 80)
    logger.info("[TARGET] PRIMARY: Main Flow (6-engine pipeline) - Every 2 hours")
    logger.info("[DISABLED] SECONDARY: Individual engines - Temporarily disabled") 
    logger.info("[SEPARATED] WEEKLY: Meta-trend analysis - Separate scheduler")
    logger.info("=" * 80)

    # === PRIMARY SCHEDULER: Main Flow Orchestrator ===

    # Main Intelligence Flow - Every 2 hours (Complete 7-engine pipeline)
    scheduler.add_job(
        worker._run_main_flow_orchestrator,
        'interval',
        hours=2,
        id='main_intelligence_flow',
        max_instances=1,
        misfire_grace_time=1800,  # 30 minutes grace period
        name='Main Intelligence Flow (7-Engine Pipeline)'
    )
    logger.info("[LAUNCH] Main Intelligence Flow scheduled (2 hour intervals)")

    # === SECONDARY SCHEDULER: Individual Engines ===
    # TEMPORARILY DISABLED - Only using Main Flow (every 2 hours)
    
    # # Content Analysis Engine (every 12 minutes)
    # scheduler.add_job(
    #     worker._run_content_analysis_task,
    #     'interval',
    #     minutes=12,
    #     id='content_analysis_engine',
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     name='Content Analysis Engine (Standalone)'
    # )
    # logger.info("[OK] Content Analysis Engine scheduled (12min intervals)")

    # # Engagement Intelligence Engine (every 18 minutes)
    # scheduler.add_job(
    #     worker._run_engagement_intelligence_task,
    #     'interval',
    #     minutes=18,
    #     id='engagement_intelligence_engine',
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     name='Engagement Intelligence Engine (Standalone)'
    # )
    # logger.info("[OK] Engagement Intelligence Engine scheduled (18min intervals)")

    # # Network Intelligence Engine (every 20 minutes)
    # scheduler.add_job(
    #     worker._run_network_intelligence_task,
    #     'interval',
    #     minutes=20,
    #     id='network_intelligence_engine',
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     name='Network Intelligence Engine (Standalone)'
    # )
    # logger.info("[OK] Network Intelligence Engine scheduled (20min intervals)")

    # # Temporal Analytics Engine (every 22 minutes)
    # scheduler.add_job(
    #     worker._run_temporal_analytics_task,
    #     'interval',
    #     minutes=22,
    #     id='temporal_analytics_engine',
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     name='Temporal Analytics Engine (Standalone)'
    # )
    # logger.info("[OK] Temporal Analytics Engine scheduled (22min intervals)")

    # # Strategic Intelligence Engine (every 25 minutes)
    # scheduler.add_job(
    #     worker._run_strategic_intelligence_task,
    #     'interval',
    #     minutes=25,
    #     id='strategic_intelligence_engine',
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     name='Strategic Intelligence Engine (Standalone)'
    # )
    # logger.info("[OK] Strategic Intelligence Engine scheduled (25min intervals)")

    # # Trending Prediction Engine (every 10 minutes)
    # scheduler.add_job(
    #     worker._run_trending_prediction_task,
    #     'interval',
    #     minutes=10,
    #     id='trending_prediction_engine',
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     name='Trending Prediction Engine (Standalone)'
    # )
    # logger.info("[OK] Trending Prediction Engine scheduled (10min intervals)")
    
    logger.info("[INFO] Individual engines temporarily disabled - using Main Flow only")

    # === WEEKLY SCHEDULER: Meta-Trend Intelligence ===
    # MOVED TO SEPARATE SCHEDULER: run_weekly_meta_scheduler.py
    logger.info("[INFO] Weekly Meta-Trend Intelligence moved to separate scheduler")
    logger.info("[TIMER] Run: python run_weekly_meta_scheduler.py")

    # === BI-DAILY SCHEDULER: Leaderboard Logger ===

    # Leaderboard Bi-Daily Logger (every 12 hours - 09:00 & 21:00 AEST/Brisbane time)
    # Note: AEST = UTC+10, AEDT = UTC+11 (daylight saving)
    # Brisbane doesn't observe daylight saving, so always UTC+10
    scheduler.add_job(
        worker._run_leaderboard_bidaily_task,
        'cron',
        hour='11,23',  # 09:00 & 21:00 AEST = 23:00 & 11:00 UTC (Brisbane = UTC+10)
        minute=0,
        timezone='Australia/Brisbane',  # Let APScheduler handle timezone
        id='leaderboard_bidaily_logger',
        max_instances=1,
        misfire_grace_time=3600,  # 1 hour grace period
        name='Leaderboard Bi-Daily Logger (09:00 & 21:00 AEST)'
    )
    logger.info("[CHAMPION] Leaderboard Bi-Daily Logger scheduled (09:00 & 21:00 AEST - every 12 hours)")

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
    logger.info("[CLEANUP] System cleanup scheduled (30min intervals)")

    # Disk cleanup task (maintenance) - Every 6 hours
    scheduler.add_job(
        worker._disk_cleanup_task,
        'interval',
        hours=6,
        id='disk_cleanup_maintenance',
        max_instances=1,
        name='Disk Cleanup (Storage Management)'
    )
    logger.info("[SAVE] Disk cleanup scheduled (6hr intervals)")

    # === SCHEDULER STARTUP ===

    scheduler.start()

    total_jobs = len(scheduler.get_jobs())
    main_flow_jobs = 1
    individual_engine_jobs = 6
    weekly_jobs = 1
    daily_jobs = 1  # Leaderboard logger
    maintenance_jobs = 2

    logger.info("=" * 80)
    logger.info("[OK] ENHANCED SCHEDULER STARTED SUCCESSFULLY!")
    logger.info(f"[LAUNCH] Main Flow Jobs: {main_flow_jobs}")
    logger.info(f"[FAST] Individual Engine Jobs: {individual_engine_jobs}")
    logger.info(f"[TIMER] Weekly Analysis Jobs: {weekly_jobs}")
    logger.info(f"[CHAMPION] Daily Logger Jobs: {daily_jobs}")
    logger.info(f"[CLEANUP] Maintenance Jobs: {maintenance_jobs}")
    logger.info(f"[ANALYTICS] Total Scheduled Jobs: {total_jobs}")
    logger.info("[TARGET] Multi-mode scheduling: Orchestrated + Individual + Daily logging")
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
