# 🕐 Test Scheduler Configuration - Kiểm tra cấu hình 15 phút

import asyncio
import logging
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scheduler_config():
    """Test scheduler configuration for 15-minute interval"""
    logger.info("🔍 Testing scheduler configuration...")
    
    try:
        # Test config import
        from worker.features.trending_config import get_config
        config = get_config()
        
        logger.info(f"✅ Config loaded successfully")
        logger.info(f"📅 Collection interval: {config.collection_interval_minutes} minutes")
        logger.info(f"📦 Batch size: {config.batch_size}")
        logger.info(f"🎯 LLM model: {config.llm_model}")
        logger.info(f"🔔 Discord notifications: {config.discord_notifications_enabled}")
        
        # Test scheduler import
        from worker.scheduler import run_scheduler_loop
        logger.info(f"✅ Scheduler import successful")
        
        # Test worker import
        from worker.base import BackgroundWorker
        logger.info(f"✅ Worker import successful")
        
        # Create test worker
        worker = BackgroundWorker()
        logger.info(f"✅ Worker instance created")
        
        # Test that scheduler can access config
        expected_interval = config.collection_interval_minutes
        logger.info(f"📊 Expected trending task interval: {expected_interval} minutes")
        
        if expected_interval == 15:
            logger.info("✅ PASS: Trending intelligence task is configured for 15 minutes")
            return True
        else:
            logger.error(f"❌ FAIL: Expected 15 minutes, got {expected_interval} minutes")
            return False
            
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_scheduler_jobs():
    """Test scheduler job configuration"""
    logger.info("🕐 Testing scheduler jobs...")
    
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from worker.features.trending_config import get_config
        
        config = get_config()
        scheduler = AsyncIOScheduler()
        
        # Mock worker for testing
        class MockWorker:
            def __init__(self):
                self.is_running = True
                self.active_tasks = []
            
            async def _run_trending_intelligence_task_with_cleanup(self):
                logger.info("📊 Mock trending intelligence task called")
            
            async def _run_sample_task(self):
                logger.info("🔄 Mock sample task called")
            
            async def _cleanup_stuck_jobs(self):
                logger.info("🧹 Mock cleanup task called")
        
        worker = MockWorker()
        
        # Add jobs like the real scheduler
        scheduler.add_job(
            worker._run_trending_intelligence_task_with_cleanup,
            'interval',
            minutes=config.collection_interval_minutes,
            id='trending_intelligence_main',
            max_instances=1,
            misfire_grace_time=300
        )
        
        scheduler.add_job(
            worker._run_sample_task,
            'interval',
            minutes=2,
            id='sample_task_test',
            max_instances=1
        )
        
        scheduler.add_job(
            worker._cleanup_stuck_jobs,
            'interval',
            minutes=30,
            id='cleanup_stuck_jobs',
            max_instances=1
        )
        
        # Check jobs
        jobs = scheduler.get_jobs()
        logger.info(f"📋 Scheduler has {len(jobs)} jobs:")
        
        trending_job = None
        for job in jobs:
            logger.info(f"  - {job.id}: runs every {job.trigger.interval}")
            if job.id == 'trending_intelligence_main':
                trending_job = job
        
        if trending_job:
            interval_minutes = trending_job.trigger.interval.total_seconds() / 60
            logger.info(f"🎯 Trending intelligence job interval: {interval_minutes} minutes")
            
            if interval_minutes == 15:
                logger.info("✅ PASS: Trending intelligence job configured for 15 minutes")
                return True
            else:
                logger.error(f"❌ FAIL: Expected 15 minutes, got {interval_minutes} minutes")
                return False
        else:
            logger.error("❌ FAIL: Trending intelligence job not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Scheduler jobs test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Run scheduler configuration tests"""
    logger.info("🚀 Starting Scheduler Configuration Tests")
    logger.info("=" * 60)
    
    test_results = []
    
    # Test configuration
    logger.info("🔧 Test 1: Configuration Loading")
    config_result = await test_scheduler_config()
    test_results.append(("Configuration", config_result))
    
    # Test scheduler jobs
    logger.info("\n🕐 Test 2: Scheduler Jobs")
    jobs_result = await test_scheduler_jobs()
    test_results.append(("Scheduler Jobs", jobs_result))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
    
    if success_rate == 1.0:
        logger.info("🎉 ALL TESTS PASSED - Trending intelligence task is configured for 15 minutes!")
    else:
        logger.error("💥 SOME TESTS FAILED - Check configuration!")
    
    return 0 if success_rate == 1.0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)