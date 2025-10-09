#!/usr/bin/env python3
"""
Mock Leaderboard Comparison Test - Demonstrates comparison logic with simulated data
Shows how leaderboard changes are detected and reported
"""

import asyncio
import json
import logging
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_mock_leaderboard(base_data: List[Dict] = None, simulate_changes: bool = False) -> List[Dict]:
    """Generate mock leaderboard data with optional changes"""

    if base_data is None:
        # Generate initial leaderboard
        users = [
            {"id": 101, "name": "Alice", "affiliation": "TeamA"},
            {"id": 102, "name": "Bob", "affiliation": "TeamB"},
            {"id": 103, "name": "Charlie", "affiliation": "TeamC"},
            {"id": 104, "name": "Diana", "affiliation": "TeamA"},
            {"id": 105, "name": "Eve", "affiliation": "TeamB"},
            {"id": 106, "name": "Frank", "affiliation": "TeamC"},
            {"id": 107, "name": "Grace", "affiliation": "TeamA"},
            {"id": 108, "name": "Henry", "affiliation": "TeamB"},
            {"id": 109, "name": "Ivy", "affiliation": "TeamC"},
            {"id": 110, "name": "Jack", "affiliation": "TeamA"},
            {"id": 111, "name": "Kate", "affiliation": "TeamB"},
            {"id": 112, "name": "Leo", "affiliation": "TeamC"},
            {"id": 113, "name": "Maya", "affiliation": "TeamA"},
            {"id": 114, "name": "Nick", "affiliation": "TeamB"},
            {"id": 115, "name": "Olivia", "affiliation": "TeamC"},
        ]

        # Assign initial scores
        entries = []
        for i, user in enumerate(users):
            score = 1000 - (i * 50) + random.randint(-20, 20)
            entries.append({
                "id": user["id"],
                "name": user["name"],
                "affiliation": user["affiliation"],
                "score": score,
                "created_at": f"2025-10-0{i % 9+1}T10:00:00Z"
            })

        return entries

    else:
        # Simulate changes to existing data
        entries = [entry.copy() for entry in base_data]

        if simulate_changes:
            logger.info("🎲 Simulating leaderboard changes...")

            # Simulate score changes (some increase, some decrease)
            for entry in entries:
                change = random.choice([
                    0, 0, 0, 0, 0,  # 50% no change
                    random.randint(5, 50),   # 25% increase
                    -random.randint(5, 30),  # 25% decrease
                ])
                entry["score"] += change
                if change > 0:
                    logger.info(f"   📈 {entry['name']}: +{change} points")
                elif change < 0:
                    logger.info(f"   📉 {entry['name']}: {change} points")

            # Simulate new entries (10% chance)
            if random.random() < 0.3:
                new_user_id = 200 + random.randint(1, 50)
                new_entry = {
                    "id": new_user_id,
                    "name": f"NewUser_{new_user_id}",
                    "affiliation": random.choice(["TeamA", "TeamB", "TeamC"]),
                    "score": random.randint(200, 800),
                    "created_at": "2025-10-09T12:00:00Z"
                }
                entries.append(new_entry)
                logger.info(
                    f"   🆕 New entry: {new_entry['name']} with {new_entry['score']} points")

            # Simulate dropouts (5% chance per user)
            original_count = len(entries)
            entries = [entry for entry in entries if random.random() > 0.05]
            dropped_count = original_count - len(entries)
            if dropped_count > 0:
                logger.info(f"   📤 {dropped_count} entries dropped out")

        return entries


async def test_mock_leaderboard_comparison():
    """Test leaderboard comparison logic with mock data"""

    try:
        from worker.tasks.leaderboard_worker import (
            normalize_and_rank, compare_snapshots,
            format_bidaily_discord_message, send_discord
        )
        import os
        import pytz

        logger.info("🎭 MOCK LEADERBOARD COMPARISON TEST")
        logger.info("=" * 60)

        webhook_url = os.getenv(
            'LEADERBOARD_DISCORD_WEBHOOK', os.getenv('DISCORD_WEBHOOK', ''))
        brisbane_tz = pytz.timezone('Australia/Brisbane')

        # === SNAPSHOT 1: Initial Data ===
        logger.info("📊 Generating initial leaderboard...")
        time1 = datetime.now(brisbane_tz)

        raw_data1 = generate_mock_leaderboard()
        entries1 = normalize_and_rank(raw_data1)

        logger.info(f"✅ Initial snapshot: {len(entries1)} entries")
        logger.info("🏆 Top 5 initial leaders:")
        for i in range(min(5, len(entries1))):
            entry = entries1[i]
            logger.info(
                f"   #{i+1} {entry['name']} — {entry['score']:,} points")

        # Send initial snapshot message
        if webhook_url:
            comparison1 = {
                'leaders_top10': entries1[:10],
                'movers_up': [],
                'movers_down': [],
                'new_entries': [],
                'dropouts': [],
                'total_today': len(entries1),
                'total_previous': 0,
                'is_first_run': True
            }

            message1 = format_bidaily_discord_message(
                time1.strftime("%Y-%m-%d_%H-%M"),
                comparison1,
                "complete",
                f"🎭 MOCK TEST — Initial Snapshot ({time1.strftime('%H:%M AEST')})"
            )

            test_header1 = f"""🎭 **MOCK LEADERBOARD COMPARISON TEST**
📊 **Phase 1:** Initial snapshot with {len(entries1)} entries
⏳ **Next:** Will simulate changes and compare

"""
            message1 = test_header1 + message1

            result1 = send_discord(message1, webhook_url)
            logger.info(
                f"📱 Initial message sent: {result1.get('success', False)}")

        # === WAIT AND SIMULATE CHANGES ===
        logger.info("⏳ Simulating time passage and changes...")
        await asyncio.sleep(3)  # Short wait for demo

        # === SNAPSHOT 2: Changed Data ===
        logger.info("🔄 Generating changed leaderboard...")
        time2 = datetime.now(brisbane_tz)

        raw_data2 = generate_mock_leaderboard(
            base_data=raw_data1, simulate_changes=True)
        entries2 = normalize_and_rank(raw_data2)

        logger.info(f"✅ Updated snapshot: {len(entries2)} entries")

        # === COMPARISON ===
        logger.info("🔍 Comparing snapshots...")
        comparison2 = compare_snapshots(entries2, entries1)

        logger.info("📊 Comparison results:")
        logger.info(
            f"   🏆 Leaders (top 10): {len(comparison2.get('leaders_top10', []))}")
        logger.info(f"   📈 Movers up: {len(comparison2.get('movers_up', []))}")
        logger.info(
            f"   📉 Movers down: {len(comparison2.get('movers_down', []))}")
        logger.info(
            f"   🆕 New entries: {len(comparison2.get('new_entries', []))}")
        logger.info(f"   📤 Dropouts: {len(comparison2.get('dropouts', []))}")

        # Log detailed changes
        movers_up = comparison2.get('movers_up', [])
        if movers_up:
            logger.info("📈 Users who moved up:")
            for mover in movers_up[:5]:
                logger.info(
                    f"   • {mover['name']}: #{mover['previous_rank']} → #{mover['rank']} (↑{mover['rank_delta']})")

        movers_down = comparison2.get('movers_down', [])
        if movers_down:
            logger.info("📉 Users who moved down:")
            for mover in movers_down[:5]:
                logger.info(
                    f"   • {mover['name']}: #{mover['previous_rank']} → #{mover['rank']} (↓{abs(mover['rank_delta'])})")

        new_entries = comparison2.get('new_entries', [])
        if new_entries:
            logger.info("🆕 New entries:")
            for entry in new_entries:
                logger.info(
                    f"   • {entry['name']}: #{entry['rank']} with {entry['score']:,} points")

        dropouts = comparison2.get('dropouts', [])
        if dropouts:
            logger.info("📤 Dropouts:")
            for dropout in dropouts:
                logger.info(
                    f"   • {dropout['name']}: was #{dropout['previous_rank']} with {dropout['previous_score']:,} points")

        # Send comparison message
        if webhook_url:
            elapsed = time2 - time1
            message2 = format_bidaily_discord_message(
                time2.strftime("%Y-%m-%d_%H-%M"),
                comparison2,
                "complete",
                f"🎭 MOCK TEST — Changes Detected ({time2.strftime('%H:%M AEST')})"
            )

            test_header2 = f"""🎭 **MOCK LEADERBOARD COMPARISON — RESULTS**
📊 **Changes:** {len(movers_up)} up, {len(movers_down)} down, {len(new_entries)} new, {len(dropouts)} out
⏱️ **Simulation time:** {elapsed.total_seconds():.1f}s

"""
            message2 = test_header2 + message2

            result2 = send_discord(message2, webhook_url)
            logger.info(
                f"📱 Comparison message sent: {result2.get('success', False)}")

        # === SAVE RESULTS ===
        test_results = {
            'test_type': 'mock_leaderboard_comparison',
            'snapshots': {
                'initial': {
                    'time': time1.isoformat(),
                    'entries_count': len(entries1),
                    'top_5': [
                        {'name': entries1[i]['name'], 'rank': i +
                            1, 'score': entries1[i]['score']}
                        for i in range(min(5, len(entries1)))
                    ]
                },
                'updated': {
                    'time': time2.isoformat(),
                    'entries_count': len(entries2),
                    'top_5': [
                        {'name': entries2[i]['name'], 'rank': i +
                            1, 'score': entries2[i]['score']}
                        for i in range(min(5, len(entries2)))
                    ]
                }
            },
            'comparison_results': {
                'leaders_count': len(comparison2.get('leaders_top10', [])),
                'movers_up_count': len(comparison2.get('movers_up', [])),
                'movers_down_count': len(comparison2.get('movers_down', [])),
                'new_entries_count': len(comparison2.get('new_entries', [])),
                'dropouts_count': len(comparison2.get('dropouts', [])),
                'movers_up_details': [
                    {
                        'name': m['name'],
                        'from_rank': m['previous_rank'],
                        'to_rank': m['rank'],
                        'rank_change': m['rank_delta']
                    } for m in comparison2.get('movers_up', [])
                ],
                'movers_down_details': [
                    {
                        'name': m['name'],
                        'from_rank': m['previous_rank'],
                        'to_rank': m['rank'],
                        'rank_change': m['rank_delta']
                    } for m in comparison2.get('movers_down', [])
                ]
            },
            'test_completed': datetime.now().isoformat()
        }

        # Save test results
        reports_dir = Path("test_reports")
        reports_dir.mkdir(exist_ok=True)
        test_file = reports_dir / \
            f"mock_leaderboard_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_file, 'w') as f:
            json.dump(test_results, f, indent=2)

        logger.info(f"💾 Test results saved: {test_file}")

        print("=" * 60)
        print("🎉 MOCK LEADERBOARD COMPARISON TEST COMPLETED!")
        print(f"📊 Entries: {len(entries1)} → {len(entries2)}")
        print(f"📈 Changes: {len(movers_up)} up, {len(movers_down)} down")
        print(f"🆕 New: {len(new_entries)}, Dropouts: {len(dropouts)}")
        print(f"💾 Results: {test_file}")
        if webhook_url:
            print("📱 Check Discord for test messages")
        print("🔍 This demonstrates the new comparison logic:")
        print("   - Compares with most recent previous report")
        print("   - Detects rank changes, new entries, and dropouts")
        print("   - Uses '(since last report)' terminology")
        print("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Test error: {str(e)}", exc_info=True)
        print(f"💥 ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎭 MOCK LEADERBOARD COMPARISON TEST")
    print("📊 Demonstrates new comparison logic with simulated data")
    print("⚡ Quick test - no waiting required")
    print("=" * 60)

    result = asyncio.run(test_mock_leaderboard_comparison())
    sys.exit(0 if result else 1)
