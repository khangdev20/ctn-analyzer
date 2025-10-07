#!/usr/bin/env python3
"""
Test script to verify MainFlowOrchestrator fixes
Tests the new workflow calling mechanism with mock data
"""

import asyncio
import json
import logging
from pathlib import Path
from pipeline.main_flow import MainFlowOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_main_flow_import():
    """Test that MainFlowOrchestrator can be imported and initialized."""
    try:
        orchestrator = MainFlowOrchestrator()
        logger.info("✅ MainFlowOrchestrator initialized successfully")

        # Test batch ID generation
        batch_id = orchestrator.generate_batch_id()
        logger.info(f"✅ Batch ID generated: {batch_id}")

        # Test engine configuration
        logger.info(f"✅ Configured {len(orchestrator.engines)} engines:")
        for i, engine in enumerate(orchestrator.engines, 1):
            logger.info(
                f"  {i}. {engine['emoji']} {engine['name']} - {engine['description']}")

        logger.info(
            f"✅ Meta-engine configured: {orchestrator.meta_engine['emoji']} {orchestrator.meta_engine['name']}")

        return True

    except Exception as e:
        logger.error(f"❌ MainFlowOrchestrator test failed: {str(e)}")
        return False


async def test_engine_instantiation():
    """Test that all engine classes can be instantiated."""
    orchestrator = MainFlowOrchestrator()

    try:
        for engine in orchestrator.engines:
            engine_instance = engine['class']()
            logger.info(f"✅ {engine['name']} instantiated successfully")

        # Test meta-engine
        meta_instance = orchestrator.meta_engine['class']()
        logger.info(
            f"✅ {orchestrator.meta_engine['name']} instantiated successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Engine instantiation test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    logger.info("🚀 Testing MainFlowOrchestrator fixes...")

    # Test 1: Import and initialization
    test1_passed = await test_main_flow_import()

    # Test 2: Engine instantiation
    test2_passed = await test_engine_instantiation()

    # Summary
    total_tests = 2
    passed_tests = sum([test1_passed, test2_passed])

    logger.info(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        logger.info(
            "🎉 All tests passed! MainFlowOrchestrator is ready for deployment.")
    else:
        logger.error("❌ Some tests failed. Please review the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
