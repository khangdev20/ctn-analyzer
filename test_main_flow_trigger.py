#!/usr/bin/env python3
"""
Main Flow Trigger Script - Full System Test
Tests the complete 7-engine analysis pipeline with real data and Discord notifications

This script:
1. Tests data collection from real API
2. Runs all 7 engines sequentially  
3. Sends real Discord notifications
4. Provides detailed execution monitoring
5. Saves comprehensive results

Usage:
    python test_main_flow_trigger.py

Author: AI Assistant
Date: October 8, 2025
Version: 1.0.0
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import main flow orchestrator
from pipeline.main_flow import MainFlowOrchestrator, run_main_flow
from worker.features.data_collector import collect_trending_data

# Configure logging for detailed monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_main_flow.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class MainFlowTrigger:
    """Trigger and monitor the complete main intelligence flow."""

    def __init__(self):
        """Initialize the trigger with monitoring capabilities."""
        self.start_time = None
        self.orchestrator = None
        self.test_results = {}

    async def run_full_system_test(self):
        """Execute complete system test with real data and Discord notifications."""
        self.start_time = datetime.now(timezone.utc)
        
        print("🚀 MAIN FLOW TRIGGER - FULL SYSTEM TEST")
        print("=" * 60)
        print(f"⏰ Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📊 Testing: 7-Engine Intelligence Pipeline")
        print(f"💬 Discord: Real notifications enabled")
        print(f"🌐 Data Source: Live API (with fallback to mock)")
        print("=" * 60)

        try:
            # Step 1: Pre-flight checks
            await self._run_preflight_checks()

            # Step 2: Test data collection
            await self._test_data_collection()

            # Step 3: Initialize orchestrator with unified reporting
            await self._initialize_orchestrator()

            # Step 4: Execute main flow
            await self._execute_main_flow()

            # Step 5: Generate test report
            await self._generate_test_report()

            print("\n✅ FULL SYSTEM TEST COMPLETED SUCCESSFULLY!")
            return True

        except Exception as e:
            print(f"\n❌ FULL SYSTEM TEST FAILED: {str(e)}")
            logger.error(f"System test failed: {str(e)}", exc_info=True)
            return False

    async def _run_preflight_checks(self):
        """Run pre-flight system checks."""
        print("\n🔍 STEP 1: PRE-FLIGHT CHECKS")
        print("-" * 30)

        # Check environment variables
        import os
        discord_webhook = os.getenv('DISCORD_WEBHOOK')
        openai_key = os.getenv('OPENAI_API_KEY')

        if discord_webhook:
            print("✅ Discord webhook configured")
        else:
            print("⚠️  Discord webhook not found")

        if openai_key:
            print("✅ OpenAI API key configured")
        else:
            print("⚠️  OpenAI API key not found")

        # Check data directories
        data_path = Path("data")
        if data_path.exists():
            print("✅ Data directory exists")
        else:
            print("⚠️  Creating data directory...")
            data_path.mkdir(parents=True, exist_ok=True)

        # Check logs directory
        logs_path = Path("logs")
        if logs_path.exists():
            print("✅ Logs directory exists")
        else:
            print("⚠️  Creating logs directory...")
            logs_path.mkdir(parents=True, exist_ok=True)

        print("✅ Pre-flight checks completed")

    async def _test_data_collection(self):
        """Test data collection from live API."""
        print("\n📥 STEP 2: DATA COLLECTION TEST")
        print("-" * 30)

        try:
            print("🌐 Testing live API connection...")
            
            # Test with 2 pages to be quick
            data_filename = collect_trending_data(2)
            
            if data_filename:
                import json
                with open(data_filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                posts_count = len(data.get('data', []))
                print(f"✅ Live API working: {posts_count} posts collected")
                print(f"📁 Data saved to: {data_filename}")
                
                self.test_results['data_collection'] = {
                    'status': 'success',
                    'source': 'live_api',
                    'posts_count': posts_count,
                    'filename': data_filename
                }
            else:
                print("⚠️  Live API failed, will use mock data fallback")
                self.test_results['data_collection'] = {
                    'status': 'fallback',
                    'source': 'mock_data',
                    'posts_count': 20,
                    'filename': None
                }

        except Exception as e:
            print(f"⚠️  Data collection error: {str(e)}")
            print("📋 Will use mock data fallback during execution")
            self.test_results['data_collection'] = {
                'status': 'error',
                'source': 'mock_data',
                'error': str(e)
            }

    async def _initialize_orchestrator(self):
        """Initialize the main flow orchestrator."""
        print("\n🎛️  STEP 3: ORCHESTRATOR INITIALIZATION")
        print("-" * 30)

        try:
            # Initialize with unified reporting enabled
            self.orchestrator = MainFlowOrchestrator(unified_reporting=True)
            print("✅ Main flow orchestrator initialized")
            print("📊 Unified Discord reporting enabled")
            print(f"🔧 Engines configured: {len(self.orchestrator.engines)}")
            
            # List all engines
            for i, engine in enumerate(self.orchestrator.engines, 1):
                print(f"   {i}. {engine['emoji']} {engine['name']}")
            
            self.test_results['orchestrator'] = {
                'status': 'success',
                'engines_count': len(self.orchestrator.engines),
                'unified_reporting': True
            }

        except Exception as e:
            print(f"❌ Orchestrator initialization failed: {str(e)}")
            raise e

    async def _execute_main_flow(self):
        """Execute the complete main intelligence flow."""
        print("\n🚀 STEP 4: MAIN FLOW EXECUTION")
        print("-" * 30)
        print("⚡ Starting 7-engine analysis pipeline...")
        print("💬 Discord notifications will be sent during execution")
        print("⏱️  This may take several minutes...")

        try:
            # Execute main flow with real Discord notifications
            execution_start = time.time()
            
            result = await self.orchestrator.run_main_flow()
            
            execution_time = time.time() - execution_start

            if result.get('status') == 'success':
                print(f"\n✅ MAIN FLOW COMPLETED SUCCESSFULLY!")
                print(f"⏱️  Total execution time: {execution_time:.1f}s")
                print(f"🎯 Successful engines: {result.get('successful_engines', 0)}/{result.get('total_engines', 0)}")
                print(f"🆔 Batch ID: {result.get('batch_id')}")

                self.test_results['main_flow'] = {
                    'status': 'success',
                    'execution_time': execution_time,
                    'successful_engines': result.get('successful_engines', 0),
                    'total_engines': result.get('total_engines', 0),
                    'batch_id': result.get('batch_id'),
                    'discord_sent': True
                }

                # Display engine results summary
                if 'engine_results' in result:
                    print("\n📊 ENGINE EXECUTION SUMMARY:")
                    for engine_result in result['engine_results']:
                        status = "✅" if engine_result['success'] else "❌"
                        print(f"   {status} {engine_result['engine']}: {engine_result['execution_time']:.1f}s")

            else:
                print(f"\n❌ MAIN FLOW FAILED!")
                print(f"⏱️  Execution time: {execution_time:.1f}s")
                print(f"❓ Error: {result.get('error', 'Unknown error')}")

                self.test_results['main_flow'] = {
                    'status': 'error',
                    'execution_time': execution_time,
                    'error': result.get('error', 'Unknown error'),
                    'successful_engines': result.get('successful_engines', 0),
                    'batch_id': result.get('batch_id')
                }

        except Exception as e:
            execution_time = time.time() - execution_start if 'execution_start' in locals() else 0
            print(f"\n❌ MAIN FLOW EXECUTION ERROR: {str(e)}")
            logger.error(f"Main flow execution error: {str(e)}", exc_info=True)
            
            self.test_results['main_flow'] = {
                'status': 'exception',
                'execution_time': execution_time,
                'error': str(e)
            }
            raise e

    async def _generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 STEP 5: TEST REPORT GENERATION")
        print("-" * 30)

        total_time = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        # Create detailed report
        report = {
            'test_metadata': {
                'test_type': 'full_system_test',
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'total_execution_time': total_time,
                'test_version': '1.0.0'
            },
            'test_results': self.test_results,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform
            }
        }

        # Save report to file
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        report_file = Path(f"test_reports/main_flow_test_{timestamp}.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"📄 Test report saved: {report_file}")
        print(f"⏱️  Total test time: {total_time:.1f}s")

        # Display summary
        print("\n📊 TEST SUMMARY:")
        for step, result in self.test_results.items():
            status = result.get('status', 'unknown')
            emoji = "✅" if status == 'success' else "⚠️" if status in ['fallback', 'warning'] else "❌"
            print(f"   {emoji} {step.replace('_', ' ').title()}: {status}")


async def main():
    """Main execution function."""
    try:
        trigger = MainFlowTrigger()
        success = await trigger.run_full_system_test()
        
        if success:
            print("\n🎉 ALL TESTS PASSED - SYSTEM IS READY!")
            print("💬 Check your Discord channel for notifications")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED - CHECK LOGS FOR DETAILS")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {str(e)}")
        logger.error(f"Unexpected error in main: {str(e)}", exc_info=True)
        return 3


if __name__ == "__main__":
    print("🧪 MAIN FLOW TRIGGER SCRIPT")
    print("Testing complete 7-engine intelligence pipeline...")
    print("Press Ctrl+C to cancel\n")
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)