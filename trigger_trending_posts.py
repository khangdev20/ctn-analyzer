#!/usr/bin/env python3
"""
Content Analysis Trigger - Trending Posts
Quick trigger for trending posts content analysis
"""

from worker.tasks.content_analysis_task import trigger_content_analysis_trending
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


async def main():
    """Run trending posts content analysis"""
    print("🔥 Starting Content Analysis - Trending Posts")
    print("=" * 50)

    result = await trigger_content_analysis_trending()

    print("=" * 50)
    if result["status"] == "success":
        print(
            f"✅ SUCCESS: Analyzed {result.get('posts_analyzed', 0)} trending posts")
        print(f"📊 Discord sent: {result.get('discord_sent', False)}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

    return result

if __name__ == "__main__":
    asyncio.run(main())
