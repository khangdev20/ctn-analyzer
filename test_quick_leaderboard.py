#!/usr/bin/env python3
"""
Quick Real Leaderboard Comparison Test - 2-minute version
Fetches real leaderboard data twice with 2-minute interval for quick testing
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def quick_leaderboard_test():
    """Quick 2-minute leaderboard comparison test"""

    try:
        from worker.tasks.leaderboard_worker import (
            fetch_all_pages, normalize_and_rank, compare_snapshots,
            format_bidaily_discord_message, send_discord
        )
        import os
        import pytz

        logger.info("⚡ QUICK LEADERBOARD TEST (2 minutes)")
        logger.info("=" * 50)

        # Configuration
        api_url = os.getenv(
            'LEADERBOARD_API_URL', 'https://social.legitreal.com/api/competition/leaderboard/')
        webhook_url = os.getenv(
            'LEADERBOARD_DISCORD_WEBHOOK', os.getenv('DISCORD_WEBHOOK', ''))
        brisbane_tz = pytz.timezone('Australia/Brisbane')

        # === SNAPSHOT 1 ===
        logger.info("📊 Taking first snapshot...")
        time1 = datetime.now(brisbane_tz)

        raw_data1, status1 = fetch_all_pages(api_url, max_pages=2)
        if not raw_data1:
            print("❌ Failed to fetch first snapshot")
            return False

        entries1 = normalize_and_rank(raw_data1)
        logger.info(f"✅ Snapshot 1: {len(entries1)} entries")

        # Send first message
        if webhook_url:
            message1 = f"""⚡ **QUICK TEST — Snapshot 1**
🕐 **Time:** {time1.strftime('%H:%M:%S AEST')}
📊 **Entries:** {len(entries1)}
⏳ **Next:** Snapshot 2 in 2 minutes

🏆 **Top 5:**
{chr(10).join([f"#{i+1} {entries1[i]['name']} — {entries1[i]['score']:,}" for i in range(min(5, len(entries1)))])}
"""

            result1 = send_discord(message1, webhook_url)
            logger.info(f"📱 Message 1 sent: {result1.get('success', False)}")

        # === WAIT 2 MINUTES ===
        logger.info("⏳ Waiting 2 minutes...")
        for i in range(120, 0, -30):
            mins, secs = divmod(i, 60)
            logger.info(f"⏳ {mins}:{secs:02d} remaining...")
            await asyncio.sleep(30)

        # === SNAPSHOT 2 ===
        logger.info("📊 Taking second snapshot...")
        time2 = datetime.now(brisbane_tz)

        raw_data2, status2 = fetch_all_pages(api_url, max_pages=2)
        if not raw_data2:
            print("❌ Failed to fetch second snapshot")
            return False

        entries2 = normalize_and_rank(raw_data2)
        logger.info(f"✅ Snapshot 2: {len(entries2)} entries")

        # Compare
        comparison = compare_snapshots(entries2, entries1)
        elapsed = time2 - time1

        logger.info("🔍 Comparison results:")
        logger.info(f"   Movers up: {len(comparison.get('movers_up', []))}")
        logger.info(
            f"   Movers down: {len(comparison.get('movers_down', []))}")
        logger.info(
            f"   New entries: {len(comparison.get('new_entries', []))}")
        logger.info(f"   Dropouts: {len(comparison.get('dropouts', []))}")

        # Send comparison message
        if webhook_url:
            changes_summary = []

            movers_up = comparison.get('movers_up', [])
            if movers_up:
                changes_summary.append(f"📈 **{len(movers_up)} moved up:**")
                for mover in movers_up[:3]:  # Top 3
                    changes_summary.append(
                        f"   • {mover['name']} (#{mover['rank']}) ↑{mover['rank_delta']}")

            movers_down = comparison.get('movers_down', [])
            if movers_down:
                changes_summary.append(f"📉 **{len(movers_down)} moved down:**")
                for mover in movers_down[:3]:  # Top 3
                    changes_summary.append(
                        f"   • {mover['name']} (#{mover['rank']}) ↓{abs(mover['rank_delta'])}")

            new_entries = comparison.get('new_entries', [])
            if new_entries:
                changes_summary.append(
                    f"🆕 **{len(new_entries)} new entries:**")
                for entry in new_entries[:3]:
                    changes_summary.append(
                        f"   • {entry['name']} (#{entry['rank']})")

            dropouts = comparison.get('dropouts', [])
            if dropouts:
                changes_summary.append(f"📤 **{len(dropouts)} dropouts:**")
                for dropout in dropouts[:3]:
                    changes_summary.append(
                        f"   • {dropout['name']} (was #{dropout.get('previous_rank', 'N/A')})")

            if not any([movers_up, movers_down, new_entries, dropouts]):
                changes_summary.append("🔄 **No significant changes detected**")
                changes_summary.append(
                    "   (This is normal for short time intervals)")

            message2 = f"""⚡ **QUICK TEST — Comparison Results**
🕐 **Time:** {time2.strftime('%H:%M:%S AEST')}
⏱️ **Elapsed:** {int(elapsed.total_seconds()//60)}m {int(elapsed.total_seconds() % 60)}s
📊 **Entries:** {len(entries1)} → {len(entries2)}

{chr(10).join(changes_summary)}

✅ **Test completed successfully!**
"""

            result2 = send_discord(message2, webhook_url)
            logger.info(f"📱 Message 2 sent: {result2.get('success', False)}")

        # Save results
        test_results = {
            'test_type': 'quick_leaderboard_comparison',
            'duration_seconds': int(elapsed.total_seconds()),
            'snapshot1': {
                'time': time1.isoformat(),
                'entries': len(entries1)
            },
            'snapshot2': {
                'time': time2.isoformat(),
                'entries': len(entries2)
            },
            'changes': {
                'movers_up': len(comparison.get('movers_up', [])),
                'movers_down': len(comparison.get('movers_down', [])),
                'new_entries': len(comparison.get('new_entries', [])),
                'dropouts': len(comparison.get('dropouts', []))
            }
        }

        # Save to file
        reports_dir = Path("test_reports")
        reports_dir.mkdir(exist_ok=True)
        test_file = reports_dir / \
            f"quick_leaderboard_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_file, 'w') as f:
            json.dump(test_results, f, indent=2)

        print("=" * 50)
        print("🎉 QUICK TEST COMPLETED!")
        print(
            f"⏱️ Duration: {int(elapsed.total_seconds()//60)}m {int(elapsed.total_seconds() % 60)}s")
        print(
            f"📊 Changes: {len(comparison.get('movers_up', []))} up, {len(comparison.get('movers_down', []))} down")
        print(f"💾 Results: {test_file}")
        if webhook_url:
            print("📱 Check Discord for test messages")
        print("=" * 50)

        return True

    except Exception as e:
        logger.error(f"❌ Test error: {str(e)}")
        print(f"💥 ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("⚡ QUICK LEADERBOARD COMPARISON TEST")
    print("⏱️ Duration: 2 minutes")
    print("📊 Real data, real Discord messages")
    print("=" * 50)

    confirm = input("🚀 Start quick test? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("❌ Cancelled")
        sys.exit(0)

    result = asyncio.run(quick_leaderboard_test())
    sys.exit(0 if result else 1)
