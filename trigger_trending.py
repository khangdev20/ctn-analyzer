#!/usr/bin/env python3
"""
Quick trigger for TRENDING content analysis
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def trigger_trending_analysis():
    """Trigger trending content analysis"""
    print("📈 TRENDING CONTENT ANALYSIS")
    print("=" * 50)

    try:
        from worker.tasks.content_analysis_task import ContentAnalysisTask

        task = ContentAnalysisTask()

        # Trending analysis settings
        print(f"📊 Configuration:")
        print(f"   Data source: API (real data)")
        print(f"   Data type: TRENDING 📈")
        print(f"   Posts: 20")
        print(f"   Discord: ✅ ON")

        print(f"\n🔥 Analyzing trending posts...")

        result = await task.run_content_analysis_workflow(
            data_source="api",
            data_type="trending",    # TRENDING posts
            num_posts=20,
            send_discord=True
        )

        print(f"\n🎉 TRENDING ANALYSIS COMPLETE!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Posts analyzed: {result.get('posts_analyzed', 0)}")
        print(
            f"   Discord sent: {'✅ YES' if result.get('discord_sent') else '❌ NO'}")
        print(f"   Processing time: {result.get('processing_time', 0):.1f}s")

        if result.get('s3_path'):
            print(f"   📁 Results saved: {result['s3_path']}")

        return result.get('status') == 'success'

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📈 Trending Content Analysis Trigger")

    success = asyncio.run(trigger_trending_analysis())

    if success:
        print("\n🎉 TRENDING ANALYSIS SUCCESSFUL!")
        print("📱 Check Discord for trending posts analysis with 📈 TRENDING label")
    else:
        print("\n❌ Trending analysis failed!")
