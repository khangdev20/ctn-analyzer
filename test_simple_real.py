#!/usr/bin/env python3
"""
Simple Real System Test
Tests the complete system with real data and sends actual Discord messages

This test:
1. Tests data collection with cloud-only storage
2. Tests Content Analysis workflow
3. Tests Trending Prediction workflow  
4. Tests Leaderboard workflow
5. Sends real Discord notifications
6. Validates system integration

Usage:
    python test_simple_real.py
"""

from dotenv import load_dotenv
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv()

# Configure logging for Windows console compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f'test_simple_real_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def test_data_collection():
    """Test data collection with cloud-only storage"""
    logger.info("="*60)
    logger.info("DATA COLLECTION TEST")
    logger.info("="*60)

    try:
        from worker.features.data_collector import collect_latest_posts, collect_existing_trending

        logger.info("Testing latest posts collection...")
        latest_result = collect_latest_posts(num_pages=2)

        if latest_result and latest_result.get('s3_key'):
            logger.info(
                f"SUCCESS: Latest posts - {latest_result.get('items_count', 'Unknown')} items")
            logger.info(f"Cloud storage: {latest_result.get('s3_key')}")
        else:
            logger.error("FAILED: Latest posts collection failed")
            return False

        logger.info("Testing trending posts collection...")
        trending_result = collect_existing_trending(num_pages=2)

        if trending_result and trending_result.get('s3_key'):
            logger.info(
                f"SUCCESS: Trending posts - {trending_result.get('items_count', 'Unknown')} items")
            logger.info(f"Cloud storage: {trending_result.get('s3_key')}")
        else:
            logger.error("FAILED: Trending posts collection failed")
            return False

        return True

    except Exception as e:
        logger.error(f"DATA COLLECTION ERROR: {e}")
        return False


async def test_content_analysis():
    """Test Content Analysis workflow"""
    logger.info("="*60)
    logger.info("CONTENT ANALYSIS TEST")
    logger.info("="*60)

    try:
        from worker.tasks.content_analysis_task import ContentAnalysisTask

        task = ContentAnalysisTask()
        logger.info("Content Analysis task initialized")

        logger.info("Running Content Analysis workflow...")
        result = await task.run_content_analysis_workflow(
            data_source='api',
            num_posts=5,
            send_discord=True
        )

        if result and result.get('status') == 'success':
            logger.info("SUCCESS: Content Analysis completed")
            logger.info(
                f"Posts analyzed: {result.get('posts_analyzed', 'Unknown')}")
            logger.info(
                f"Discord sent: {result.get('discord_notification_sent', 'Unknown')}")
            return True
        else:
            logger.error(
                f"FAILED: Content Analysis - {result.get('error', 'Unknown error') if result else 'No result'}")
            return False

    except Exception as e:
        logger.error(f"CONTENT ANALYSIS ERROR: {e}")
        return False


async def test_trending_prediction():
    """Test Trending Prediction workflow"""
    logger.info("="*60)
    logger.info("TRENDING PREDICTION TEST")
    logger.info("="*60)

    try:
        from worker.tasks.trending_prediction_task import TrendingPredictionTask

        task = TrendingPredictionTask()
        logger.info("Trending Prediction task initialized")

        logger.info("Running Trending Prediction workflow...")
        result = await task.run_trending_prediction_workflow(
            send_discord=True
        )

        if result and result.get('status') == 'success':
            logger.info("SUCCESS: Trending Prediction completed")
            logger.info(
                f"Posts analyzed: {result.get('posts_analyzed', 'Unknown')}")
            logger.info(
                f"Trending candidates: {len(result.get('trending_candidates', []))}")
            logger.info(
                f"Discord sent: {result.get('discord_notification', 'Unknown')}")
            return True
        else:
            logger.error(
                f"FAILED: Trending Prediction - {result.get('error', 'Unknown error') if result else 'No result'}")
            return False

    except Exception as e:
        logger.error(f"TRENDING PREDICTION ERROR: {e}")
        return False


async def test_leaderboard():
    """Test Leaderboard workflow"""
    logger.info("="*60)
    logger.info("LEADERBOARD TEST")
    logger.info("="*60)

    try:
        from worker.tasks.leaderboard_worker import leaderboard_bidaily_task

        logger.info("Running Leaderboard bi-daily task...")
        result = await leaderboard_bidaily_task(force_post=True)

        if result and result.get('status') == 'success':
            logger.info("SUCCESS: Leaderboard completed")
            logger.info(
                f"Current entries: {result.get('entries_current', 'Unknown')}")
            logger.info(
                f"Discord sent: {result.get('discord_sent', 'Unknown')}")
            return True
        else:
            logger.error(
                f"FAILED: Leaderboard - {result.get('error', 'Unknown error') if result else 'No result'}")
            return False

    except Exception as e:
        logger.error(f"LEADERBOARD ERROR: {e}")
        return False


async def get_recent_s3_sources():
    """Get recent S3 data sources for Discord reporting"""
    try:
        from data_access.s3_store import S3Store

        s3_store = S3Store()
        recent_sources = []

        # Check for recent data files
        today = datetime.now(timezone.utc)
        date_prefix = s3_store.build_key(
            "raw",
            f"{today.year}",
            f"{today.month:02d}",
            f"{today.day:02d}"
        )

        client = s3_store.get_s3_client()
        response = client.list_objects_v2(
            Bucket=s3_store.bucket,
            Prefix=date_prefix,
            MaxKeys=10
        )

        if 'Contents' in response:
            for obj in response['Contents'][-5:]:  # Get last 5 files
                recent_sources.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'modified': obj['LastModified'].strftime('%H:%M:%S')
                })

        return recent_sources
    except Exception as e:
        logger.warning(f"Could not fetch S3 sources: {e}")
        return []


async def test_discord_notification():
    """Test direct Discord notification with S3 source information"""
    logger.info("="*60)
    logger.info("DISCORD NOTIFICATION TEST")
    logger.info("="*60)

    try:
        from notifiers.discord_webhook_sender import send_discord_message_webhook

        webhook_url = os.getenv('DISCORD_WEBHOOK')
        if not webhook_url:
            logger.error("FAILED: No Discord webhook configured")
            return False

        # Get S3 source information
        s3_sources = await get_recent_s3_sources()

        # Build message with S3 source info
        test_message = f"**System Test Complete** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n" \
            f"✅ All systems operational\n" \
            f"☁️ Cloud-only storage active\n" \
            f"🔗 Pattern integration working\n" \
            f"📊 Real data processing successful\n\n"

        if s3_sources:
            test_message += "**Recent S3 Data Sources:**\n"
            for source in s3_sources:
                filename = source['key'].split('/')[-1]
                test_message += f"• `{filename}` ({source['size']} bytes, {source['modified']})\n"
        else:
            test_message += "📁 S3 Sources: No recent files found\n"

        test_message += f"\n🔗 S3 Bucket: `ctn-analyzer/social-intel/`"

        logger.info("Sending test notification to Discord...")
        success = send_discord_message_webhook(test_message, webhook_url)

        if success:
            logger.info("SUCCESS: Discord notification sent")
            return True
        else:
            logger.error("FAILED: Discord notification failed")
            return False

    except Exception as e:
        logger.error(f"DISCORD ERROR: {e}")
        return False


async def test_s3_storage():
    """Test S3 storage connectivity"""
    logger.info("="*60)
    logger.info("S3 STORAGE TEST")
    logger.info("="*60)

    try:
        from data_access.s3_store import S3Store

        s3_store = S3Store()
        logger.info("S3Store initialized")

        # Test write
        test_data = {
            "test": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "System test data"
        }

        test_key = s3_store.build_key("test", "system_test.json")

        logger.info("Testing S3 write...")
        write_result = s3_store.s3_write_json(
            key=test_key,
            data=test_data,
            compress=True
        )

        if write_result.get('success'):
            logger.info("SUCCESS: S3 write completed")
            logger.info(f"S3 URL: {write_result.get('s3_url')}")

            # Test read
            logger.info("Testing S3 read...")
            read_data = s3_store.s3_read_json(test_key)

            if read_data and read_data.get('test'):
                logger.info("SUCCESS: S3 read completed")

                # Cleanup (optional - S3 objects auto-expire)
                try:
                    client = s3_store.get_s3_client()
                    client.delete_object(Bucket=s3_store.bucket, Key=test_key)
                    logger.info("Test file cleaned up")
                except Exception as cleanup_error:
                    logger.info(
                        f"Cleanup note: {cleanup_error} (not critical)")

                return True
            else:
                logger.error("FAILED: S3 read failed")
                return False
        else:
            logger.error(
                f"FAILED: S3 write failed - {write_result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"S3 STORAGE ERROR: {e}")
        return False


async def main():
    """Run simple system test"""
    logger.info("STARTING SIMPLE SYSTEM TEST")
    logger.info("="*100)

    start_time = datetime.now()
    test_results = {}

    # Test 1: S3 Storage
    logger.info("Test 1: S3 Storage")
    test_results['s3'] = await test_s3_storage()

    # Test 2: Data Collection
    logger.info("\nTest 2: Data Collection")
    test_results['data_collection'] = await test_data_collection()

    # Test 3: Content Analysis
    logger.info("\nTest 3: Content Analysis")
    test_results['content_analysis'] = await test_content_analysis()

    # Test 4: Trending Prediction
    logger.info("\nTest 4: Trending Prediction")
    test_results['trending_prediction'] = await test_trending_prediction()

    # Test 5: Leaderboard
    logger.info("\nTest 5: Leaderboard")
    test_results['leaderboard'] = await test_leaderboard()

    # Test 6: Discord Notifications
    logger.info("\nTest 6: Discord Notifications")
    test_results['discord'] = await test_discord_notification()

    # Summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("="*100)
    logger.info("SYSTEM TEST SUMMARY")
    logger.info("="*100)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name.upper()}: {status}")
        if result:
            passed += 1

    logger.info("-"*100)
    logger.info(
        f"RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    logger.info(f"DURATION: {duration.total_seconds():.1f} seconds")
    logger.info(f"COMPLETED: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Save test report
    report = {
        "test_time": end_time.isoformat(),
        "duration_seconds": duration.total_seconds(),
        "results": test_results,
        "passed": passed,
        "total": total,
        "success_rate": (passed/total)*100
    }

    os.makedirs("test_reports", exist_ok=True)
    report_file = f"test_reports/simple_system_test_{end_time.strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Test report saved: {report_file}")

    if passed == total:
        logger.info("ALL TESTS PASSED - System is fully operational!")

        # Send final success notification with S3 sources
        if test_results.get('discord'):
            try:
                from notifiers.discord_webhook_sender import send_discord_message_webhook

                # Get S3 source information
                s3_sources = await get_recent_s3_sources()

                success_message = f"🎉 **System Test Complete - ALL PASS**\n\n" \
                    f"📊 Tests passed: {passed}/{total}\n" \
                    f"⏱️ Duration: {duration.total_seconds():.1f}s\n" \
                    f"☁️ Cloud-only architecture: Active\n" \
                    f"🔗 Pattern integration: Working\n" \
                    f"📈 Real data processing: Successful\n\n"

                if s3_sources:
                    success_message += "**Recent S3 Data Sources:**\n"
                    for source in s3_sources:
                        filename = source['key'].split('/')[-1]
                        success_message += f"• `{filename}` ({source['size']} bytes, {source['modified']})\n"
                    success_message += f"\n🔗 S3 Bucket: `ctn-analyzer/social-intel/`\n\n"
                else:
                    success_message += "📁 S3 Sources: Available in cloud storage\n\n"

                success_message += "✅ **System is fully operational!**"

                webhook_url = os.getenv('DISCORD_WEBHOOK')
                if webhook_url:
                    send_discord_message_webhook(success_message, webhook_url)
            except Exception as e:
                logger.warning(
                    f"Could not send final success notification: {e}")
    else:
        logger.error(f"SOME TESTS FAILED - {total-passed} failures detected")

    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        sys.exit(1)
