"""
Test Suite for Strategic Intelligence System
Comprehensive testing of strategic intelligence agent and task workflow
"""

from worker.tasks.strategic_intelligence_task import StrategicIntelligenceTask, run_strategic_intelligence_task
from worker.features.strategic_intelligence import StrategicIntelligenceAgent, analyze_strategic_patterns
import asyncio
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStrategicIntelligence(unittest.TestCase):
    """Test suite for Strategic Intelligence functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.agent = StrategicIntelligenceAgent()
        self.task = StrategicIntelligenceTask()
        self.test_batch_id = "test_strategic_batch"

        # Create sample strategic data
        self.sample_posts = self._create_sample_strategic_data()

    def _create_sample_strategic_data(self):
        """Create sample posts with strategic characteristics"""
        posts = []
        base_time = datetime.now(timezone.utc)

        # Sample political/campaign content with different framings
        sample_contents = [
            # Attack framing
            "The corrupt administration has failed our economy completely. This disaster must end!",
            "Lies and scandals have destroyed our trust in government. Time for change!",
            "The incompetent policies are ruining our future. We need new leadership now.",

            # Support framing
            "Amazing progress on job creation! Our successful policies are working for families.",
            "Proud of the excellent achievements in healthcare reform. Great leadership delivers results.",
            "Strong economic growth shows our effective strategy is bringing prosperity.",

            # Call to action
            "Vote for change! Register now and make your voice heard in this election.",
            "Join our campaign! Volunteer, donate, and help spread the message of hope.",
            "Take action today! Contact your representatives and demand better policies.",

            # Emotional appeal
            "Our children deserve a better future. Together we can build hope and opportunity.",
            "Families are struggling with fear and uncertainty. We must unite for justice.",
            "The American dream is under threat. Let's fight for freedom and prosperity.",

            # Themed content
            "Healthcare costs are crushing working families. We need affordable medical care.",
            "Climate change threatens our environment. Time for green energy solutions.",
            "Education funding cuts hurt our students. Investment in schools is critical.",
            "Immigration reform must balance security with compassion for refugees.",
            "Economic inequality grows while the wealthy avoid paying fair taxes."
        ]

        # Sample authors (some coordinated)
        authors = [
            "campaign_smith", "campaign_jones", "policy_expert", "citizen_advocate",
            "reform_now", "future_vote", "team_castillo1", "team_castillo2",
            "progressive_voice", "conservative_view", "independent_mind", "local_activist"
        ]

        for i, content in enumerate(sample_contents):
            # Create timestamp with some coordination patterns
            if "team_castillo" in authors[i % len(authors)]:
                # Coordinated timing for team_castillo members
                hours_offset = 1 + (i % 3) * 0.5  # Close timing
            else:
                hours_offset = i * 2.3  # Spread out timing

            post_time = base_time - timedelta(hours=hours_offset)

            # Generate engagement metrics
            like_count = 50 + (i * 15) + (hash(content) % 100)
            reply_count = 10 + (i * 3) + (hash(content) % 25)
            repost_count = 5 + (i * 2) + (hash(content) % 15)

            post = {
                "id": f"strategic_post_{i:03d}",
                "created_at": post_time.isoformat(),
                "content": content,
                "like_count": like_count,
                "reply_count": reply_count,
                "repost_count": repost_count,
                "author": {
                    "username": authors[i % len(authors)],
                    "follower_count": 1000 + (i * 100)
                },
                "tags": ["politics", "campaign", "election"] if i % 3 == 0 else ["politics"],
                "engagement": {
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "repost_count": repost_count
                },
                "metadata": {
                    "created_at": post_time.isoformat(),
                    "platform": "strategic_test"
                }
            }
            posts.append(post)

        return posts

    def test_strategic_intelligence_core(self):
        """Test core strategic intelligence functionality"""
        print("🧪 Testing Strategic Intelligence Core...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            # Check basic structure
            self.assertIsInstance(result, dict)
            self.assertEqual(result["batch_id"], self.test_batch_id)
            self.assertIn("strategic_summary", result)
            self.assertIn("framing_analysis", result)
            self.assertIn("theme_analysis", result)
            self.assertIn("coordination_analysis", result)
            self.assertIn("emotional_analysis", result)
            self.assertIn("strategic_patterns", result)
            self.assertIn("discord_message", result)

            # Check strategic summary
            summary = result["strategic_summary"]
            self.assertGreater(summary["analyzed_posts"], 0)
            self.assertIsNotNone(summary["dominant_framing"])

            print(f"✅ Analyzed {summary['analyzed_posts']} posts")
            print(f"✅ Dominant framing: {summary['dominant_framing']}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_framing_classification(self):
        """Test content framing classification"""
        print("🧪 Testing Framing Classification...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            framing_analysis = result["framing_analysis"]

            # Check structure
            self.assertIn("framing_counts", framing_analysis)
            self.assertIn("framing_percentages", framing_analysis)
            self.assertIn("dominant_framing", framing_analysis)
            self.assertIn("post_classifications", framing_analysis)

            # Check that we classified posts
            self.assertGreater(framing_analysis["total_analyzed"], 0)

            # Check framing categories exist
            framing_counts = framing_analysis["framing_counts"]
            expected_framings = ["attack", "support",
                                 "call_to_action", "emotional_appeal", "neutral"]
            for framing in expected_framings:
                self.assertIn(framing, framing_counts)

            # Check percentages add up to approximately 100%
            percentages = framing_analysis["framing_percentages"]
            total_percentage = sum(percentages.values())
            self.assertAlmostEqual(total_percentage, 100.0, delta=0.5)

            print(
                f"✅ Classified {len(framing_analysis['post_classifications'])} posts by framing")
            print(
                f"✅ Dominant framing: {framing_analysis['dominant_framing']}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_theme_analysis(self):
        """Test shared theme analysis"""
        print("🧪 Testing Theme Analysis...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            theme_analysis = result["theme_analysis"]

            # Check structure
            self.assertIn("theme_counts", theme_analysis)
            self.assertIn("theme_percentages", theme_analysis)
            self.assertIn("top_themes", theme_analysis)
            self.assertIn("theme_posts", theme_analysis)

            # Check that we found themes
            theme_counts = theme_analysis["theme_counts"]
            self.assertGreater(len(theme_counts), 0)

            # Check top themes
            top_themes = theme_analysis["top_themes"]
            self.assertIsInstance(top_themes, list)

            print(f"✅ Identified {len(theme_counts)} themes")
            print(f"✅ Top themes: {', '.join(top_themes[:3])}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_coordination_detection(self):
        """Test coordinated behavior detection"""
        print("🧪 Testing Coordination Detection...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            coordination_analysis = result["coordination_analysis"]

            # Check structure
            self.assertIn("groups_detected", coordination_analysis)
            self.assertIn("coordination_groups", coordination_analysis)
            self.assertIn("group_analysis", coordination_analysis)
            self.assertIn("total_authors_analyzed", coordination_analysis)

            # Check that we analyzed authors
            self.assertGreater(
                coordination_analysis["total_authors_analyzed"], 0)

            # Check coordination groups format
            coordination_groups = coordination_analysis["coordination_groups"]
            self.assertIsInstance(coordination_groups, list)

            groups_detected = coordination_analysis["groups_detected"]
            print(
                f"✅ Analyzed {coordination_analysis['total_authors_analyzed']} authors")
            print(f"✅ Detected {groups_detected} coordination groups")

            if groups_detected > 0:
                primary_group = coordination_groups[0]
                print(
                    f"✅ Primary group: {primary_group.get('group_name', 'Unknown')}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_emotional_analysis(self):
        """Test emotional strategy analysis"""
        print("🧪 Testing Emotional Analysis...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            emotional_analysis = result["emotional_analysis"]

            # Check structure
            self.assertIn("emotion_scores", emotional_analysis)
            self.assertIn("avg_emotion_score", emotional_analysis)
            self.assertIn("emotion_std_deviation", emotional_analysis)
            self.assertIn("consistency_level", emotional_analysis)
            self.assertIn("emotional_patterns", emotional_analysis)
            self.assertIn("dominant_emotion", emotional_analysis)

            # Check emotion scores
            emotion_scores = emotional_analysis["emotion_scores"]
            self.assertIsInstance(emotion_scores, list)
            self.assertGreater(len(emotion_scores), 0)

            # Check consistency level
            consistency_level = emotional_analysis["consistency_level"]
            self.assertIn(consistency_level, ["High", "Low", "Unknown"])

            # Check emotional patterns
            emotional_patterns = emotional_analysis["emotional_patterns"]
            expected_emotions = ["positive", "negative", "neutral"]
            for emotion in expected_emotions:
                self.assertIn(emotion, emotional_patterns)

            print(
                f"✅ Analyzed {len(emotion_scores)} posts for emotional content")
            print(f"✅ Consistency level: {consistency_level}")
            print(
                f"✅ Dominant emotion: {emotional_analysis['dominant_emotion']}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_strategic_patterns(self):
        """Test strategic pattern identification"""
        print("🧪 Testing Strategic Pattern Identification...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            strategic_patterns = result["strategic_patterns"]

            # Check structure
            self.assertIn("patterns_detected", strategic_patterns)
            self.assertIn("strategic_patterns", strategic_patterns)

            # Check patterns
            patterns_detected = strategic_patterns["patterns_detected"]
            patterns_list = strategic_patterns["strategic_patterns"]

            self.assertIsInstance(patterns_list, list)
            self.assertEqual(len(patterns_list), patterns_detected)

            # Check pattern structure
            for pattern in patterns_list:
                self.assertIn("pattern", pattern)
                self.assertIn("description", pattern)
                self.assertIn("confidence", pattern)

            print(f"✅ Identified {patterns_detected} strategic patterns")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_discord_message_generation(self):
        """Test Discord message formatting"""
        print("🧪 Testing Discord Message Generation...")

        async def run_test():
            result = await self.agent.analyze_strategic_patterns(self.sample_posts, self.test_batch_id)

            discord_message = result["discord_message"]

            # Check message exists and has expected format
            self.assertIsInstance(discord_message, str)
            # Should be substantial
            self.assertGreater(len(discord_message), 100)
            self.assertIn("🧭", discord_message)  # Should have compass emoji
            self.assertIn("Strategic Intelligence Summary", discord_message)

            # Check for key sections
            self.assertIn("Dominant Framing:", discord_message)
            self.assertIn("Common Themes:", discord_message)
            self.assertIn("Detected Campaign Group:", discord_message)
            self.assertIn("Emotional Strategy:", discord_message)

            # Check Discord character limit
            self.assertLessEqual(len(discord_message), 2000)

            print("✅ Discord message generated successfully")
            print(f"✅ Message length: {len(discord_message)} characters")

            return discord_message

        message = asyncio.run(run_test())
        self.assertIsNotNone(message)

    def test_strategic_task_workflow(self):
        """Test complete strategic intelligence task workflow"""
        print("🧪 Testing Strategic Intelligence Task Workflow...")

        # Mock the data collection to use our sample data
        async def mock_collect_data(batch_id):
            return self.sample_posts

        async def run_test():
            # Patch the data collection method
            with patch.object(self.task, '_collect_strategic_data', side_effect=mock_collect_data):
                with patch.object(self.task, '_save_analysis_results', return_value=True):
                    with patch.object(self.task, '_send_discord_notification', return_value=True):
                        result = await self.task.run_strategic_analysis_workflow(self.test_batch_id)

            # Check workflow result structure
            self.assertIsInstance(result, dict)
            self.assertEqual(result["batch_id"], self.test_batch_id)
            self.assertEqual(result["workflow"], "strategic_intelligence")
            self.assertTrue(result["success"])
            self.assertIn("analysis_results", result)
            self.assertTrue(result["has_discord_message"])
            self.assertGreater(result["posts_count"], 0)

            print(f"✅ Workflow completed successfully")
            print(f"✅ Processed {result['posts_count']} posts")
            print(
                f"✅ Discord notification: {result.get('discord_notification_sent', False)}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_empty_data_handling(self):
        """Test handling of empty or insufficient data"""
        print("🧪 Testing Empty Data Handling...")

        async def run_test():
            # Test with empty posts
            result = await self.agent.analyze_strategic_patterns([], self.test_batch_id)

            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("error", False))
            self.assertIn("discord_message", result)

            # Test with insufficient posts
            small_dataset = self.sample_posts[:3]
            result2 = await self.agent.analyze_strategic_patterns(small_dataset, self.test_batch_id)

            # Should still work with small dataset (min is 5, but should handle gracefully)
            self.assertIsInstance(result2, dict)

            print("✅ Empty data handling works correctly")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_standalone_function(self):
        """Test standalone analyze_strategic_patterns function"""
        print("🧪 Testing Standalone Function...")

        async def run_test():
            result = await analyze_strategic_patterns(self.sample_posts, "standalone_strategic_test")

            self.assertIsInstance(result, dict)
            self.assertEqual(result["batch_id"], "standalone_strategic_test")
            self.assertIn("strategic_summary", result)
            self.assertIn("discord_message", result)

            print("✅ Standalone function works correctly")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)


def run_comprehensive_test():
    """Run all strategic intelligence tests"""
    print("🚀 Starting Comprehensive Strategic Intelligence Test Suite")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStrategicIntelligence)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("=" * 60)
    print(f"📊 Test Results Summary:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n⚠️ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success_rate = (result.testsRun - len(result.failures) -
                    len(result.errors)) / result.testsRun * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("🎉 All tests passed! Strategic Intelligence system is ready for deployment.")
    elif success_rate >= 80:
        print("✅ Most tests passed. System is functional with minor issues.")
    else:
        print("⚠️ Multiple test failures. Review system before deployment.")

    return result.wasSuccessful()


async def demo_strategic_intelligence():
    """Demonstrate strategic intelligence capabilities"""
    print("\n🎭 Strategic Intelligence System Demo")
    print("=" * 50)

    # Create demo agent
    agent = StrategicIntelligenceAgent()

    # Create sample data
    test_case = TestStrategicIntelligence()
    test_case.setUp()
    sample_posts = test_case.sample_posts

    print(f"📊 Running analysis on {len(sample_posts)} sample posts...")

    # Run analysis
    result = await agent.analyze_strategic_patterns(sample_posts, "demo_strategic_batch")

    # Display key insights
    print("\n🔍 Key Insights:")

    strategic_summary = result.get("strategic_summary", {})
    print(f"• Posts analyzed: {strategic_summary.get('analyzed_posts', 0)}")
    print(
        f"• Dominant framing: {strategic_summary.get('dominant_framing', 'Unknown')}")

    framing_analysis = result.get("framing_analysis", {})
    if framing_analysis.get("framing_percentages"):
        percentages = framing_analysis["framing_percentages"]
        top_framings = sorted(percentages.items(),
                              key=lambda x: x[1], reverse=True)[:3]
        framing_str = ", ".join(
            [f"{f.replace('_', ' ').title()}: {p}%" for f, p in top_framings])
        print(f"• Framing breakdown: {framing_str}")

    theme_analysis = result.get("theme_analysis", {})
    top_themes = theme_analysis.get("top_themes", [])
    if top_themes:
        print(f"• Top themes: {', '.join(top_themes[:3])}")

    coordination_analysis = result.get("coordination_analysis", {})
    groups_detected = coordination_analysis.get("groups_detected", 0)
    print(f"• Coordination groups detected: {groups_detected}")

    emotional_analysis = result.get("emotional_analysis", {})
    consistency = emotional_analysis.get("consistency_level", "Unknown")
    print(f"• Emotional consistency: {consistency}")

    print("\n📱 Discord Message Preview:")
    print("-" * 40)
    print(result.get("discord_message", "No message generated"))
    print("-" * 40)

    return result


if __name__ == "__main__":
    # Run comprehensive test
    print("Starting Strategic Intelligence Test Suite...")
    success = run_comprehensive_test()

    if success:
        # Run demo if all tests pass
        print("\n" + "=" * 60)
        asyncio.run(demo_strategic_intelligence())

    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Strategic Intelligence Testing Complete")
