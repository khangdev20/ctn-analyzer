#!/usr/bin/env python3
"""
Simple Real Data Test for Leaderboard System
Tests the leaderboard system with actual API data and actions

Usage:
    python test_real_data.py               # Test with live API
    python test_real_data.py --save        # Save snapshot after testing
    python test_real_data.py --compare     # Compare with yesterday's data

Author: AI Assistant
Date: October 8, 2025
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_real_data.log')
    ]
)

logger = logging.getLogger(__name__)

# Import leaderboard components
from worker.tasks.leaderboard_worker import (
    fetch_all_pages,
    normalize_and_rank, 
    compare_snapshots,
    format_discord_message
)
from data_access.leaderboard_store import (
    read_snapshot,
    write_snapshot,
    health_check
)


async def test_real_data_flow(save_snapshot=False, compare_data=False):
    """Test complete real data flow"""
    logger.info("[START] Testing real data flow...")
    
    try:
        # Step 1: Get API URL
        api_url = os.getenv('LEADERBOARD_API_URL', 'https://social.legitreal.com/api/competition/leaderboard/')
        logger.info(f"[API] Using URL: {api_url}")
        
        # Step 2: Fetch real data
        logger.info("[FETCH] Fetching data from API...")
        raw_data, status = fetch_all_pages(api_url)
        
        if not raw_data:
            logger.error(f"[ERROR] Failed to fetch data (status: {status})")
            return False
            
        logger.info(f"[OK] Fetched {len(raw_data)} entries (status: {status})")
        logger.info(f"[SAMPLE] First entry: {raw_data[0] if raw_data else 'None'}")
        
        # Step 3: Process data
        logger.info("[PROCESS] Processing and ranking data...")
        ranked_data = normalize_and_rank(raw_data)
        
        if not ranked_data:
            logger.error("[ERROR] Failed to process data")
            return False
            
        logger.info(f"[OK] Processed {len(ranked_data)} ranked entries")
        logger.info(f"[TOP3] Top 3 entries:")
        for i, entry in enumerate(ranked_data[:3]):
            logger.info(f"   {i+1}. {entry.get('name', 'Unknown')} - Score: {entry.get('score', 0)}")
        
        # Step 4: Save snapshot if requested
        today = datetime.now().strftime('%Y-%m-%d')
        if save_snapshot:
            logger.info(f"[SAVE] Saving snapshot for {today}...")
            save_success = write_snapshot(today, ranked_data)
            if save_success:
                logger.info("[OK] Snapshot saved successfully")
            else:
                logger.warning("[WARNING] Failed to save snapshot")
        
        # Step 5: Compare with yesterday if requested
        if compare_data:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            logger.info(f"[COMPARE] Loading yesterday's data ({yesterday})...")
            
            yesterday_data = read_snapshot(yesterday)
            if yesterday_data:
                logger.info(f"[OK] Loaded {len(yesterday_data)} entries from yesterday")
                
                # Perform comparison
                comparison = compare_snapshots(ranked_data, yesterday_data)
                
                logger.info("[ANALYSIS] Comparison results:")
                logger.info(f"   New entries: {len(comparison.get('new_entries', []))}")
                logger.info(f"   Rank changes: {len(comparison.get('rank_changes', []))}")
                logger.info(f"   Score changes: {len(comparison.get('score_changes', []))}")
                
                # Show some interesting changes
                rank_changes = comparison.get('rank_changes', [])
                if rank_changes:
                    logger.info("[HIGHLIGHTS] Notable rank changes:")
                    for change in rank_changes[:5]:  # Show top 5 changes
                        name = change.get('name', 'Unknown')
                        old_rank = change.get('old_rank', 'N/A')
                        new_rank = change.get('new_rank', 'N/A')
                        logger.info(f"   {name}: {old_rank} -> {new_rank}")
                
                # Format Discord message (but don't send)
                logger.info("[FORMAT] Creating Discord message...")
                message = format_discord_message(ranked_data, comparison)
                
                if message:
                    logger.info("[OK] Discord message created successfully")
                    if isinstance(message, dict) and 'embeds' in message:
                        embed = message['embeds'][0] if message['embeds'] else {}
                        logger.info(f"   Title: {embed.get('title', 'N/A')}")
                        logger.info(f"   Description length: {len(embed.get('description', ''))}")
                        logger.info(f"   Fields: {len(embed.get('fields', []))}")
                else:
                    logger.warning("[WARNING] Failed to create Discord message")
                    
            else:
                logger.info("[INFO] No yesterday data found for comparison")
        
        # Step 6: Show storage health
        logger.info("[HEALTH] Checking storage health...")
        health = health_check()
        logger.info(f"   Status: {health.get('status', 'unknown')}")
        logger.info(f"   Snapshots: {health.get('total_snapshots', 0)}")
        logger.info(f"   Latest: {health.get('latest_snapshot', 'none')}")
        
        logger.info("[SUCCESS] Real data flow test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Real data flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Leaderboard System with Real Data')
    parser.add_argument('--save', action='store_true', help='Save today\'s snapshot')
    parser.add_argument('--compare', action='store_true', help='Compare with yesterday\'s data')
    
    args = parser.parse_args()
    
    logger.info("[TEST] Starting Real Data Test")
    logger.info("=" * 50)
    
    success = await test_real_data_flow(args.save, args.compare)
    
    logger.info("=" * 50)
    if success:
        logger.info("[RESULT] Test completed successfully!")
        return 0
    else:
        logger.error("[RESULT] Test failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)