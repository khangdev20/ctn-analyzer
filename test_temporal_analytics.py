"""
Test Suite for Temporal Analytics System
Comprehensive testing of temporal analytics agent and task workflow
"""

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

from worker.features.temporal_analytics import TemporalAnalyticsAgent, analyze_temporal_patterns
from worker.tasks.temporal_analytics_task import TemporalAnalyticsTask, run_temporal_analytics_task


class TestTemporalAnalytics(unittest.TestCase):
    """Test suite for Temporal Analytics functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.agent = TemporalAnalyticsAgent()
        self.task = TemporalAnalyticsTask()
        self.test_batch_id = "test_temporal_batch"
        
        # Create sample temporal data
        self.sample_posts = self._create_sample_temporal_data()

    def _create_sample_temporal_data(self):
        """Create sample posts with temporal characteristics"""
        posts = []
        base_time = datetime.now(timezone.utc)
        
        # Create posts across different hours and days
        for i in range(50):
            # Vary posting times across hours and days
            hours_offset = (i * 3.7) % 168  # Spread across a week
            post_time = base_time - timedelta(hours=hours_offset)
            
            # Simulate engagement patterns based on posting time
            hour = post_time.hour
            day = post_time.weekday()
            
            # Higher engagement during peak hours (17-19) and weekdays
            base_engagement = 50
            if 17 <= hour <= 19:  # Peak hours
                base_engagement *= 2.5
            elif 12 <= hour <= 14:  # Lunch time
                base_engagement *= 1.5
            elif 9 <= hour <= 11:  # Morning
                base_engagement *= 1.3
            
            if day < 5:  # Weekdays
                base_engagement *= 1.4
            
            # Add randomization
            engagement_variation = 0.3 + (i % 5) * 0.2
            total_engagement = int(base_engagement * engagement_variation)
            
            like_count = int(total_engagement * 0.6)
            reply_count = int(total_engagement * 0.25)
            repost_count = int(total_engagement * 0.15)
            
            post = {
                "id": f"post_{i:03d}",
                "created_at": post_time.isoformat(),
                "content": f"Sample post content {i} with some text that varies in length",
                "like_count": like_count,
                "reply_count": reply_count,
                "repost_count": repost_count,
                "author": {
                    "username": f"user_{i % 10}",
                    "follower_count": 1000 + (i * 50)
                },
                "tags": ["trending", "test"] if i % 3 == 0 else ["test"],
                "engagement": {
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "repost_count": repost_count
                },
                "metadata": {
                    "created_at": post_time.isoformat(),
                    "platform": "test_platform"
                }
            }
            posts.append(post)
        
        return posts

    def test_temporal_analytics_core(self):
        """Test core temporal analytics functionality"""
        print("🧪 Testing Temporal Analytics Core...")
        
        async def run_test():
            result = await self.agent.analyze_temporal_patterns(self.sample_posts, self.test_batch_id)
            
            # Check basic structure
            self.assertIsInstance(result, dict)
            self.assertEqual(result["batch_id"], self.test_batch_id)
            self.assertIn("temporal_summary", result)
            self.assertIn("hourly_patterns", result)
            self.assertIn("daily_patterns", result)
            self.assertIn("optimal_times", result)
            self.assertIn("discord_message", result)
            
            # Check temporal summary
            summary = result["temporal_summary"]
            self.assertGreater(summary["total_posts"], 0)
            self.assertGreater(summary["time_span_hours"], 0)
            
            print(f"✅ Analyzed {summary['total_posts']} posts over {summary['time_span_hours']:.1f} hours")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_hourly_pattern_analysis(self):
        """Test hourly pattern analysis"""
        print("🧪 Testing Hourly Pattern Analysis...")
        
        async def run_test():
            result = await self.agent.analyze_temporal_patterns(self.sample_posts, self.test_batch_id)
            
            hourly_patterns = result["hourly_patterns"]
            
            # Check structure
            self.assertIn("hourly_stats", hourly_patterns)
            self.assertIn("best_hours", hourly_patterns)
            self.assertIn("optimal_ranges", hourly_patterns)
            
            # Check that we found some best hours
            self.assertGreater(len(hourly_patterns["best_hours"]), 0)
            
            # Check hourly stats has 24 entries
            self.assertEqual(len(hourly_patterns["hourly_stats"]), 24)
            
            # Verify peak hour is valid
            peak_hour = hourly_patterns.get("peak_hour")
            if peak_hour is not None:
                self.assertGreaterEqual(peak_hour, 0)
                self.assertLessEqual(peak_hour, 23)
            
            print(f"✅ Found {len(hourly_patterns['best_hours'])} optimal hours")
            print(f"✅ Detected {len(hourly_patterns['optimal_ranges'])} time ranges")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_daily_pattern_analysis(self):
        """Test daily pattern analysis"""
        print("🧪 Testing Daily Pattern Analysis...")
        
        async def run_test():
            result = await self.agent.analyze_temporal_patterns(self.sample_posts, self.test_batch_id)
            
            daily_patterns = result["daily_patterns"]
            
            # Check structure
            self.assertIn("daily_stats", daily_patterns)
            self.assertIn("best_days", daily_patterns)
            self.assertIn("best_day_names", daily_patterns)
            
            # Check that we found some best days
            self.assertGreater(len(daily_patterns["best_days"]), 0)
            
            # Check daily stats has 7 entries
            self.assertEqual(len(daily_patterns["daily_stats"]), 7)
            
            # Verify day names are valid
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day_name in daily_patterns["best_day_names"]:
                self.assertIn(day_name, valid_days)
            
            print(f"✅ Found {len(daily_patterns['best_days'])} optimal days")
            print(f"✅ Best days: {', '.join(daily_patterns['best_day_names'][:3])}")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_time_to_trend_analysis(self):
        """Test time-to-trend analysis"""
        print("🧪 Testing Time-to-Trend Analysis...")
        
        async def run_test():
            result = await self.agent.analyze_temporal_patterns(self.sample_posts, self.test_batch_id)
            
            trend_analysis = result["trend_analysis"]
            
            # Check structure
            self.assertIn("trending_posts_count", trend_analysis)
            self.assertIn("avg_time_to_trend_minutes", trend_analysis)
            self.assertIn("momentum_data", trend_analysis)
            
            # Check reasonable values
            if trend_analysis["trending_posts_count"] > 0:
                self.assertGreater(trend_analysis["avg_time_to_trend_minutes"], 0)
                self.assertLess(trend_analysis["avg_time_to_trend_minutes"], 600)  # Less than 10 hours
            
            print(f"✅ Analyzed {trend_analysis['trending_posts_count']} trending posts")
            if trend_analysis["avg_time_to_trend_minutes"] > 0:
                print(f"✅ Average time to trend: {trend_analysis['avg_time_to_trend_minutes']:.1f} minutes")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_momentum_duration_analysis(self):
        """Test momentum duration analysis"""
        print("🧪 Testing Momentum Duration Analysis...")
        
        async def run_test():
            result = await self.agent.analyze_temporal_patterns(self.sample_posts, self.test_batch_id)
            
            momentum_analysis = result["momentum_analysis"]
            
            # Check structure
            self.assertIn("analyzed_posts", momentum_analysis)
            self.assertIn("avg_momentum_duration_hours", momentum_analysis)
            self.assertIn("momentum_durations", momentum_analysis)
            
            # Check reasonable values
            if momentum_analysis["analyzed_posts"] > 0:
                self.assertGreater(momentum_analysis["avg_momentum_duration_hours"], 0)
                self.assertLess(momentum_analysis["avg_momentum_duration_hours"], 48)  # Less than 2 days
            
            print(f"✅ Analyzed momentum for {momentum_analysis['analyzed_posts']} posts")
            if momentum_analysis["avg_momentum_duration_hours"] > 0:
                print(f"✅ Average momentum duration: {momentum_analysis['avg_momentum_duration_hours']:.1f} hours")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_discord_message_generation(self):
        """Test Discord message formatting"""
        print("🧪 Testing Discord Message Generation...")
        
        async def run_test():
            result = await self.agent.analyze_temporal_patterns(self.sample_posts, self.test_batch_id)
            
            discord_message = result["discord_message"]
            
            # Check message exists and has expected format
            self.assertIsInstance(discord_message, str)
            self.assertGreater(len(discord_message), 100)  # Should be substantial
            self.assertIn("⏰", discord_message)  # Should have clock emoji
            self.assertIn("Temporal Analysis Report", discord_message)
            
            # Check for key sections
            self.assertIn("Best Days:", discord_message)
            self.assertIn("Optimal Hours:", discord_message)
            self.assertIn("Time-to-Trend:", discord_message)
            self.assertIn("Momentum Duration:", discord_message)
            self.assertIn("💡", discord_message)  # Should have tip
            
            # Check Discord character limit
            self.assertLessEqual(len(discord_message), 2000)
            
            print("✅ Discord message generated successfully")
            print(f"✅ Message length: {len(discord_message)} characters")
            
            return discord_message
        
        message = asyncio.run(run_test())
        self.assertIsNotNone(message)

    def test_temporal_task_workflow(self):
        """Test complete temporal analytics task workflow"""
        print("🧪 Testing Temporal Analytics Task Workflow...")
        
        # Mock the data collection to use our sample data
        async def mock_collect_data(batch_id):
            return self.sample_posts
        
        async def run_test():
            # Patch the data collection method
            with patch.object(self.task, '_collect_temporal_data', side_effect=mock_collect_data):
                with patch.object(self.task, '_save_analysis_results', return_value=True):
                    with patch.object(self.task, '_send_discord_notification', return_value=True):
                        result = await self.task.run_temporal_analysis_workflow(self.test_batch_id)
            
            # Check workflow result structure
            self.assertIsInstance(result, dict)
            self.assertEqual(result["batch_id"], self.test_batch_id)
            self.assertEqual(result["workflow"], "temporal_analytics")
            self.assertTrue(result["success"])
            self.assertIn("analysis_results", result)
            self.assertTrue(result["has_discord_message"])
            self.assertGreater(result["posts_count"], 0)
            
            print(f"✅ Workflow completed successfully")
            print(f"✅ Processed {result['posts_count']} posts")
            print(f"✅ Discord notification: {result.get('discord_notification_sent', False)}")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_empty_data_handling(self):
        """Test handling of empty or insufficient data"""
        print("🧪 Testing Empty Data Handling...")
        
        async def run_test():
            # Test with empty posts
            result = await self.agent.analyze_temporal_patterns([], self.test_batch_id)
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("error", False))
            self.assertIn("discord_message", result)
            
            # Test with insufficient posts
            small_dataset = self.sample_posts[:5]
            result2 = await self.agent.analyze_temporal_patterns(small_dataset, self.test_batch_id)
            
            # Should still work with small dataset
            self.assertIsInstance(result2, dict)
            
            print("✅ Empty data handling works correctly")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_standalone_function(self):
        """Test standalone analyze_temporal_patterns function"""
        print("🧪 Testing Standalone Function...")
        
        async def run_test():
            result = await analyze_temporal_patterns(self.sample_posts, "standalone_test")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["batch_id"], "standalone_test")
            self.assertIn("temporal_summary", result)
            self.assertIn("discord_message", result)
            
            print("✅ Standalone function works correctly")
            
            return result
        
        result = asyncio.run(run_test())
        self.assertIsNotNone(result)


def run_comprehensive_test():
    """Run all temporal analytics tests"""
    print("🚀 Starting Comprehensive Temporal Analytics Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTemporalAnalytics)
    
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
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All tests passed! Temporal Analytics system is ready for deployment.")
    elif success_rate >= 80:
        print("✅ Most tests passed. System is functional with minor issues.")
    else:
        print("⚠️ Multiple test failures. Review system before deployment.")
    
    return result.wasSuccessful()


async def demo_temporal_analytics():
    """Demonstrate temporal analytics capabilities"""
    print("\n🎭 Temporal Analytics System Demo")
    print("=" * 50)
    
    # Create demo agent
    agent = TemporalAnalyticsAgent()
    
    # Create sample data
    test_case = TestTemporalAnalytics()
    test_case.setUp()
    sample_posts = test_case.sample_posts
    
    print(f"📊 Running analysis on {len(sample_posts)} sample posts...")
    
    # Run analysis
    result = await agent.analyze_temporal_patterns(sample_posts, "demo_batch")
    
    # Display key insights
    print("\n🔍 Key Insights:")
    
    temporal_summary = result.get("temporal_summary", {})
    print(f"• Total posts analyzed: {temporal_summary.get('total_posts', 0)}")
    print(f"• Time span: {temporal_summary.get('time_span_hours', 0):.1f} hours")
    print(f"• Avg engagement/hour: {temporal_summary.get('avg_engagement_per_hour', 0):.1f}")
    
    optimal_times = result.get("optimal_times", {})
    if optimal_times.get("best_days"):
        print(f"• Best days: {', '.join(optimal_times['best_days'][:2])}")
    
    if optimal_times.get("optimal_ranges"):
        best_range = optimal_times["optimal_ranges"][0]
        print(f"• Optimal hours: {best_range['range_label']}")
    
    trend_analysis = result.get("trend_analysis", {})
    if trend_analysis.get("avg_time_to_trend_minutes", 0) > 0:
        print(f"• Avg time to trend: {trend_analysis['avg_time_to_trend_minutes']:.0f} minutes")
    
    momentum_analysis = result.get("momentum_analysis", {})
    if momentum_analysis.get("avg_momentum_duration_hours", 0) > 0:
        print(f"• Avg momentum duration: {momentum_analysis['avg_momentum_duration_hours']:.1f} hours")
    
    print("\n📱 Discord Message Preview:")
    print("-" * 40)
    print(result.get("discord_message", "No message generated"))
    print("-" * 40)
    
    return result


if __name__ == "__main__":
    # Run comprehensive test
    print("Starting Temporal Analytics Test Suite...")
    success = run_comprehensive_test()
    
    if success:
        # Run demo if all tests pass
        print("\n" + "=" * 60)
        asyncio.run(demo_temporal_analytics())
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Temporal Analytics Testing Complete")