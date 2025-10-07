#!/usr/bin/env python3
"""
Test the full trending intelligence task flow
"""

from worker.tasks.trending_intelligence_task import TrendingIntelligenceTask
import sys
import os
import asyncio
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MockWorker:
    """Mock worker for testing"""

    def __init__(self):
        self.active_tasks = []
        self.task_count = 0


async def test_full_pipeline():
    """Test the full trending intelligence pipeline"""

    print("[TEST] Testing full trending intelligence pipeline...")

    # Create mock worker
    worker = MockWorker()
    worker.task_count = 1

    try:
        # Create task instance
        task = TrendingIntelligenceTask()
        print("[INSTANCE] TrendingIntelligenceTask created successfully")

        # Run the full pipeline
        print("[PIPELINE] Starting full pipeline...")
        result = await task.run_full_pipeline(worker)

        if result:
            print(f"[SUCCESS] Pipeline completed successfully!")
            print(f"[RESULT] Status: {result.get('status', 'unknown')}")
            if 'discord_sent' in result:
                print(
                    f"[DISCORD] Discord notification sent: {result['discord_sent']}")
            if 'batch_id' in result:
                print(f"[BATCH] Batch ID: {result['batch_id']}")
        else:
            print("[FAILED] Pipeline returned no result")

    except Exception as e:
        print(f"[ERROR] Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
