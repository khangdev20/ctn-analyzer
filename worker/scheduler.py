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

logger = logging.getLogger(__name__)

# Import dynamic scheduler config
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.scheduler_config import get_scheduler_config
except ImportError as e:
    logger.warning(f"Could not import scheduler config: {e}")
    get_scheduler_config = None


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

    # Load dynamic scheduler configuration
    scheduler_config = None
    if get_scheduler_config:
        try:
            scheduler_config = get_scheduler_config()
            logger.info("[CONFIG] Using dynamic scheduler intervals")
        except Exception as e:
            logger.warning(
                f"[CONFIG] Failed to load dynamic config: {e}, using hardcoded intervals")

    # Get intervals from config or use defaults
    content_analysis_minutes = 12
    trending_prediction_minutes = 10
    leaderboard_hours = 1

    if scheduler_config:
        content_analysis_minutes = scheduler_config.get_interval(
            'content_analysis') or 12
        trending_prediction_minutes = scheduler_config.get_interval(
            'trending_prediction') or 10
        leaderboard_hours = scheduler_config.get_interval('leaderboard') or 1

    logger.info(
        "[LAUNCH] DYNAMIC SCHEDULER: Content Analysis + Trending Prediction + Leaderboard")
    logger.info("=" * 80)
    logger.info(
        f"[ACTIVE] Content Analysis Engine - Every {content_analysis_minutes} minutes (Latest Posts)")
    logger.info(
        f"[ACTIVE] Trending Prediction Engine - Every {trending_prediction_minutes} minutes")
    logger.info(
        f"[ACTIVE] Leaderboard Logger - Every {leaderboard_hours} hour(s) (DYNAMIC)")
    logger.info(
        "[DISABLED] Main Flow, Debate Strategy, Maintenance - Temporarily disabled")
    logger.info("=" * 80)

    # === PRIMARY SCHEDULER: Main Flow Orchestrator ===
    # TEMPORARILY DISABLED - Only using individual engines

    # # Main Intelligence Flow - Every 2 hours (Complete 7-engine pipeline)
    # scheduler.add_job(
    #     worker._run_main_flow_orchestrator,
    #     'interval',
    #     hours=2,
    #     id='main_intelligence_flow',
    #     max_instances=1,
    #     misfire_grace_time=1800,  # 30 minutes grace period
    #     name='Main Intelligence Flow (7-Engine Pipeline)'
    # )
    # logger.info("[LAUNCH] Main Intelligence Flow scheduled (2 hour intervals)")

    # === SECONDARY SCHEDULER: Individual Engines ===
    # ENABLED - Only Content Analysis

    # Content Analysis Engine (dynamic interval)
    scheduler.add_job(
        worker._run_content_analysis_task,
        'interval',
        minutes=content_analysis_minutes,
        id='content_analysis_engine',
        max_instances=1,
        misfire_grace_time=300,
        name=f'Content Analysis Engine (Every {content_analysis_minutes}min)'
    )
    logger.info(
        f"[OK] Content Analysis Engine scheduled ({content_analysis_minutes}min intervals)")

    # Trending Prediction Engine (dynamic interval)
    scheduler.add_job(
        worker._run_trending_prediction_task,
        'interval',
        minutes=trending_prediction_minutes,
        id='trending_prediction_engine',
        max_instances=1,
        misfire_grace_time=300,
        name=f'Trending Prediction Engine (Every {trending_prediction_minutes}min)'
    )
    logger.info(
        f"[OK] Trending Prediction Engine scheduled ({trending_prediction_minutes}min intervals)")

    logger.info(
        "[INFO] Other engines temporarily disabled - using Content Analysis + Trending Prediction only")

    # === WEEKLY SCHEDULER: Meta-Trend Intelligence ===
    # MOVED TO SEPARATE SCHEDULER: run_weekly_meta_scheduler.py
    logger.info(
        "[INFO] Weekly Meta-Trend Intelligence moved to separate scheduler")
    logger.info("[TIMER] Run: python run_weekly_meta_scheduler.py")

    # === HOURLY SCHEDULER: Leaderboard Logger (TEST MODE) ===

    # Leaderboard Logger (dynamic interval)
    scheduler.add_job(
        worker._run_leaderboard_bidaily_task,
        'interval',
        hours=leaderboard_hours,
        id='leaderboard_dynamic_logger',
        max_instances=1,
        misfire_grace_time=900,  # 15 minutes grace period
        name=f'Leaderboard Logger (Every {leaderboard_hours} hour(s) - DYNAMIC)'
    )
    logger.info(
        f"[DYNAMIC] Leaderboard Logger scheduled ({leaderboard_hours} hour intervals - API configurable)")

    # === DEBATE STRATEGY SCHEDULER ===
    # TEMPORARILY DISABLED

    # # Debate Strategy Monitor - Every 2 hours
    # scheduler.add_job(
    #     worker._run_debate_strategy_task,
    #     'interval',
    #     hours=2,
    #     id='debate_strategy_monitor',
    #     max_instances=1,
    #     misfire_grace_time=1800,  # 30 minutes grace period
    #     name='Debate Strategy Monitor (Competition AI Agent)'
    # )
    # logger.info("[🎯] Debate Strategy Monitor scheduled (2 hour intervals)")

    # === MAINTENANCE SCHEDULER ===
    # TEMPORARILY DISABLED

    # # Cleanup task (maintenance)
    # scheduler.add_job(
    #     worker._cleanup_stuck_jobs,
    #     'interval',
    #     minutes=30,
    #     id='cleanup_maintenance',
    #     max_instances=1,
    #     name='System Cleanup (Maintenance)'
    # )
    # logger.info("[CLEANUP] System cleanup scheduled (30min intervals)")

    # # Disk cleanup task (maintenance) - Every 6 hours
    # scheduler.add_job(
    #     worker._disk_cleanup_task,
    #     'interval',
    #     hours=6,
    #     id='disk_cleanup_maintenance',
    #     max_instances=1,
    #     name='Disk Cleanup (Storage Management)'
    # )
    logger.info("[SAVE] Disk cleanup scheduled (6hr intervals)")

    # === SCHEDULER STARTUP ===

    scheduler.start()

    total_jobs = len(scheduler.get_jobs())
    main_flow_jobs = 1
    individual_engine_jobs = 6
    weekly_jobs = 1
    daily_jobs = 1  # Leaderboard logger
    debate_jobs = 1  # Debate strategy monitor
    maintenance_jobs = 2

    logger.info("=" * 80)
    logger.info("[OK] FOCUSED SCHEDULER STARTED SUCCESSFULLY!")
    logger.info(f"[ACTIVE] Content Analysis Jobs: 1 (Latest Posts)")
    logger.info(f"[ACTIVE] Trending Prediction Jobs: 1")
    logger.info(f"[ACTIVE] Leaderboard Logger Jobs: 1 (TEST MODE)")
    logger.info(f"[DISABLED] Main Flow Jobs: 0 (temporarily disabled)")
    logger.info(f"[DISABLED] Debate Strategy Jobs: 0 (temporarily disabled)")
    logger.info(f"[DISABLED] Maintenance Jobs: 0 (temporarily disabled)")
    logger.info(f"[ANALYTICS] Total Active Jobs: 3")
    logger.info(
        f"[DYNAMIC MODE] Content Analysis ({content_analysis_minutes}min) + Trending Prediction ({trending_prediction_minutes}min) + Leaderboard ({leaderboard_hours}h) - API CONFIGURABLE")
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
