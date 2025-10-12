"""
Hourly Content Analysis + Leaderboard Scheduler
Simplified scheduler with only essential tasks

ACTIVE TASKS:
- Latest Posts Content Analysis: Every 1 hour
- Trending Posts Content Analysis: Every 1 hour (30min offset)  
- Leaderboard Updates: Every 1 hour

Author: AI Assistant  
Date: October 12, 2025
Version: 3.0.0 - Simplified Hourly Focus
"""

import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


async def run_scheduler_loop(worker):
    """
    Simplified hourly scheduler for content analysis and leaderboard

    Active Tasks:
    - Latest Posts Analysis: Every 1 hour at :00
    - Trending Posts Analysis: Every 1 hour at :30  
    - Leaderboard Updates: Every 1 hour
    """
    scheduler = AsyncIOScheduler()

    # Using fixed hourly intervals for simplified setup
    logger.info("[CONFIG] Using fixed 1-hour intervals for all tasks")

    # Fixed hourly intervals for all tasks
    leaderboard_hours = 1

    logger.info(
        "[SCHEDULER] Starting Content Analysis (Latest + Trending) + Leaderboard System")
    logger.info("[CONTENT] Latest & Trending reports every 1 hour each")
    logger.info(f"[LEADERBOARD] Every {leaderboard_hours} hour(s)")

    # === PRIMARY SCHEDULER: Content Analysis + Leaderboard ===

    # Content Analysis - Latest Posts (Every Hour)
    scheduler.add_job(
        worker._run_content_analysis_latest_task,
        'interval',
        hours=1,
        id='content_analysis_latest',
        max_instances=1,
        misfire_grace_time=300,
        name='Content Analysis - Latest Posts (Every Hour)'
    )
    logger.info("[CONTENT] Latest posts scheduled (1h intervals)")

    # Content Analysis - Trending Posts (Every Hour, offset by 30min)
    offset_time = datetime.now() + timedelta(minutes=30)

    scheduler.add_job(
        worker._run_content_analysis_trending_task,
        'interval',
        hours=1,
        id='content_analysis_trending',
        max_instances=1,
        misfire_grace_time=300,
        name='Content Analysis - Trending Posts (Every Hour, 30min offset)',
        next_run_time=offset_time  # Start 30 minutes after latest posts
    )
    logger.info(
        "[CONTENT] Trending posts scheduled (1h intervals, 30min offset)")

    # Leaderboard Updates (Every Hour)
    scheduler.add_job(
        worker._run_leaderboard_bidaily_task,
        'interval',
        hours=leaderboard_hours,
        id='leaderboard_hourly',
        max_instances=1,
        misfire_grace_time=900,  # 15 minutes grace period
        name=f'Leaderboard Updates (Every {leaderboard_hours} hour(s))'
    )
    logger.info(f"[LEADERBOARD] Scheduled ({leaderboard_hours}h intervals)")

    scheduler.start()

    logger.info(
        "[OK] Hourly Scheduler started - Latest + Trending + Leaderboard active")
    logger.info("[TIMING] Latest: :00, Trending: :30, optimal spacing")

    try:
        while worker.is_running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("[STOP] Scheduler stopped")
    finally:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass  # Ignore shutdown errors
