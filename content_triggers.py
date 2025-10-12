#!/usr/bin/env python3
"""
Content Analysis Triggers - Quick Reference
Both latest and trending posts analysis triggers
"""

from worker.tasks.content_analysis_task import trigger_content_analysis_latest, trigger_content_analysis_trending
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


def print_usage():
    """Print usage instructions"""
    print("📊 CONTENT ANALYSIS TRIGGERS")
    print("=" * 50)
    print("Available triggers:")
    print("1. Latest Posts Analysis  - python -c \"import asyncio; from worker.tasks.content_analysis_task import trigger_content_analysis_latest; asyncio.run(trigger_content_analysis_latest())\"")
    print("2. Trending Posts Analysis - python -c \"import asyncio; from worker.tasks.content_analysis_task import trigger_content_analysis_trending; asyncio.run(trigger_content_analysis_trending())\"")
    print()
    print("Quick commands:")
    print("Latest:   python trigger_latest.py")
    print("Trending: python trigger_trending_posts.py")
    print()


async def run_both():
    """Run both latest and trending analysis"""
    print("🚀 Running BOTH Content Analysis Triggers")
    print("=" * 60)

    # Run latest first
    print("1️⃣ Starting Latest Posts Analysis...")
    latest_result = await trigger_content_analysis_latest()

    print("\n" + "=" * 60)

    # Run trending second
    print("2️⃣ Starting Trending Posts Analysis...")
    trending_result = await trigger_content_analysis_trending()

    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY:")
    print(
        f"Latest Posts: {'✅ SUCCESS' if latest_result['status'] == 'success' else '❌ FAILED'}")
    print(
        f"Trending Posts: {'✅ SUCCESS' if trending_result['status'] == 'success' else '❌ FAILED'}")

    return {"latest": latest_result, "trending": trending_result}


async def main():
    """Main function"""
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == "latest":
            return await trigger_content_analysis_latest()
        elif action == "trending":
            return await trigger_content_analysis_trending()
        elif action == "both":
            return await run_both()
        else:
            print_usage()
    else:
        print_usage()

if __name__ == "__main__":
    asyncio.run(main())
