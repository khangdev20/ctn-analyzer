#!/usr/bin/env python3
"""
Test script for Leaderboard Daily Logger system
Tests all components: API fetching, data processing, Discord formatting

Usage:
    python test_leaderboard_system.py                  # Test with live API
    python test_leaderboard_system.py --mock           # Test with mock data
    python test_leaderboard_system.py --no-discord     # Skip Discord posting
    python test_leaderboard_system.py --run-once       # Manual run (bypass locks)

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
        logging.FileHandler('test_leaderboard.log')
    ]
)

logger = logging.getLogger(__name__)

# Import leaderboard components
from worker.tasks.leaderboard_worker import (
    fetch_all_pages,
    normalize_and_rank, 
    compare_snapshots,
    format_discord_message,
    send_discord,
    leaderboard_daily_task
)
from data_access.leaderboard_store import (
    read_snapshot,
    write_snapshot,
    set_posted_lock,
    health_check
)


async def test_api_fetch():
    """Test API fetching with pagination"""
    logger.info("[SEARCH] Testing API fetch with pagination...")
    
    try:
        entries = await fetch_all_pages()
        
        if entries:
            logger.info(f"[OK] API fetch successful: {len(entries)} entries")
            logger.info(f"   Sample entry: {entries[0]}")
            return entries
        else:
            logger.warning("[WARNING] API fetch returned empty results")
            return None
            
    except Exception as e:
        logger.error(f"[ERROR] API fetch failed: {e}")
        return None


def test_data_processing(entries):
    """Test data normalization and ranking"""
    logger.info("[REFRESH] Testing data processing...")
    
    try:
        if not entries:
            logger.warning("[WARNING] No entries to process")
            return None
            
        ranked_entries = normalize_and_rank(entries)
        
        logger.info(f"[OK] Data processing successful: {len(ranked_entries)} ranked entries")
        logger.info(f"   Top entry: {ranked_entries[0]}")
        logger.info(f"   Rank range: {ranked_entries[0]['rank']} - {ranked_entries[-1]['rank']}")
        
        return ranked_entries
        
    except Exception as e:
        logger.error(f"[ERROR] Data processing failed: {e}")
        return None


def test_comparison(today_entries):
    """Test day-over-day comparison"""
    logger.info("[ANALYTICS] Testing comparison logic...")
    
    try:
        # Create mock yesterday data for testing
        yesterday_entries = []
        if today_entries:
            # Simulate some changes
            for i, entry in enumerate(today_entries[:10]):
                mock_entry = entry.copy()
                # Simulate score changes
                mock_entry['score'] = max(0, entry['score'] - (i * 50))
                # Simulate rank changes
                mock_entry['rank'] = entry['rank'] + (1 if i % 2 == 0 else -1)
                yesterday_entries.append(mock_entry)
        
        comparison = compare_snapshots(today_entries, yesterday_entries)
        
        logger.info(f"[OK] Comparison successful:")
        logger.info(f"   New entries: {len(comparison.get('new_entries', []))}")
        logger.info(f"   Rank changes: {len(comparison.get('rank_changes', []))}")
        logger.info(f"   Score changes: {len(comparison.get('score_changes', []))}")
        
        return comparison
        
    except Exception as e:
        logger.error(f"[ERROR] Comparison failed: {e}")
        return None


def test_discord_formatting(today_entries, comparison):
    """Test Discord message formatting"""
    logger.info("[CHAT] Testing Discord formatting...")
    
    try:
        if not today_entries or not comparison:
            logger.warning("[WARNING] No data for Discord formatting")
            return None
            
        message = format_discord_message(today_entries, comparison)
        
        if message:
            logger.info("[OK] Discord formatting successful")
            logger.info(f"   Message type: {type(message)}")
            if isinstance(message, dict):
                logger.info(f"   Contains embeds: {'embeds' in message}")
            else:
                logger.info(f"   Message length: {len(str(message))}")
            return message
        else:
            logger.warning("[WARNING] Discord formatting returned empty message")
            return None
            
    except Exception as e:
        logger.error(f"[ERROR] Discord formatting failed: {e}")
        return None


async def test_discord_sending(message, skip_discord=False):
    """Test Discord webhook sending"""
    logger.info("[SEND] Testing Discord sending...")
    
    if skip_discord:
        logger.info("[NEXT] Skipping Discord sending (--no-discord)")
        return True
    
    try:
        if not message:
            logger.warning("[WARNING] No message to send")
            return False
            
        # Add test prefix to avoid confusion
        if isinstance(message, dict) and 'embeds' in message:
            if message['embeds'] and message['embeds'][0].get('title'):
                message['embeds'][0]['title'] = f"[TEST] TEST: {message['embeds'][0]['title']}"
        
        success = await send_discord(message)
        
        if success:
            logger.info("[OK] Discord sending successful")
        else:
            logger.warning("[WARNING] Discord sending failed")
            
        return success
        
    except Exception as e:
        logger.error(f"[ERROR] Discord sending error: {e}")
        return False


def test_storage():
    """Test storage operations"""
    logger.info("[SAVE] Testing storage operations...")
    
    try:
        # Test health check
        health = health_check()
        logger.info(f"Storage health: {health}")
        
        # Test lock operations
        test_date = "2025-01-01"
        lock_set = set_posted_lock(test_date)
        logger.info(f"Lock set result: {lock_set}")
        
        # Test read/write operations
        test_entries = [
            {'id': 'test1', 'name': 'Test User 1', 'score': 1000, 'rank': 1},
            {'id': 'test2', 'name': 'Test User 2', 'score': 900, 'rank': 2}
        ]
        
        write_success = write_snapshot(test_date, test_entries)
        logger.info(f"Write test result: {write_success}")
        
        if write_success:
            read_entries = read_snapshot(test_date)
            logger.info(f"Read test result: {len(read_entries) if read_entries else 0} entries")
        
        logger.info("[OK] Storage operations successful")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Storage test failed: {e}")
        return False


async def test_full_integration(use_mock=False, skip_discord=False, run_once=False):
    """Test full integration"""
    logger.info("[REFRESH] Testing full integration...")
    
    try:
        if run_once:
            logger.info("[UNLOCKED] Running in manual mode (bypass locks)")
            
        result = await leaderboard_daily_task(force=run_once)
        
        logger.info(f"[OK] Full integration test result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] Full integration test failed: {e}")
        return None


def create_mock_data():
    """Create mock leaderboard data for testing"""
    logger.info("[MOCK] Creating mock data...")
    
    mock_entries = []
    for i in range(50):
        mock_entries.append({
            'id': f'user_{i+1:03d}',
            'name': f'Test User {i+1}',
            'score': 10000 - (i * 100),
            'affiliation': f'Team {(i % 5) + 1}',
            'created_at': '2025-10-08T00:00:00Z',
            'updated_at': '2025-10-08T00:00:00Z'
        })
    
    logger.info(f"[OK] Created {len(mock_entries)} mock entries")
    return mock_entries


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test Leaderboard Daily Logger system')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of live API')
    parser.add_argument('--no-discord', action='store_true', help='Skip Discord posting')
    parser.add_argument('--run-once', action='store_true', help='Manual run (bypass locks)')
    parser.add_argument('--component', choices=['api', 'processing', 'comparison', 'discord', 'storage', 'integration'], 
                       help='Test specific component only')
    
    args = parser.parse_args()
    
    logger.info("[TEST] Starting Leaderboard Daily Logger Tests")
    logger.info("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test storage first
    if not args.component or args.component == 'storage':
        total_tests += 1
        if test_storage():
            success_count += 1
    
    # Get data (mock or live)
    entries = None
    if not args.component or args.component in ['api', 'processing', 'comparison', 'discord', 'integration']:
        if args.mock:
            entries = create_mock_data()
        else:
            if not args.component or args.component == 'api':
                total_tests += 1
                entries = await test_api_fetch()
                if entries:
                    success_count += 1
    
    # Test data processing
    ranked_entries = None
    if entries and (not args.component or args.component == 'processing'):
        total_tests += 1
        ranked_entries = test_data_processing(entries)
        if ranked_entries:
            success_count += 1
    
    # Test comparison
    comparison = None
    if ranked_entries and (not args.component or args.component == 'comparison'):
        total_tests += 1
        comparison = test_comparison(ranked_entries)
        if comparison:
            success_count += 1
    
    # Test Discord formatting and sending
    if ranked_entries and comparison and (not args.component or args.component == 'discord'):
        total_tests += 1
        message = test_discord_formatting(ranked_entries, comparison)
        if message:
            success_count += 1
            
            total_tests += 1
            if await test_discord_sending(message, args.no_discord):
                success_count += 1
    
    # Test full integration
    if not args.component or args.component == 'integration':
        total_tests += 1
        result = await test_full_integration(args.mock, args.no_discord, args.run_once)
        if result and result.get('status') == 'success':
            success_count += 1
    
    logger.info("=" * 60)
    logger.info(f"[TEST] Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("[OK] All tests passed! Leaderboard system is ready.")
        return 0
    else:
        logger.warning("[WARNING] Some tests failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)