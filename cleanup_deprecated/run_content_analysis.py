"""
Content Analysis Trigger
Quick script to run content analysis independently
"""
import asyncio
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from worker.tasks.content_analysis_task import ContentAnalysisTask


async def main():
    """Run content analysis workflow"""
    print("🤖 Starting Content Analysis Workflow")
    print("=" * 50)
    
    task = ContentAnalysisTask()
    
    # Ask user for data source
    print("Choose data source:")
    print("1. API (real trending data)")
    print("2. Mock (test data)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    data_source = "api" if choice == "1" else "mock"
    
    print(f"Using {data_source} data source...")
    
    # Run the analysis
    result = await task.run_content_analysis_workflow(
        data_source=data_source,
        num_posts=15
    )
    
    print("\n" + "=" * 50)
    print("🏁 CONTENT ANALYSIS RESULTS")
    print("=" * 50)
    
    print(f"Status: {result['status']}")
    print(f"Batch ID: {result['batch_id']}")
    print(f"Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
    
    if result['status'] == 'success':
        print(f"Posts Collected: {result['total_posts_collected']}")
        print(f"Posts Analyzed: {result['posts_analyzed']}")
        print(f"Discord Sent: {'✅' if result['discord_sent'] else '❌'}")
        
        summary = result.get('analysis_summary', {})
        if summary:
            print(f"\n📊 ANALYSIS SUMMARY:")
            print(f"  Avg Readability: {summary.get('avg_readability', 0):.1f}/100")
            print(f"  Avg Content Quality: {summary.get('avg_content_quality', 0):.1f}/100")
            print(f"  Dominant Sentiment: {summary.get('dominant_sentiment', 'unknown')}")
            print(f"  Top Emotions: {', '.join(summary.get('top_emotions', [])[:3])}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())