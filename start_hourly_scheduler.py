#!/usr/bin/env python3
"""
Start Hourly Content Analysis Scheduler
Starts the scheduler with hourly latest and trending analysis
"""

from worker.scheduler import run_scheduler_loop
from worker.base import BackgroundWorker
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


async def start_hourly_scheduler():
    """Start the hourly content analysis scheduler"""
    print("🕐 STARTING HOURLY CONTENT ANALYSIS SCHEDULER")
    print("=" * 60)
    print("📊 SCHEDULE:")
    print("   • Latest Posts Analysis: Every 1 hour")
    print("   • Trending Posts Analysis: Every 1 hour (offset)")
    print("   • Leaderboard Updates: Every 1 hour")
    print("=" * 60)
    print("Press Ctrl+C to stop the scheduler")
    print()

    try:
        # Create worker instance
        worker = BackgroundWorker()

        # Start the scheduler loop
        await run_scheduler_loop(worker)

    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(start_hourly_scheduler())
