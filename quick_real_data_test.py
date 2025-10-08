#!/usr/bin/env python3
"""
Quick Real Data Test - Main Flow with Actual Trending Data
Fast test using real data from trending_data JSON files
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from pipeline.main_flow import MainFlowOrchestrator

async def quick_real_data_test():
    """Quick test with real data."""
    
    print("🌐 QUICK REAL DATA TEST")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # 1. Load real data
        print("📥 Loading real trending data...")
        trending_files = list(Path(".").glob("trending_data_*.json"))
        latest_file = sorted(trending_files, reverse=True)[0]
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            real_data = json.load(f)
        
        posts_count = len(real_data.get('data', []))
        total_engagement = sum(
            post.get('like_count', 0) + post.get('reply_count', 0) + post.get('repost_count', 0)
            for post in real_data.get('data', [])
        )
        
        print(f"✅ Loaded {posts_count} real posts from {latest_file}")
        print(f"💫 Total engagement: {total_engagement:,}")
        
        # 2. Run main flow
        print("\n🚀 Running main flow with real data...")
        orchestrator = MainFlowOrchestrator(unified_reporting=True)
        result = await orchestrator.run_main_flow()
        
        execution_time = time.time() - start_time
        
        # 3. Show results
        if result.get('status') == 'success':
            print(f"\n✅ SUCCESS!")
            print(f"⏱️  Time: {execution_time:.1f}s")
            print(f"🎯 Engines: {result.get('successful_engines', 0)}/{result.get('total_engines', 0)}")
            print(f"🆔 Batch: {result.get('batch_id')}")
            
            # Show engine results
            if 'engine_results' in result:
                print("\n📊 Engine Results:")
                for engine_result in result['engine_results']:
                    status = "✅" if engine_result['success'] else "❌"
                    print(f"   {status} {engine_result['engine']}: {engine_result['execution_time']:.1f}s")
            
            print("\n🎉 REAL DATA PROCESSING COMPLETE!")
            print("💬 Check Discord for real insights")
            
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n💥 ERROR: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing main flow with REAL trending data...")
    success = asyncio.run(quick_real_data_test())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")