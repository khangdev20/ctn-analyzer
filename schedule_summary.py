#!/usr/bin/env python3
"""
Hourly Content Analysis Scheduler Summary
Shows the new hourly scheduling configuration for latest and trending posts
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


def show_schedule_summary():
    """Display the new hourly schedule configuration"""
    print("🕐 HOURLY CONTENT ANALYSIS SCHEDULER")
    print("=" * 60)
    print()
    print("📊 SCHEDULED JOBS:")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│ 1. Latest Posts Analysis     │ Every 1 hour at :00     │")
    print("│ 2. Trending Posts Analysis   │ Every 1 hour at :30     │")
    print("│ 3. Leaderboard Updates       │ Every 1 hour             │")
    print("└─────────────────────────────────────────────────────────┘")
    print()
    print("⏰ TIMING EXAMPLE:")
    print("   • 14:00 - Latest Posts Analysis runs")
    print("   • 14:30 - Trending Posts Analysis runs")
    print("   • 15:00 - Latest Posts Analysis runs")
    print("   • 15:30 - Trending Posts Analysis runs")
    print("   • And so on...")
    print()
    print("🚀 HOW TO START:")
    print("   python start_hourly_scheduler.py")
    print()
    print("🧪 HOW TO TEST:")
    print("   python test_hourly_scheduler.py")
    print()
    print("🔧 MANUAL TRIGGERS:")
    print("   python trigger_latest.py          # Run latest posts now")
    print("   python trigger_trending_posts.py  # Run trending posts now")
    print("   python content_triggers.py both   # Run both now")
    print()
    print("📋 FEATURES:")
    print("   ✅ 30-minute offset between latest and trending")
    print("   ✅ Full Discord reporting with rich embeds")
    print("   ✅ S3 cloud storage integration")
    print("   ✅ Competition context for LLM compliance")
    print("   ✅ Clean, focused logging")
    print("   ✅ Error handling and recovery")
    print()


def show_quick_commands():
    """Show quick command reference"""
    print("⚡ QUICK COMMANDS:")
    print("=" * 30)
    print("Start scheduler:")
    print("  python start_hourly_scheduler.py")
    print()
    print("Test individual:")
    print("  python trigger_latest.py")
    print("  python trigger_trending_posts.py")
    print()
    print("Run both once:")
    print("  python content_triggers.py both")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        show_quick_commands()
    else:
        show_schedule_summary()
