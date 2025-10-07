"""
Main Flow Orchestrator Demo
Demonstrates the complete 7-engine pipeline with Discord reporting

This is a simplified demo that shows how the orchestrator works.
For production use, the system will be run via the scheduler in worker/scheduler.py

Usage: python demo_main_flow.py

Author: AI Assistant
Date: October 7, 2025
"""

import asyncio
import logging
from datetime import datetime

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def demo_main_flow():
    """Demonstrate the main flow orchestrator."""

    print("🚀 MAIN FLOW ORCHESTRATOR - DEMO")
    print("=" * 60)
    print(f"⏰ Demo Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Import the orchestrator
        from pipeline.main_flow import run_main_flow

        print("📋 Executing Main Intelligence Flow...")
        print("🎯 This will run all 7 analysis engines sequentially:")
        print("   1. Data Collection")
        print("   2. Content Analysis Engine")
        print("   3. Engagement Intelligence Engine")
        print("   4. Network Intelligence Engine")
        print("   5. Temporal Analytics Engine")
        print("   6. Strategic Intelligence Engine")
        print("   7. Trending Prediction Engine")
        print("\n🚀 Starting execution...")
        print("-" * 60)

        # Execute the main flow
        result = await run_main_flow()

        print("-" * 60)
        print("📊 EXECUTION RESULTS:")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Batch ID: {result.get('batch_id', 'N/A')}")
        print(
            f"Execution Time: {result.get('execution_time_seconds', 0):.2f} seconds")
        print(
            f"Successful Engines: {result.get('successful_engines', 0)}/{result.get('total_engines', 7)}")

        if result.get('status') == 'success':
            print("\n✅ DEMO COMPLETED SUCCESSFULLY!")
            print("🎉 All engines executed successfully with Discord reporting")
            print("📈 System is ready for production deployment")
        else:
            print(f"\n⚠️ DEMO COMPLETED WITH ISSUES")
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            print("🔧 Check individual engine implementations")

        # Show engine results if available
        engine_results = result.get('engine_results', [])
        if engine_results:
            print(f"\n📋 INDIVIDUAL ENGINE RESULTS:")
            for engine_result in engine_results:
                engine_name = engine_result.get('engine', 'Unknown')
                success = engine_result.get('success', False)
                exec_time = engine_result.get('execution_time', 0)
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} {engine_name}: {exec_time:.2f}s")

    except Exception as e:
        print(f"❌ DEMO FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"⏰ Demo Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


async def demo_scheduler_info():
    """Show scheduler configuration information."""

    print("\n📅 SCHEDULER CONFIGURATION INFO")
    print("=" * 40)

    print("🚀 Main Flow Orchestrator: Every 15 minutes")
    print("   - Complete 7-engine sequential pipeline")
    print("   - Discord reporting after each engine")
    print("   - Comprehensive execution summary")

    print("\n⚡ Individual Engine Scheduling:")
    engines = [
        ("Content Analysis", "12 minutes"),
        ("Engagement Intelligence", "18 minutes"),
        ("Network Intelligence", "20 minutes"),
        ("Temporal Analytics", "22 minutes"),
        ("Strategic Intelligence", "25 minutes"),
        ("Trending Prediction", "10 minutes")
    ]

    for engine_name, interval in engines:
        print(f"   • {engine_name}: Every {interval}")

    print("\n📅 Weekly Meta-Trend Analysis: Sunday 2 AM UTC")
    print("   - Comprehensive cross-engine analysis")
    print("   - Weekly trend calendar generation")
    print("   - Long-term pattern identification")

    print("\n🧹 System Maintenance: Every 30 minutes")
    print("   - Cleanup stuck tasks")
    print("   - Resource optimization")

    print("\n🎯 Total Scheduled Jobs: 9")
    print("✅ Dual-mode operation: Orchestrated + Individual")


if __name__ == "__main__":
    async def main():
        """Run the demo."""
        await demo_main_flow()
        await demo_scheduler_info()

        print("\n🚀 To start the production system, run:")
        print("   python run.py")
        print("\n📊 To monitor the system, check:")
        print("   - Flask API: http://localhost:5000/status")
        print("   - Discord notifications (if configured)")
        print("   - Log files: bot.log")

    asyncio.run(main())
