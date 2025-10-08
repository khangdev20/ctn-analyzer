#!/usr/bin/env python3
"""
Weekly Meta-Trend Intelligence Scheduler
Separate scheduler for weekly meta-trend analysis

This scheduler runs independently from the main flow and executes:
- Meta-trend analysis every Sunday at 2 AM UTC
- Weekly cross-engine intelligence synthesis
- Comprehensive weekly reports and insights

Usage:
    python run_weekly_meta_scheduler.py

Author: AI Assistant
Date: October 8, 2025
Version: 1.0.0
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from worker.tasks.meta_trend_intelligence_task import MetaTrendIntelligenceTask
from worker.features.trending_config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/weekly_meta_scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class WeeklyMetaScheduler:
    """Dedicated scheduler for weekly meta-trend intelligence."""

    def __init__(self):
        """Initialize the weekly meta scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.meta_task = MetaTrendIntelligenceTask()
        self.is_running = False

    async def run_weekly_meta_analysis(self):
        """Execute weekly meta-trend analysis."""
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            batch_id = f"weekly_meta_{timestamp}"
            
            logger.info("📅 STARTING WEEKLY META-TREND ANALYSIS")
            logger.info("=" * 60)
            logger.info(f"🆔 Batch ID: {batch_id}")
            logger.info(f"⏰ Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            logger.info("🔍 Analysis Type: Cross-engine weekly intelligence synthesis")
            logger.info("=" * 60)

            # Execute meta-trend analysis workflow
            result = await self.meta_task.run_weekly_intelligence_workflow(batch_id)

            if result and result.get('success'):
                logger.info("✅ WEEKLY META-TREND ANALYSIS COMPLETED SUCCESSFULLY")
                logger.info(f"📊 Posts Analyzed: {result.get('posts_analyzed', 0)}")
                logger.info(f"🔮 Analysis Results: Generated successfully") 
                logger.info(f"📈 Batch ID: {result.get('batch_id', batch_id)}")
                
                # Send Discord notification manually since we removed send_discord parameter
                await self._send_discord_notification(result, batch_id)
                
                return True
            else:
                logger.error("❌ WEEKLY META-TREND ANALYSIS FAILED")
                logger.error(f"Error: {result.get('error', 'Unknown error') if result else 'No result returned'}")
                return False

        except Exception as e:
            logger.error(f"💥 WEEKLY META-TREND ANALYSIS EXCEPTION: {str(e)}", exc_info=True)
            return False

    def setup_weekly_schedule(self):
        """Setup weekly scheduling for meta-trend analysis."""
        try:
            # Schedule for every Sunday at 2:00 AM UTC
            self.scheduler.add_job(
                self.run_weekly_meta_analysis,
                'cron',
                day_of_week='sun',  # Sunday
                hour=2,             # 2 AM UTC
                minute=0,           # Exactly at 2:00
                timezone='UTC',
                id='weekly_meta_trend_analysis',
                max_instances=1,
                misfire_grace_time=3600,  # 1 hour grace period
                name='Weekly Meta-Trend Intelligence Analysis'
            )

            logger.info("📅 WEEKLY META-TREND SCHEDULER CONFIGURED")
            logger.info("⏰ Schedule: Every Sunday at 2:00 AM UTC")
            logger.info("🎯 Next Run: " + str(self.scheduler.get_job('weekly_meta_trend_analysis').next_run_time))
            
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup weekly schedule: {str(e)}")
            return False

    async def start_scheduler(self):
        """Start the weekly meta-trend scheduler."""
        try:
            if self.is_running:
                logger.warning("⚠️  Scheduler is already running")
                return

            # Setup schedule
            if not self.setup_weekly_schedule():
                raise RuntimeError("Failed to setup weekly schedule")

            # Start scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("🚀 WEEKLY META-TREND SCHEDULER STARTED")
            logger.info("📅 Waiting for weekly execution schedule...")
            logger.info("💡 Press Ctrl+C to stop the scheduler")

            # Keep running until interrupted
            try:
                while self.is_running:
                    await asyncio.sleep(60)  # Check every minute
                    
                    # Log status every hour
                    current_time = datetime.now(timezone.utc)
                    if current_time.minute == 0:
                        next_run = self.scheduler.get_job('weekly_meta_trend_analysis').next_run_time
                        logger.info(f"⏰ Scheduler running - Next meta-analysis: {next_run}")

            except KeyboardInterrupt:
                logger.info("⚠️  Scheduler interrupted by user")
            finally:
                await self.stop_scheduler()

        except Exception as e:
            logger.error(f"💥 Failed to start weekly scheduler: {str(e)}", exc_info=True)
            raise

    async def stop_scheduler(self):
        """Stop the weekly meta-trend scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("🛑 Weekly meta-trend scheduler stopped")
            
            self.is_running = False

        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {str(e)}")

    async def _send_discord_notification(self, result: dict, batch_id: str):
        """Send Discord notification for weekly meta-trend analysis."""
        try:
            from notifiers.discord_webhook_sender import DiscordWebhookSender
            
            discord_sender = DiscordWebhookSender()
            
            posts_analyzed = result.get('posts_analyzed', 0)
            success = result.get('success', False)
            
            if success:
                message = (
                    f"📅 **Weekly Meta-Trend Intelligence**\n"
                    f"✅ **Analysis Complete**\n"
                    f"📊 Posts Analyzed: **{posts_analyzed}**\n"
                    f"🔮 Weekly Insights: Generated\n"
                    f"🆔 Batch ID: `{batch_id}`\n"
                    f"⏰ Completed: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                )
            else:
                message = (
                    f"📅 **Weekly Meta-Trend Intelligence**\n"
                    f"❌ **Analysis Failed**\n"
                    f"🆔 Batch ID: `{batch_id}`\n"
                    f"⏰ Attempted: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                )

            await discord_sender.send_message(message)
            logger.info("💬 Discord notification sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to send Discord notification: {str(e)}")

    async def run_immediate_test(self):
        """Run immediate meta-trend analysis for testing."""
        logger.info("🧪 RUNNING IMMEDIATE WEEKLY META-TREND TEST")
        success = await self.run_weekly_meta_analysis()
        
        if success:
            logger.info("✅ Immediate test completed successfully")
        else:
            logger.error("❌ Immediate test failed")
        
        return success


async def main():
    """Main execution function for weekly meta scheduler."""
    scheduler = WeeklyMetaScheduler()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--test':
            # Run immediate test
            print("🧪 WEEKLY META-TREND IMMEDIATE TEST")
            print("=" * 50)
            success = await scheduler.run_immediate_test()
            return 0 if success else 1
        else:
            # Run scheduled weekly analysis
            print("📅 WEEKLY META-TREND SCHEDULER")
            print("=" * 50)
            await scheduler.start_scheduler()
            return 0

    except KeyboardInterrupt:
        print("\n⚠️  Weekly scheduler interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {str(e)}")
        logger.error(f"Unexpected error in weekly scheduler: {str(e)}", exc_info=True)
        return 3


if __name__ == "__main__":
    print("📅 WEEKLY META-TREND INTELLIGENCE SCHEDULER")
    print("Dedicated scheduler for weekly cross-engine analysis")
    print("Usage:")
    print("  python run_weekly_meta_scheduler.py        # Start weekly scheduler")
    print("  python run_weekly_meta_scheduler.py --test # Run immediate test")
    print()
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)