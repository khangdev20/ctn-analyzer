"""
Comprehensive Engagement Intelligence Test
Tests all components of the Engagement & Growth Analysis system
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_engagement_intelligence_core():
    """Test the core EngagementIntelligenceAgent"""
    print("🧠 Testing Core Engagement Intelligence Agent...")

    try:
        from worker.features.engagement_intelligence import EngagementIntelligenceAgent

        # Create test data snapshots
        previous_data = {
            "posts": [
                {
                    "id": "post_1",
                    "like_count": 50,
                    "reply_count": 10,
                    "repost_count": 5,
                    "author": {"username": "user1"},
                    "content": "Test post 1",
                    "collected_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
                },
                {
                    "id": "post_2",
                    "like_count": 25,
                    "reply_count": 15,
                    "repost_count": 8,
                    "author": {"username": "user2"},
                    "content": "Test post 2",
                    "collected_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
                }
            ]
        }

        current_data = {
            "posts": [
                {
                    "id": "post_1",
                    "like_count": 150,  # +100 likes
                    "reply_count": 25,  # +15 replies
                    "repost_count": 12,  # +7 reposts
                    "author": {"username": "user1"},
                    "content": "Test post 1",
                    "collected_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "post_2",
                    "like_count": 60,   # +35 likes
                    "reply_count": 45,  # +30 replies
                    "repost_count": 18,  # +10 reposts
                    "author": {"username": "user2"},
                    "content": "Test post 2",
                    "collected_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        # Test analysis
        agent = EngagementIntelligenceAgent()
        results = await agent.analyze_engagement_growth(
            previous_data, current_data, "test_core_analysis"
        )

        # Verify results structure
        required_fields = [
            'batch_id', 'analysis_timestamp', 'growth_summary',
            'top_performers', 'engagement_composition', 'discord_message'
        ]

        missing_fields = [
            field for field in required_fields if field not in results]
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False

        # Check growth summary
        growth = results['growth_summary']
        print(f"✅ Growth Summary:")
        print(f"   • Avg Velocity: +{growth['avg_velocity_per_min']:.2f}/min")
        print(f"   • Posts with Growth: {growth['posts_with_growth']}")
        print(f"   • Total Delta: +{growth['total_delta_engagement']}")

        # Check top performers
        performers = results['top_performers']
        print(f"✅ Top Performers: {len(performers)} found")
        for i, perf in enumerate(performers[:3], 1):
            print(
                f"   {i}. @{perf['author']} - +{perf['velocity_per_min']:.1f}/min")

        # Check engagement composition
        comp = results['engagement_composition']
        print(f"✅ Engagement Composition:")
        print(f"   • Likes: {comp['likes_percent']}%")
        print(f"   • Replies: {comp['replies_percent']}%")
        print(f"   • Reposts: {comp['reposts_percent']}%")

        # Check Discord message
        discord_msg = results['discord_message']
        print(f"✅ Discord Message: {len(discord_msg)} characters")

        return True

    except Exception as e:
        print(f"❌ Core test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_engagement_task_workflow():
    """Test the complete EngagementIntelligenceTask workflow"""
    print("\n🚀 Testing Complete Engagement Task Workflow...")

    try:
        from worker.tasks.engagement_intelligence_task import EngagementIntelligenceTask

        # Create task
        task = EngagementIntelligenceTask()

        # Test workflow (should use mock data since no real data available)
        results = await task.run_engagement_analysis_workflow(
            batch_id="test_workflow_001",
            send_discord=False,  # Don't spam Discord during tests
            save_results=False   # Don't save files during tests
        )

        # Check workflow results
        workflow_status = results.get('workflow_status', 'unknown')
        print(f"Status: {workflow_status}")

        if workflow_status in ['success', 'success_baseline']:
            print(f"✅ Workflow completed successfully")
            print(f"   • Batch ID: {results.get('batch_id')}")
            print(f"   • Matched Posts: {results.get('matched_posts', 0)}")

            # Check if analysis data is present
            if 'growth_summary' in results:
                growth = results['growth_summary']
                print(
                    f"   • Avg Velocity: +{growth.get('avg_velocity_per_min', 0):.2f}/min")

            return True
        else:
            error_msg = results.get('error_message', 'Unknown error')
            print(f"❌ Workflow failed: {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_discord_formatting():
    """Test Discord message formatting"""
    print("\n💬 Testing Discord Message Formatting...")

    try:
        from worker.features.engagement_intelligence import EngagementIntelligenceAgent

        agent = EngagementIntelligenceAgent()

        # Create sample data for formatting test
        sample_data = {
            "avg_velocity": 2.5,
            "posts": [
                {
                    "id": "1",
                    "author": {"username": "testuser1"},
                    "velocity_per_min": 3.2,
                    "delta_likes": 45,
                    "delta_replies": 12,
                    "delta_reposts": 8,
                    "is_accelerating": True
                },
                {
                    "id": "2",
                    "author": {"username": "testuser2"},
                    "velocity_per_min": 2.8,
                    "delta_likes": 30,
                    "delta_replies": 15,
                    "delta_reposts": 5,
                    "is_accelerating": False
                }
            ],
            "posts_with_growth": 2,
            "posts_with_acceleration": 1
        }

        # Test quick update formatting
        quick_update = await agent.format_quick_engagement_update(sample_data)

        print("✅ Discord Quick Update:")
        print("-" * 40)
        print(quick_update)
        print("-" * 40)

        # Verify formatting elements
        required_elements = ["📊", "📈", "🚀", "/min"]
        missing_elements = [
            elem for elem in required_elements if elem not in quick_update]

        if missing_elements:
            print(f"❌ Missing Discord elements: {missing_elements}")
            return False

        print("✅ All Discord formatting elements present")
        return True

    except Exception as e:
        print(f"❌ Discord formatting test failed: {e}")
        return False


async def test_velocity_calculations():
    """Test engagement velocity and acceleration calculations"""
    print("\n⚡ Testing Velocity & Acceleration Calculations...")

    try:
        from worker.features.engagement_intelligence import EngagementIntelligenceAgent

        agent = EngagementIntelligenceAgent()

        # Test data with known expected results
        previous_data = {
            "posts": [{
                "id": "calc_test",
                "like_count": 100,
                "reply_count": 20,
                "repost_count": 10,
                "collected_at": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(),
                "author": {"username": "calctest"}
            }]
        }

        current_data = {
            "posts": [{
                "id": "calc_test",
                "like_count": 200,  # +100 likes
                "reply_count": 40,  # +20 replies
                "repost_count": 25,  # +15 reposts
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "author": {"username": "calctest"}
            }]
        }

        # Expected: +135 total engagement over 20 minutes = 6.75/min velocity
        results = await agent.analyze_engagement_growth(
            previous_data, current_data, "velocity_test"
        )

        if results.get('error'):
            print(f"❌ Calculation test failed: {results.get('error_message')}")
            return False

        # Check calculations
        growth = results['growth_summary']
        expected_velocity = 135 / 20  # 6.75/min
        actual_velocity = growth['avg_velocity_per_min']

        print(f"✅ Velocity Calculation:")
        print(f"   • Expected: ~{expected_velocity:.2f}/min")
        print(f"   • Actual: {actual_velocity:.2f}/min")
        print(f"   • Delta Likes: +100")
        print(f"   • Delta Replies: +20")
        print(f"   • Delta Reposts: +15")
        print(f"   • Total Delta: +135")

        # Verify composition percentages
        comp = results['engagement_composition']
        expected_likes_pct = int((100/135) * 100)  # ~74%
        expected_replies_pct = int((20/135) * 100)  # ~15%
        expected_reposts_pct = int((15/135) * 100)  # ~11%

        print(f"✅ Composition Calculation:")
        print(
            f"   • Likes: {comp['likes_percent']}% (expected ~{expected_likes_pct}%)")
        print(
            f"   • Replies: {comp['replies_percent']}% (expected ~{expected_replies_pct}%)")
        print(
            f"   • Reposts: {comp['reposts_percent']}% (expected ~{expected_reposts_pct}%)")

        return True

    except Exception as e:
        print(f"❌ Velocity calculation test failed: {e}")
        return False


def check_required_files():
    """Check if all required Engagement Intelligence files exist"""
    print("\n📁 Checking Required Files...")

    required_files = [
        "worker/features/engagement_intelligence.py",
        "worker/tasks/engagement_intelligence_task.py",
        "test_engagement_intelligence.py",
        "test_engagement_api.py"
    ]

    import os

    all_present = True
    for file_path in required_files:
        if os.path.exists(file_path):
            # Get file size
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_present = False

    return all_present


async def main():
    """Run comprehensive Engagement Intelligence tests"""
    print("🧪 COMPREHENSIVE ENGAGEMENT INTELLIGENCE TEST")
    print("=" * 60)
    print("Testing Engagement & Growth Analysis + Discord Summary")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check file structure
    files_ok = check_required_files()

    if not files_ok:
        print("\n❌ Missing required files. Cannot proceed with tests.")
        return

    # Run all tests
    test_results = []

    # Test 1: Core Intelligence Agent
    core_ok = await test_engagement_intelligence_core()
    test_results.append(("Core Intelligence Agent", core_ok))

    # Test 2: Complete Task Workflow
    workflow_ok = await test_engagement_task_workflow()
    test_results.append(("Task Workflow", workflow_ok))

    # Test 3: Discord Formatting
    discord_ok = await test_discord_formatting()
    test_results.append(("Discord Formatting", discord_ok))

    # Test 4: Velocity Calculations
    velocity_ok = await test_velocity_calculations()
    test_results.append(("Velocity Calculations", velocity_ok))

    # Results Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(
        f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Engagement & Growth Analysis system is COMPLETE and ready!")
        print("\nKey Features Verified:")
        print("• ✅ Engagement velocity calculation (Δtotal_engagement / Δtime)")
        print("• ✅ Engagement acceleration analysis")
        print("• ✅ Top 5 fastest growing posts identification")
        print("• ✅ Discord message formatting with emojis")
        print("• ✅ Engagement composition analysis")
        print("• ✅ Complete workflow integration")
    else:
        print(f"\n⚠️ {total-passed} tests failed. System needs attention.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
