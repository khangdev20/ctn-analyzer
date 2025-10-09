#!/usr/bin/env python3
"""
High Impact Mock Leaderboard Test - Demonstrates significant ranking changes
Shows dramatic leaderboard movements and new entries
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


def generate_dramatic_leaderboard_changes(base_data: List[Dict]) -> List[Dict]:
    """Generate dramatic changes to demonstrate comparison logic"""

    entries = [entry.copy() for entry in base_data]
    logger.info("🎪 Creating DRAMATIC leaderboard changes...")

    # 1. Boost some low-ranking users significantly
    low_performers = [e for e in entries if e['score'] < 500]
    if low_performers:
        boost_user = random.choice(low_performers)
        boost_amount = random.randint(800, 1200)
        boost_user['score'] += boost_amount
        logger.info(
            f"   🚀 MAJOR BOOST: {boost_user['name']} +{boost_amount} points!")

    # 2. Drop some high performers
    top_performers = [e for e in entries if e['score'] > 800]
    if len(top_performers) >= 2:
        drop_users = random.sample(top_performers, 2)
        for user in drop_users:
            drop_amount = random.randint(300, 600)
            user['score'] -= drop_amount
            logger.info(
                f"   📉 MAJOR DROP: {user['name']} -{drop_amount} points!")

    # 3. Add several new high-performing entries
    new_entries = []
    for i in range(3):
        new_id = 300 + i
        new_score = random.randint(700, 1100)
        new_entry = {
            "id": new_id,
            "name": f"RocketUser_{new_id}",
            "affiliation": random.choice(["TeamA", "TeamB", "TeamC"]),
            "score": new_score,
            "created_at": "2025-10-09T14:00:00Z"
        }
        new_entries.append(new_entry)
        logger.info(
            f"   🌟 NEW HIGH PERFORMER: {new_entry['name']} with {new_score} points!")

    entries.extend(new_entries)

    # 4. Remove some middle performers (dropouts)
    middle_performers = [e for e in entries if 400 <= e['score'] <= 600]
    if len(middle_performers) >= 2:
        dropouts = random.sample(middle_performers, 2)
        for dropout in dropouts:
            logger.info(
                f"   💨 DROPOUT: {dropout['name']} ({dropout['score']} points)")
            entries.remove(dropout)

    # 5. Give moderate changes to remaining users
    for entry in entries:
        if entry['id'] < 300:  # Original entries only
            change = random.choice([
                random.randint(20, 80),   # 40% moderate increase
                -random.randint(10, 40),  # 40% moderate decrease
                0, 0                      # 20% no change
            ])
            entry['score'] += change
            if change > 50:
                logger.info(f"   📈 Good gain: {entry['name']} +{change}")
            elif change < -20:
                logger.info(f"   📉 Notable drop: {entry['name']} {change}")

    return entries


async def test_dramatic_leaderboard_comparison():
    """Test with dramatic changes to showcase comparison features"""

    try:
        from worker.tasks.leaderboard_worker import (
            normalize_and_rank, compare_snapshots,
            format_bidaily_discord_message, send_discord
        )
        import os
        import pytz

        logger.info("🎪 DRAMATIC LEADERBOARD CHANGES TEST")
        logger.info("=" * 60)

        webhook_url = os.getenv(
            'LEADERBOARD_DISCORD_WEBHOOK', os.getenv('DISCORD_WEBHOOK', ''))
        brisbane_tz = pytz.timezone('Australia/Brisbane')

        # === SNAPSHOT 1: Initial Stable Data ===
        logger.info("📊 Creating initial stable leaderboard...")
        time1 = datetime.now(brisbane_tz)

        # Create predictable initial data
        initial_data = []
        for i in range(12):
            score = 1000 - (i * 60) + random.randint(-10, 10)
            initial_data.append({
                "id": 100 + i,
                "name": f"User_{chr(65+i)}",  # User_A, User_B, etc.
                "affiliation": f"Team{(i % 3)+1}",
                "score": score,
                "created_at": f"2025-10-0{(i % 9)+1}T10:00:00Z"
            })

        entries1 = normalize_and_rank(initial_data)

        logger.info(f"✅ Initial snapshot: {len(entries1)} entries")
        logger.info("🏆 Initial top 5:")
        for i in range(min(5, len(entries1))):
            entry = entries1[i]
            logger.info(
                f"   #{i+1} {entry['name']} — {entry['score']:,} points")

        # Send initial snapshot
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
                f"🎪 DRAMATIC TEST — Initial Stable State ({time1.strftime('%H:%M AEST')})"
            )

            test_header1 = f"""🎪 **DRAMATIC LEADERBOARD CHANGES TEST**
📊 **Phase 1:** Stable initial state with {len(entries1)} entries
🎭 **Coming next:** Major ranking shake-ups!

"""
            message1 = test_header1 + message1

            result1 = send_discord(message1, webhook_url)
            logger.info(
                f"📱 Initial message sent: {result1.get('success', False)}")

        # === SIMULATE DRAMATIC CHANGES ===
        logger.info("⏳ Preparing dramatic changes...")
        await asyncio.sleep(3)

        logger.info("🎪 Generating DRAMATIC leaderboard changes...")
        time2 = datetime.now(brisbane_tz)

        changed_data = generate_dramatic_leaderboard_changes(initial_data)
        entries2 = normalize_and_rank(changed_data)

        logger.info(f"✅ Dramatic snapshot: {len(entries2)} entries")
        logger.info("🏆 NEW top 5 after changes:")
        for i in range(min(5, len(entries2))):
            entry = entries2[i]
            logger.info(
                f"   #{i+1} {entry['name']} — {entry['score']:,} points")

        # === COMPARISON ===
        logger.info("🔍 Analyzing dramatic changes...")
        comparison2 = compare_snapshots(entries2, entries1)

        logger.info("🎉 DRAMATIC RESULTS:")
        logger.info(
            f"   🏆 Leaders (top 10): {len(comparison2.get('leaders_top10', []))}")
        logger.info(f"   🚀 Movers up: {len(comparison2.get('movers_up', []))}")
        logger.info(
            f"   📉 Movers down: {len(comparison2.get('movers_down', []))}")
        logger.info(
            f"   🌟 New entries: {len(comparison2.get('new_entries', []))}")
        logger.info(f"   💨 Dropouts: {len(comparison2.get('dropouts', []))}")

        # Show top movers
        movers_up = comparison2.get('movers_up', [])
        if movers_up:
            logger.info("🚀 BIGGEST CLIMBERS:")
            for mover in sorted(movers_up, key=lambda x: x['rank_delta'])[:3]:
                logger.info(
                    f"   🎯 {mover['name']}: #{mover['previous_rank']} → #{mover['rank']} (↑{mover['rank_delta']} positions!)")

        movers_down = comparison2.get('movers_down', [])
        if movers_down:
            logger.info("📉 BIGGEST FALLERS:")
            for mover in sorted(movers_down, key=lambda x: x['rank_delta'], reverse=True)[:3]:
                logger.info(
                    f"   📉 {mover['name']}: #{mover['previous_rank']} → #{mover['rank']} (↓{abs(mover['rank_delta'])} positions)")

        new_entries = comparison2.get('new_entries', [])
        if new_entries:
            logger.info("🌟 NEW HIGH PERFORMERS:")
            for entry in sorted(new_entries, key=lambda x: x['rank'])[:3]:
                logger.info(
                    f"   ⭐ {entry['name']}: Debuts at #{entry['rank']} with {entry['score']:,} points!")

        # Send dramatic results
        if webhook_url:
            elapsed = time2 - time1
            message2 = format_bidaily_discord_message(
                time2.strftime("%Y-%m-%d_%H-%M"),
                comparison2,
                "complete",
                f"🎪 DRAMATIC TEST — Major Shake-up! ({time2.strftime('%H:%M AEST')})"
            )

            test_header2 = f"""🎪 **DRAMATIC LEADERBOARD CHANGES — RESULTS!**
🚀 **Major movements:** {len(movers_up)} climbers, {len(movers_down)} fallers
🌟 **New stars:** {len(new_entries)} debut entries
💨 **Departures:** {len(comparison2.get('dropouts', []))} dropouts
⏱️ **Analysis time:** {elapsed.total_seconds():.1f}s

"""
            message2 = test_header2 + message2

            result2 = send_discord(message2, webhook_url)
            logger.info(
                f"📱 Dramatic results sent: {result2.get('success', False)}")

        # === SAVE DETAILED RESULTS ===
        test_results = {
            'test_type': 'dramatic_leaderboard_comparison',
            'test_description': 'High-impact changes to demonstrate comparison logic',
            'snapshots': {
                'initial': {
                    'time': time1.isoformat(),
                    'entries_count': len(entries1),
                    'top_5': [
                        {
                            'name': entries1[i]['name'],
                            'rank': i+1,
                            'score': entries1[i]['score'],
                            'affiliation': entries1[i]['affiliation']
                        }
                        for i in range(min(5, len(entries1)))
                    ]
                },
                'dramatic': {
                    'time': time2.isoformat(),
                    'entries_count': len(entries2),
                    'top_5': [
                        {
                            'name': entries2[i]['name'],
                            'rank': i+1,
                            'score': entries2[i]['score'],
                            'affiliation': entries2[i]['affiliation']
                        }
                        for i in range(min(5, len(entries2)))
                    ]
                }
            },
            'dramatic_changes': {
                'total_movers_up': len(movers_up),
                'total_movers_down': len(movers_down),
                'new_entries': len(new_entries),
                'dropouts': len(comparison2.get('dropouts', [])),
                'biggest_climbers': [
                    {
                        'name': m['name'],
                        'from_rank': m['previous_rank'],
                        'to_rank': m['rank'],
                        'positions_gained': m['rank_delta'],
                        'score': m['score']
                    } for m in sorted(movers_up, key=lambda x: x['rank_delta'])[:5]
                ],
                'biggest_fallers': [
                    {
                        'name': m['name'],
                        'from_rank': m['previous_rank'],
                        'to_rank': m['rank'],
                        'positions_lost': abs(m['rank_delta']),
                        'score': m['score']
                    } for m in sorted(movers_down, key=lambda x: x['rank_delta'], reverse=True)[:5]
                ],
                'new_high_performers': [
                    {
                        'name': e['name'],
                        'debut_rank': e['rank'],
                        'score': e['score'],
                        'affiliation': e['affiliation']
                    } for e in sorted(new_entries, key=lambda x: x['rank'])[:5]
                ]
            },
            'test_completed': datetime.now().isoformat()
        }

        # Save results
        reports_dir = Path("test_reports")
        reports_dir.mkdir(exist_ok=True)
        test_file = reports_dir / \
            f"dramatic_leaderboard_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_file, 'w') as f:
            json.dump(test_results, f, indent=2)

        logger.info(f"💾 Detailed results saved: {test_file}")

        print("=" * 60)
        print("🎉 DRAMATIC LEADERBOARD COMPARISON TEST COMPLETED!")
        print(f"📊 Entries: {len(entries1)} → {len(entries2)}")
        print(f"🚀 Major climbers: {len(movers_up)}")
        print(f"📉 Major fallers: {len(movers_down)}")
        print(f"🌟 New debuts: {len(new_entries)}")
        print(f"💨 Dropouts: {len(comparison2.get('dropouts', []))}")
        print(f"💾 Results: {test_file}")
        if webhook_url:
            print("📱 Check Discord for dramatic comparison messages!")
        print("")
        print("🎯 KEY FEATURES DEMONSTRATED:")
        print("   ✅ Dramatic rank changes detection")
        print("   ✅ New high-performer entries")
        print("   ✅ Dropout detection")
        print("   ✅ 'Since last report' comparison logic")
        print("   ✅ Rich Discord formatting")
        print("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Dramatic test error: {str(e)}", exc_info=True)
        print(f"💥 ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎪 DRAMATIC LEADERBOARD CHANGES TEST")
    print("🚀 Showcases major ranking movements and new entries")
    print("🎯 Demonstrates all comparison features")
    print("=" * 60)

    result = asyncio.run(test_dramatic_leaderboard_comparison())
    sys.exit(0 if result else 1)
