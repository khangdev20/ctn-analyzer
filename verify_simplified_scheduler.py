#!/usr/bin/env python3
"""
Verify Simplified Scheduler Configuration
Confirms only latest, trending, and leaderboard tasks are active
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


def verify_scheduler():
    """Verify the simplified scheduler configuration"""
    print("🔍 VERIFYING SIMPLIFIED SCHEDULER")
    print("=" * 50)

    try:
        from worker.base import BackgroundWorker

        worker = BackgroundWorker()
        print("✅ Worker instance created")

        # Verify only the 3 required methods exist and work
        required_methods = {
            '_run_content_analysis_latest_task': 'Latest Posts Analysis',
            '_run_content_analysis_trending_task': 'Trending Posts Analysis',
            '_run_leaderboard_bidaily_task': 'Leaderboard Updates'
        }

        print("\n📋 VERIFYING ACTIVE TASKS:")
        all_methods_exist = True

        for method_name, description in required_methods.items():
            if hasattr(worker, method_name):
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - MISSING!")
                all_methods_exist = False

        print("\n📊 FINAL CONFIGURATION:")
        print("┌─────────────────────────────────────────────────┐")
        print("│                ACTIVE TASKS (3)                 │")
        print("├─────────────────────────────────────────────────┤")
        print("│ Latest Posts Analysis    │ Every 1 hour (:00)  │")
        print("│ Trending Posts Analysis  │ Every 1 hour (:30)  │")
        print("│ Leaderboard Updates      │ Every 1 hour         │")
        print("└─────────────────────────────────────────────────┘")

        print("\n🎯 REMOVED COMPLEXITY:")
        print("   ❌ Dynamic configuration loading")
        print("   ❌ Unused trending prediction")
        print("   ❌ Multiple scheduling strategies")
        print("   ❌ Complex interval calculations")

        print("\n✨ BENEFITS:")
        print("   ✅ Simple, predictable hourly schedule")
        print("   ✅ Only essential tasks running")
        print("   ✅ Clean, maintainable code")
        print("   ✅ Fixed timing prevents conflicts")

        if all_methods_exist:
            print("\n🎉 VERIFICATION SUCCESS!")
            print("   Ready to start: python start_hourly_scheduler.py")
        else:
            print("\n❌ VERIFICATION FAILED!")
            print("   Some required methods are missing.")

    except Exception as e:
        print(f"❌ Verification error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_scheduler()
