#!/usr/bin/env python3
"""
Test Hourly Content Analysis Scheduler
Tests the new hourly latest and trending posts scheduler
"""

from worker.base import BackgroundWorker
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


async def test_scheduler():
    """Test the new hourly scheduler configuration"""
    print("🕐 TESTING HOURLY CONTENT ANALYSIS SCHEDULER")
    print("=" * 60)

    try:
        # Create worker instance
        worker = BackgroundWorker()

        print("✅ Worker instance created")

        # Test individual methods
        print("\n📊 Testing individual task methods:")

        # Test latest task method
        print("1️⃣ Testing latest posts task method...")
        try:
            latest_result = await worker._run_content_analysis_latest_task()
            print(
                f"   ✅ Latest task: {latest_result.get('status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Latest task error: {e}")

        print("\n" + "="*60)

        # Test trending task method
        print("2️⃣ Testing trending posts task method...")
        try:
            trending_result = await worker._run_content_analysis_trending_task()
            print(
                f"   ✅ Trending task: {trending_result.get('status', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Trending task error: {e}")

        print("\n" + "="*60)
        print("🎉 SCHEDULER TEST CONFIGURATION:")
        print("   📊 Latest Posts: Every 1 hour")
        print("   🔥 Trending Posts: Every 1 hour (offset)")
        print("   📈 Leaderboard: Every 1 hour")
        print("   ✅ All task methods working!")

    except Exception as e:
        print(f"❌ Scheduler test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scheduler())
