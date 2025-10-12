#!/usr/bin/env python3
"""
Content Analysis Trigger - Latest Posts
Quick trigger for latest posts content analysis
"""

from worker.tasks.content_analysis_task import trigger_content_analysis_latest
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))


async def main():
    """Run latest posts content analysis"""
    print("🚀 Starting Content Analysis - Latest Posts")
    print("=" * 50)

    result = await trigger_content_analysis_latest()

    print("=" * 50)
    if result["status"] == "success":
        print(
            f"✅ SUCCESS: Analyzed {result.get('posts_analyzed', 0)} latest posts")
        print(f"📊 Discord sent: {result.get('discord_sent', False)}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

    return result

if __name__ == "__main__":
    asyncio.run(main())
