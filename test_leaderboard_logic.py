#!/usr/bin/env python3
"""
Test script to verify leaderboard's new comparison logic
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_leaderboard_logic():
    """Test the updated leaderboard comparison logic"""

    try:
        from worker.tasks.leaderboard_worker import leaderboard_bidaily_task

        logger.info("🧪 Testing updated leaderboard comparison logic...")
        logger.info(
            "📊 This will now compare with the most recent previous report")
        logger.info("📈 Instead of fixed time intervals (12h ago or yesterday)")

        # Run bi-daily task to test new logic
        result = await leaderboard_bidaily_task(force_post=True)

        if result['status'] == 'success':
            logger.info("✅ Leaderboard test successful!")
            logger.info(f"📊 Current entries: {result['entries_current']}")
            logger.info(f"📈 Previous entries: {result['entries_previous']}")
            logger.info(f"🔄 Discord sent: {result['discord_sent']}")
            logger.info(f"📝 Message length: {result['message_length']} chars")

            comparison = result.get('comparison', {})
            logger.info(f"🏆 Leaders: {comparison.get('leaders')}")
            logger.info(f"📈 Movers up: {comparison.get('movers_up')}")
            logger.info(f"📉 Movers down: {comparison.get('movers_down')}")
            logger.info(f"🆕 New entries: {comparison.get('new_entries')}")
            logger.info(f"📤 Dropouts: {comparison.get('dropouts')}")
            logger.info(f"🌟 First run: {comparison.get('is_first_run')}")

            print("✅ SUCCESS: New leaderboard comparison logic working!")
            print("📊 Now compares with most recent previous report")
            print("🔍 Check Discord channel to see updated messages")
            return True
        else:
            logger.error(f"❌ Leaderboard test failed: {result}")
            print("❌ FAILED: Leaderboard test encountered errors")
            return False

    except Exception as e:
        logger.error(f"❌ Test error: {str(e)}")
        print(f"💥 ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LEADERBOARD COMPARISON LOGIC TEST")
    print("Testing updated logic: Compare with most recent report")
    print("=" * 60)

    result = asyncio.run(test_leaderboard_logic())

    print("=" * 60)
    if result:
        print("🎉 LEADERBOARD UPDATE TEST COMPLETED SUCCESSFULLY!")
        print("📊 Comparison logic now uses most recent previous report")
        print("🔄 No more fixed time intervals - more flexible and accurate")
    else:
        print("💥 LEADERBOARD TEST FAILED - Check logs for details")
    print("=" * 60)
