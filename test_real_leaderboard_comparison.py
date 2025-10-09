#!/usr/bin/env python3
"""
Real Leaderboard Comparison Test - Simulates time-based comparison with real data
Fetches real leaderboard data twice with 5-minute interval to test comparison logic
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_real_leaderboard_comparison():
    """Test real leaderboard comparison with time-based simulation"""

    try:
        from worker.tasks.leaderboard_worker import (
            fetch_all_pages, normalize_and_rank, compare_snapshots,
            format_bidaily_discord_message, send_discord
        )
        import os
        import pytz

        logger.info("🎯 REAL LEADERBOARD COMPARISON TEST")
        logger.info("=" * 60)
        logger.info("📊 This test will:")
        logger.info("1. Fetch real leaderboard data (1st time)")
        logger.info("2. Send Discord notification")
        logger.info("3. Wait 5 minutes")
        logger.info("4. Fetch real leaderboard data (2nd time)")
        logger.info("5. Compare changes and send update")

        # Test configuration
        api_url = os.getenv(
            'LEADERBOARD_API_URL', 'https://social.legitreal.com/api/competition/leaderboard/')
        webhook_url = os.getenv(
            'LEADERBOARD_DISCORD_WEBHOOK', os.getenv('DISCORD_WEBHOOK', ''))

        if not webhook_url:
            logger.warning(
                "⚠️ No Discord webhook configured - messages won't be sent")
            print("⚠️ WARNING: No Discord webhook configured")

        brisbane_tz = pytz.timezone('Australia/Brisbane')

        # === PHASE 1: First Fetch ===
        logger.info("🔄 PHASE 1: First leaderboard fetch...")
        start_time = datetime.now(brisbane_tz)
        timestamp1 = start_time.strftime("%Y-%m-%d_%H-%M")

        # Fetch first dataset
        logger.info("[FETCH] Getting first leaderboard snapshot...")
        raw_data1, status1 = fetch_all_pages(
            api_url, timeout=15, max_retries=3, max_pages=3)

        if not raw_data1:
            logger.error("❌ Failed to fetch first dataset")
            print("❌ FAILED: Could not fetch initial leaderboard data")
            return False

        # Normalize first dataset
        entries1 = normalize_and_rank(raw_data1)
        logger.info(f"✅ First snapshot: {len(entries1)} entries")

        # Format and send first message
        comparison1 = {
            'leaders_top10': entries1[:10],
            'movers_up': [],
            'movers_down': [],
            'new_entries': [],
            'dropouts': [],
            'total_today': len(entries1),
            'total_previous': 0,
            'is_first_run': True
        }

        message1 = format_bidaily_discord_message(
            timestamp1,
            comparison1,
            status1,
            f"🧪 TEST Phase 1 — Initial Snapshot ({start_time.strftime('%H:%M AEST')})"
        )

        # Add test context to message
        test_header = f"""🧪 **REAL LEADERBOARD COMPARISON TEST**
⏰ **Phase 1/2:** Initial snapshot at {start_time.strftime('%H:%M:%S AEST')}
📊 **Next:** Will fetch again in 5 minutes and compare changes

"""
        message1 = test_header + message1

        logger.info(f"📝 Generated Phase 1 message ({len(message1)} chars)")

        # Send first Discord message
        if webhook_url:
            discord_result1 = await asyncio.get_event_loop().run_in_executor(
                None, lambda: send_discord(message1, webhook_url)
            )
            if discord_result1.get('success'):
                logger.info("✅ Phase 1 Discord message sent successfully")
                print("✅ Phase 1: Initial snapshot sent to Discord")
            else:
                logger.warning("⚠️ Phase 1 Discord message failed")
                print("⚠️ Phase 1: Discord send failed")
        else:
            logger.info(
                "ℹ️ Phase 1: Discord message prepared (no webhook configured)")
            print("ℹ️ Phase 1: Message prepared (no webhook)")

        # === WAIT PERIOD ===
        wait_minutes = 5
        logger.info(
            f"⏳ WAITING {wait_minutes} minutes for leaderboard changes...")
        print(f"⏳ Waiting {wait_minutes} minutes for changes...")
        print("   (In production, this would be natural time between reports)")

        # Show countdown
        for remaining in range(wait_minutes * 60, 0, -30):
            mins, secs = divmod(remaining, 60)
            logger.info(f"⏳ Time remaining: {mins}:{secs:02d}")
            await asyncio.sleep(30)

        logger.info("⏰ Wait period complete - fetching second snapshot...")

        # === PHASE 2: Second Fetch ===
        logger.info("🔄 PHASE 2: Second leaderboard fetch...")
        second_time = datetime.now(brisbane_tz)
        timestamp2 = second_time.strftime("%Y-%m-%d_%H-%M")

        # Fetch second dataset
        logger.info("[FETCH] Getting second leaderboard snapshot...")
        raw_data2, status2 = fetch_all_pages(
            api_url, timeout=15, max_retries=3, max_pages=3)

        if not raw_data2:
            logger.error("❌ Failed to fetch second dataset")
            print("❌ FAILED: Could not fetch second leaderboard data")
            return False

        # Normalize second dataset
        entries2 = normalize_and_rank(raw_data2)
        logger.info(f"✅ Second snapshot: {len(entries2)} entries")

        # === COMPARISON ===
        logger.info("🔍 COMPARING snapshots...")
        comparison2 = compare_snapshots(entries2, entries1)

        # Log comparison results
        logger.info(f"📊 Comparison results:")
        logger.info(f"   Leaders: {len(comparison2.get('leaders_top10', []))}")
        logger.info(f"   Movers up: {len(comparison2.get('movers_up', []))}")
        logger.info(
            f"   Movers down: {len(comparison2.get('movers_down', []))}")
        logger.info(
            f"   New entries: {len(comparison2.get('new_entries', []))}")
        logger.info(f"   Dropouts: {len(comparison2.get('dropouts', []))}")

        # Format and send comparison message
        time_elapsed = second_time - start_time
        elapsed_str = f"{int(time_elapsed.total_seconds() // 60)}m {int(time_elapsed.total_seconds() % 60)}s"

        message2 = format_bidaily_discord_message(
            timestamp2,
            comparison2,
            status2,
            f"🧪 TEST Phase 2 — Changes After {elapsed_str} ({second_time.strftime('%H:%M AEST')})"
        )

        # Add test comparison context
        test_header2 = f"""🧪 **REAL LEADERBOARD COMPARISON TEST — RESULTS**
⏰ **Phase 2/2:** Comparison after {elapsed_str} wait
📊 **Changes detected:** {len(comparison2.get('movers_up', []))} up, {len(comparison2.get('movers_down', []))} down
🆕 **New entries:** {len(comparison2.get('new_entries', []))} | **Dropouts:** {len(comparison2.get('dropouts', []))}

"""
        message2 = test_header2 + message2

        logger.info(f"📝 Generated Phase 2 message ({len(message2)} chars)")

        # Send second Discord message
        if webhook_url:
            discord_result2 = await asyncio.get_event_loop().run_in_executor(
                None, lambda: send_discord(message2, webhook_url)
            )
            if discord_result2.get('success'):
                logger.info("✅ Phase 2 Discord message sent successfully")
                print("✅ Phase 2: Comparison results sent to Discord")
            else:
                logger.warning("⚠️ Phase 2 Discord message failed")
                print("⚠️ Phase 2: Discord send failed")
        else:
            logger.info(
                "ℹ️ Phase 2: Discord message prepared (no webhook configured)")
            print("ℹ️ Phase 2: Comparison message prepared (no webhook)")

        # === SUMMARY ===
        logger.info("📋 TEST SUMMARY:")
        logger.info(
            f"   Phase 1: {len(entries1)} entries at {start_time.strftime('%H:%M:%S')}")
        logger.info(
            f"   Phase 2: {len(entries2)} entries at {second_time.strftime('%H:%M:%S')}")
        logger.info(f"   Elapsed: {elapsed_str}")
        logger.info(
            f"   Changes: {len(comparison2.get('movers_up', []))} up, {len(comparison2.get('movers_down', []))} down")

        # Save test results
        test_results = {
            'test_type': 'real_leaderboard_comparison',
            'phase_1': {
                'timestamp': timestamp1,
                'entries_count': len(entries1),
                'fetch_status': status1,
                'discord_sent': discord_result1.get('success', False) if webhook_url else None
            },
            'phase_2': {
                'timestamp': timestamp2,
                'entries_count': len(entries2),
                'fetch_status': status2,
                'discord_sent': discord_result2.get('success', False) if webhook_url else None
            },
            'comparison': {
                'time_elapsed_seconds': int(time_elapsed.total_seconds()),
                'leaders': len(comparison2.get('leaders_top10', [])),
                'movers_up': len(comparison2.get('movers_up', [])),
                'movers_down': len(comparison2.get('movers_down', [])),
                'new_entries': len(comparison2.get('new_entries', [])),
                'dropouts': len(comparison2.get('dropouts', []))
            },
            'test_completed': datetime.now().isoformat()
        }

        # Create test_reports directory if it doesn't exist
        reports_dir = Path("test_reports")
        reports_dir.mkdir(exist_ok=True)

        # Save test results
        test_file = reports_dir / \
            f"real_leaderboard_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_file, 'w') as f:
            json.dump(test_results, f, indent=2)

        logger.info(f"💾 Test results saved: {test_file}")

        print("=" * 60)
        print("🎉 REAL LEADERBOARD COMPARISON TEST COMPLETED!")
        print(f"⏰ Total test time: {elapsed_str}")
        print(f"📊 Snapshots: {len(entries1)} → {len(entries2)} entries")
        print(
            f"🔄 Changes: {len(comparison2.get('movers_up', []))} up, {len(comparison2.get('movers_down', []))} down")
        print(
            f"🆕 New: {len(comparison2.get('new_entries', []))}, Dropouts: {len(comparison2.get('dropouts', []))}")
        print(f"💾 Results saved: {test_file}")
        if webhook_url:
            print("📱 Check Discord channel for test messages")
        print("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Test error: {str(e)}", exc_info=True)
        print(f"💥 TEST ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 REAL LEADERBOARD COMPARISON TEST")
    print("=" * 60)
    print("📊 This test will fetch real leaderboard data twice with 5-minute interval")
    print("🔍 It will compare changes and send Discord notifications")
    print("⏰ Total test time: ~5 minutes")
    print("=" * 60)

    # Ask for confirmation
    confirm = input(
        "🤔 Do you want to start the 5-minute test? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("❌ Test cancelled by user")
        sys.exit(0)

    print("🚀 Starting real leaderboard comparison test...")
    result = asyncio.run(test_real_leaderboard_comparison())

    if result:
        print("🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("💥 Test failed!")
        sys.exit(1)
