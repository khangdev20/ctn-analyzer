"""
Trending Prediction System - Comprehensive Test Suite

This test suite validates all aspects of the Trending Prediction system including:
- Weighted scoring rubric calculations
- Trending probability algorithms
- Candidate identification and ranking
- Discord message formatting
- Workflow integration
- Edge case handling

Author: AI Assistant
Date: October 7, 2025
Version: 1.0.0
"""

from worker.tasks.trending_prediction_task import TrendingPredictionTask, run_trending_prediction_task
from worker.features.trending_prediction import TrendingPredictionAgent, analyze_trending_potential
import asyncio
import unittest
import json
import sys
import os
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import trending prediction components


class TestTrendingPrediction(unittest.TestCase):
    """Comprehensive test suite for Trending Prediction system."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = TrendingPredictionAgent()
        self.task = TrendingPredictionTask()

        # Sample test data with varied scoring
        self.sample_posts = [
            {
                'id': '584721',
                'content': 'Breaking: Major policy announcement with huge implications!',
                'author': 'political_insider',
                'story_score': 85,
                'engagement_score': 92,
                'velocity': 8.5,
                'network_influence': 0.75,
                'timing_score': 88,
                'strategic_score': 82
            },
            {
                'id': '584512',
                'content': 'This healthcare initiative could transform our community',
                'author': 'health_advocate',
                'story_score': 78,
                'engagement_score': 84,
                'velocity': 7.2,
                'network_influence': 0.68,
                'timing_score': 82,
                'strategic_score': 75
            },
            {
                'id': '584330',
                'content': 'Heartwarming story about local resilience and hope',
                'author': 'community_voice',
                'story_score': 82,
                'engagement_score': 79,
                'velocity': 6.8,
                'network_influence': 0.71,
                'timing_score': 85,
                'strategic_score': 78
            },
            {
                'id': '584102',
                'content': 'Average post about daily updates',
                'author': 'regular_user',
                'story_score': 45,
                'engagement_score': 38,
                'velocity': 2.1,
                'network_influence': 0.25,
                'timing_score': 42,
                'strategic_score': 35
            }
        ]

    def test_trending_prediction_core(self):
        """Test core trending prediction functionality."""
        print("🧪 Testing Trending Prediction Core...")

        async def run_test():
            result = await self.agent.analyze_trending_potential(self.sample_posts, "test_core")

            # Validate basic structure
            self.assertIn('posts_analyzed', result)
            self.assertIn('average_final_score', result)
            self.assertIn('trending_candidates', result)
            self.assertIn('discord_message', result)

            # Validate data quality
            self.assertEqual(result['posts_analyzed'], len(self.sample_posts))
            self.assertGreater(result['average_final_score'], 0)
            self.assertIsInstance(result['trending_candidates'], list)

            print(f"✅ Analyzed {result['posts_analyzed']} posts")
            print(f"✅ Average score: {result['average_final_score']}")
            print(
                f"✅ Trending candidates: {len(result['trending_candidates'])}")

            return result

        result = asyncio.run(run_test())
        self.assertIsNotNone(result)

    def test_weighted_scoring_rubric(self):
        """Test weighted scoring rubric calculations."""
        print("🧪 Testing Weighted Scoring Rubric...")

        async def run_test():
            result = await self.agent.analyze_trending_potential(self.sample_posts, "test_scoring")

            # Check that detailed scores are available
            self.assertIn('detailed_scores', result)
            detailed_scores = result['detailed_scores']

            if detailed_scores:
                first_post = detailed_scores[0]

                # Validate scoring components exist
                required_components = [
                    'content_component', 'engagement_component', 'timing_component',
                    'network_component', 'strategy_component', 'final_score'
                ]

                for component in required_components:
                    self.assertIn(component, first_post)
                    self.assertIsInstance(first_post[component], (int, float))

                # Validate weighted calculation (approximately)
                expected_total = (
                    first_post['content_component'] + first_post['engagement_component'] +
                    first_post['timing_component'] + first_post['network_component'] +
                    first_post['strategy_component']
                )

                # Should be close to final score (within rounding tolerance)
                self.assertAlmostEqual(
                    expected_total, first_post['final_score'], delta=0.5)

                print(
                    f"✅ Scoring components validated for post {first_post.get('id')}")
                print(
                    f"✅ Content: {first_post['content_component']}, Engagement: {first_post['engagement_component']}")
                print(f"✅ Final score calculation verified")

        asyncio.run(run_test())

    def test_trending_probability_calculation(self):
        """Test trending probability algorithms."""
        print("🧪 Testing Trending Probability Calculation...")

        async def run_test():
            result = await self.agent.analyze_trending_potential(self.sample_posts, "test_probability")

            detailed_scores = result.get('detailed_scores', [])

            for post in detailed_scores:
                # Validate probability exists and is in valid range
                self.assertIn('trending_probability', post)
                probability = post['trending_probability']

                self.assertGreaterEqual(probability, 0.0)
                self.assertLessEqual(probability, 1.0)

                # Higher scoring posts should generally have higher probabilities
                if post['final_score'] > 80:
                    self.assertGreater(probability, 0.6,
                                       f"High scoring post {post.get('id')} should have high probability")

            print(
                f"✅ Validated probability calculations for {len(detailed_scores)} posts")

            # Test probability distribution
            probabilities = [p['trending_probability']
                             for p in detailed_scores]
            if probabilities:
                max_prob = max(probabilities)
                min_prob = min(probabilities)
                print(f"✅ Probability range: {min_prob:.3f} to {max_prob:.3f}")

        asyncio.run(run_test())

    def test_trending_candidate_identification(self):
        """Test trending candidate identification and ranking."""
        print("🧪 Testing Trending Candidate Identification...")

        async def run_test():
            # Test with high-scoring posts that should be trending candidates
            high_score_posts = [
                {
                    'id': 'high_1',
                    'content': 'Ultra viral content with massive engagement',
                    'author': 'viral_creator',
                    'story_score': 95,
                    'engagement_score': 98,
                    'velocity': 9.8,
                    'network_influence': 0.95,
                    'timing_score': 94,
                    'strategic_score': 92
                },
                {
                    'id': 'high_2',
                    'content': 'Another trending post with great metrics',
                    'author': 'trending_user',
                    'story_score': 88,
                    'engagement_score': 91,
                    'velocity': 8.9,
                    'network_influence': 0.87,
                    'timing_score': 89,
                    'strategic_score': 85
                }
            ]

            result = await self.agent.analyze_trending_potential(high_score_posts, "test_candidates")

            trending_candidates = result.get('trending_candidates', [])

            # Should identify candidates with high scores
            self.assertGreater(len(trending_candidates), 0,
                               "Should identify trending candidates")

            # Validate candidate structure
            for candidate in trending_candidates:
                required_fields = ['rank', 'post_id',
                                   'trending_probability', 'final_score']
                for field in required_fields:
                    self.assertIn(field, candidate)

                # Trending candidates should have high probability
                self.assertGreaterEqual(candidate['trending_probability'], 0.8)

            # Candidates should be ranked by probability
            if len(trending_candidates) > 1:
                for i in range(len(trending_candidates) - 1):
                    self.assertGreaterEqual(
                        trending_candidates[i]['trending_probability'],
                        trending_candidates[i + 1]['trending_probability'],
                        "Candidates should be ranked by probability"
                    )

            print(
                f"✅ Identified {len(trending_candidates)} trending candidates")
            for candidate in trending_candidates:
                print(
                    f"  🏆 Rank {candidate['rank']}: Post {candidate['post_id']} ({candidate['trending_probability']:.3f})")

        asyncio.run(run_test())

    def test_influencing_factors_analysis(self):
        """Test analysis of top influencing factors."""
        print("🧪 Testing Influencing Factors Analysis...")

        async def run_test():
            result = await self.agent.analyze_trending_potential(self.sample_posts, "test_factors")

            # Validate influencing factors
            self.assertIn('top_influencing_factors', result)
            factors = result['top_influencing_factors']

            self.assertIsInstance(factors, list)
            self.assertGreater(len(factors), 0)

            # Factors should be meaningful strings
            for factor in factors:
                self.assertIsInstance(factor, str)
                self.assertGreater(len(factor), 0)

            print(f"✅ Identified {len(factors)} key influencing factors")
            for i, factor in enumerate(factors, 1):
                print(f"  {i}. {factor}")

        asyncio.run(run_test())

    def test_discord_message_generation(self):
        """Test Discord message formatting."""
        print("🧪 Testing Discord Message Generation...")

        async def run_test():
            result = await self.agent.analyze_trending_potential(self.sample_posts, "test_discord")

            # Validate Discord message exists
            self.assertIn('discord_message', result)
            discord_message = result['discord_message']

            self.assertIsInstance(discord_message, str)
            self.assertGreater(len(discord_message), 0)

            # Check for required Discord format elements
            required_elements = [
                '🔥 **Trending Prediction Report**',
                '**Avg Final Score:**',
                '**Trending Candidates:**',
                '**Top Influencing Factors:**'
            ]

            for element in required_elements:
                self.assertIn(element, discord_message,
                              f"Discord message should contain: {element}")

            print(f"✅ Discord message generated successfully")
            print(f"✅ Message length: {len(discord_message)} characters")

            # Display preview
            print("\n📱 Discord Message Preview:")
            print("-" * 40)
            print(discord_message)
            print("-" * 40)

        asyncio.run(run_test())

    def test_score_distribution_analysis(self):
        """Test score distribution calculations."""
        print("🧪 Testing Score Distribution Analysis...")

        async def run_test():
            result = await self.agent.analyze_trending_potential(self.sample_posts, "test_distribution")

            # Validate score distribution
            self.assertIn('score_distribution', result)
            distribution = result['score_distribution']

            if distribution:
                # Check statistical measures
                expected_stats = ['score_mean', 'score_median',
                                  'score_std', 'score_min', 'score_max']
                for stat in expected_stats:
                    self.assertIn(stat, distribution)
                    self.assertIsInstance(distribution[stat], (int, float))

                # Validate logical relationships
                self.assertLessEqual(
                    distribution['score_min'], distribution['score_mean'])
                self.assertLessEqual(
                    distribution['score_mean'], distribution['score_max'])
                self.assertGreaterEqual(distribution['score_std'], 0)

                print(f"✅ Score distribution calculated")
                print(
                    f"  Mean: {distribution['score_mean']}, Median: {distribution['score_median']}")
                print(
                    f"  Range: {distribution['score_min']} - {distribution['score_max']}")
                print(f"  Std Dev: {distribution['score_std']}")

        asyncio.run(run_test())

    def test_empty_data_handling(self):
        """Test handling of empty or insufficient data."""
        print("🧪 Testing Empty Data Handling...")

        async def run_test():
            # Test with empty data
            result = await self.agent.analyze_trending_potential([], "test_empty")

            self.assertIn('posts_analyzed', result)
            self.assertEqual(result['posts_analyzed'], 0)
            self.assertIn('discord_message', result)

            # Test with single post
            single_post = [self.sample_posts[0]]
            result_single = await self.agent.analyze_trending_potential(single_post, "test_single")

            self.assertEqual(result_single['posts_analyzed'], 1)
            self.assertIn('trending_candidates', result_single)

            print(f"✅ Empty data handling works correctly")
            print(f"✅ Single post analysis works correctly")

        asyncio.run(run_test())

    def test_trending_task_workflow(self):
        """Test complete trending prediction task workflow."""
        print("🧪 Testing Trending Prediction Task Workflow...")

        async def run_test():
            # Test task execution
            result = await self.task.run_trending_prediction_workflow("test_workflow")

            # Validate workflow results
            self.assertIn('status', result)
            self.assertIn('batch_id', result)
            self.assertIn('timestamp', result)

            # Should have either success status or handle gracefully
            self.assertIn(result['status'], ['success', 'no_data', 'error'])

            if result['status'] == 'success':
                self.assertIn('posts_processed', result)
                self.assertIn('trending_candidates', result)
                self.assertIn('analysis_results', result)

                print(f"✅ Workflow completed successfully")
                print(f"✅ Processed {result.get('posts_processed', 0)} posts")
                print(
                    f"✅ Found {result.get('trending_candidates', 0)} candidates")
            else:
                print(
                    f"✅ Workflow handled {result['status']} condition gracefully")

        asyncio.run(run_test())

    def test_standalone_function(self):
        """Test standalone analyze_trending_potential function."""
        print("🧪 Testing Standalone Function...")

        async def run_test():
            # Test standalone function call
            result = await analyze_trending_potential(self.sample_posts, "test_standalone")

            # Should return same structure as agent method
            self.assertIn('posts_analyzed', result)
            self.assertIn('average_final_score', result)
            self.assertIn('trending_candidates', result)
            self.assertIn('discord_message', result)

            self.assertEqual(result['posts_analyzed'], len(self.sample_posts))

            print(f"✅ Standalone function works correctly")
            print(f"✅ Processed {result['posts_analyzed']} posts")

        asyncio.run(run_test())

    def test_scoring_edge_cases(self):
        """Test edge cases in scoring calculations."""
        print("🧪 Testing Scoring Edge Cases...")

        async def run_test():
            # Test extreme values
            extreme_posts = [
                {
                    'id': 'extreme_high',
                    'content': 'Maximum score test post',
                    'author': 'test_user',
                    'story_score': 100,
                    'engagement_score': 100,
                    'velocity': 10,
                    'network_influence': 1.0,
                    'timing_score': 100,
                    'strategic_score': 100
                },
                {
                    'id': 'extreme_low',
                    'content': 'Minimum score test post',
                    'author': 'test_user',
                    'story_score': 0,
                    'engagement_score': 0,
                    'velocity': 0,
                    'network_influence': 0.0,
                    'timing_score': 0,
                    'strategic_score': 0
                }
            ]

            result = await self.agent.analyze_trending_potential(extreme_posts, "test_extremes")

            # Should handle extreme values gracefully
            self.assertEqual(result['posts_analyzed'], 2)
            self.assertIn('detailed_scores', result)

            detailed_scores = result['detailed_scores']
            if len(detailed_scores) >= 2:
                high_score_post = next(
                    (p for p in detailed_scores if p['id'] == 'extreme_high'), None)
                low_score_post = next(
                    (p for p in detailed_scores if p['id'] == 'extreme_low'), None)

                if high_score_post and low_score_post:
                    # High score post should have higher final score
                    self.assertGreater(
                        high_score_post['final_score'], low_score_post['final_score'])

                    # Probabilities should be in valid range
                    self.assertGreaterEqual(
                        high_score_post['trending_probability'], 0.0)
                    self.assertLessEqual(
                        high_score_post['trending_probability'], 1.0)
                    self.assertGreaterEqual(
                        low_score_post['trending_probability'], 0.0)
                    self.assertLessEqual(
                        low_score_post['trending_probability'], 1.0)

            print(f"✅ Edge cases handled correctly")

        asyncio.run(run_test())


def run_all_tests():
    """Run all trending prediction tests with detailed output."""
    print("🚀 Starting Comprehensive Trending Prediction Test Suite")
    print("=" * 60)

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTrendingPrediction)

    # Run tests with detailed output
    test_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    test_result = test_runner.run(test_suite)

    # Print summary
    print("=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ Tests run: {test_result.testsRun}")
    print(f"❌ Failures: {len(test_result.failures)}")
    print(f"⚠️ Errors: {len(test_result.errors)}")

    if test_result.failures:
        print("\n❌ Failures:")
        for test, failure in test_result.failures:
            print(f"  - {test}: {failure}")

    if test_result.errors:
        print("\n⚠️ Errors:")
        for test, error in test_result.errors:
            print(f"  - {test}: {error}")

    success_rate = ((test_result.testsRun - len(test_result.failures) - len(test_result.errors)) /
                    test_result.testsRun * 100) if test_result.testsRun > 0 else 0

    print(f"\n🎯 Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 Excellent! Trending Prediction system is ready for deployment.")
        status = "SUCCESS"
    elif success_rate >= 80:
        print("✅ Good performance. Minor issues to address.")
        status = "MOSTLY_SUCCESS"
    else:
        print("⚠️ Significant issues detected. Review required.")
        status = "NEEDS_WORK"

    print(f"\n{status}: Trending Prediction Testing Complete")
    return test_result.wasSuccessful()


if __name__ == "__main__":
    print("Starting Trending Prediction Test Suite...")
    success = run_all_tests()

    if success:
        # Run integration demo
        print("\n" + "=" * 60)
        print("🎭 Trending Prediction System Demo")
        print("=" * 50)

        async def run_demo():
            agent = TrendingPredictionAgent()

            # Demo with sample data
            demo_posts = [
                {
                    'id': '584721',
                    'content': 'Breaking: Revolutionary policy change announced!',
                    'author': 'news_insider',
                    'story_score': 88,
                    'engagement_score': 94,
                    'velocity': 9.1,
                    'network_influence': 0.82,
                    'timing_score': 91,
                    'strategic_score': 86
                },
                {
                    'id': '584512',
                    'content': 'Community rallies for important local cause',
                    'author': 'community_leader',
                    'story_score': 75,
                    'engagement_score': 81,
                    'velocity': 6.8,
                    'network_influence': 0.65,
                    'timing_score': 78,
                    'strategic_score': 72
                }
            ]

            result = await agent.analyze_trending_potential(demo_posts, "demo_trending")

            print(f"📊 Demo Results:")
            print(f"Posts Analyzed: {result['posts_analyzed']}")
            print(f"Average Final Score: {result['average_final_score']}")
            print(f"Trending Candidates: {len(result['trending_candidates'])}")
            print(
                f"Top Factors: {', '.join(result['top_influencing_factors'])}")

            print("\n📱 Sample Discord Message:")
            print("-" * 40)
            print(result['discord_message'])
            print("-" * 40)

        asyncio.run(run_demo())
        print("\n✅ SUCCESS: Trending Prediction Testing and Demo Complete")
    else:
        print("\n❌ FAILED: Trending Prediction Testing Complete")
