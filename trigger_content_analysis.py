#!/usr/bin/env python3
"""
Content Analysis Trigger Script
Quick way to run content analysis manually
"""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def trigger_content_analysis():
    """Trigger content analysis workflow"""
    print("🚀 TRIGGERING CONTENT ANALYSIS")
    print("=" * 50)

    try:
        # Method 1: Direct Content Analysis Task
        print("📊 Method 1: Direct Content Analysis Task")
        from worker.tasks.content_analysis_task import ContentAnalysisTask

        task = ContentAnalysisTask()
        print("✅ ContentAnalysisTask created")

        # Configuration - you can modify these
        DATA_SOURCE = "api"        # "api" for real data, "mock" for test
        DATA_TYPE = "trending"     # "latest" or "trending"
        NUM_POSTS = 15             # Number of posts to analyze
        SEND_DISCORD = True        # Send to Discord

        print(f"📊 Configuration:")
        print(f"   Data source: {DATA_SOURCE}")
        print(
            f"   Data type: {DATA_TYPE.upper()} {'🆕' if DATA_TYPE == 'latest' else '📈' if DATA_TYPE == 'trending' else '🧪'}")
        print(f"   Posts: {NUM_POSTS}")
        print(f"   Discord: {'✅ ON' if SEND_DISCORD else '❌ OFF'}")

        # Run with configured settings
        print(f"\n🔥 Running content analysis...")
        result = await task.run_content_analysis_workflow(
            data_source=DATA_SOURCE,
            data_type=DATA_TYPE,
            num_posts=NUM_POSTS,
            send_discord=SEND_DISCORD
        )

        if result.get("status") == "success":
            print(f"✅ Content analysis completed successfully!")
            print(f"📊 Processed: {result.get('posts_analyzed', 0)} posts")
            print(f"⏱️  Duration: {result.get('processing_time', 0):.1f}s")
            print(
                f"📨 Discord: {'Sent' if result.get('discord_sent') else 'Failed'}")

            if result.get('analysis_results', {}).get('aggregate_metrics'):
                metrics = result['analysis_results']['aggregate_metrics']
                print(f"\n📈 Key Metrics:")
                print(
                    f"   - Avg sentiment: {metrics.get('avg_sentiment_score', 0):.2f}")
                print(
                    f"   - Avg quality: {metrics.get('avg_content_quality', 0):.1f}/100")
                print(
                    f"   - Dominant emotion: {metrics.get('dominant_emotion', 'N/A')}")
        else:
            print(
                f"❌ Content analysis failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error triggering content analysis: {e}")
        import traceback
        traceback.print_exc()


async def trigger_main_flow_content_analysis():
    """Trigger content analysis via main flow pipeline"""
    print("\n🔄 TRIGGERING VIA MAIN FLOW PIPELINE")
    print("=" * 50)

    try:
        from pipeline.main_flow import MainFlowOrchestrator

        # Create orchestrator
        orchestrator = MainFlowOrchestrator(unified_reporting=True)
        print("✅ MainFlowOrchestrator created")

        # Run full pipeline (includes content analysis + trending prediction)
        print("\n🚀 Running full intelligence pipeline...")
        result = await orchestrator.run_complete_flow()

        if result:
            print("✅ Main flow pipeline completed successfully!")
            print("📊 Content analysis was part of the full pipeline")
        else:
            print("❌ Main flow pipeline failed")

    except Exception as e:
        print(f"❌ Error with main flow: {e}")


def show_menu():
    """Show trigger options"""
    print("\n🎯 CONTENT ANALYSIS TRIGGER OPTIONS")
    print("=" * 50)
    print("1. 📊 Direct Content Analysis (standalone)")
    print("2. 🔄 Full Main Flow Pipeline (with content analysis)")
    print("3. 🧪 Quick Test (mock data)")
    print("4. ❌ Exit")
    return input("\nSelect option (1-4): ").strip()


async def trigger_quick_test():
    """Quick test with mock data"""
    print("\n🧪 QUICK TEST WITH MOCK DATA")
    print("=" * 50)

    try:
        from worker.tasks.content_analysis_task import ContentAnalysisTask

        task = ContentAnalysisTask()

        # Run with mock data (faster, no API calls)
        result = await task.run_content_analysis_workflow(
            data_source="mock",     # Use mock data
            num_posts=10,          # Analyze 10 posts
            send_discord=False     # Skip Discord for test
        )

        if result.get("status") == "success":
            print(f"✅ Quick test completed!")
            print(f"📊 Processed: {result.get('posts_analyzed', 0)} posts")
            print(f"⏱️  Duration: {result.get('processing_time', 0):.1f}s")
        else:
            print(f"❌ Quick test failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ Quick test error: {e}")


async def main():
    """Main trigger interface"""
    print(
        f"🕐 Content Analysis Trigger - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        choice = show_menu()

        if choice == "1":
            await trigger_content_analysis()
        elif choice == "2":
            await trigger_main_flow_content_analysis()
        elif choice == "3":
            await trigger_quick_test()
        elif choice == "4":
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Please select 1-4.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())
