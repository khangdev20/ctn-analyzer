"""
Test Engagement Intelligence System
Demonstrates social engagement analysis with mock data
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock data generators
def generate_mock_post(post_id: str, 
                      base_likes: int = 50, 
                      base_replies: int = 10, 
                      base_reposts: int = 5,
                      created_hours_ago: int = 2) -> Dict:
    """Generate mock social media post"""
    created_time = datetime.now(timezone.utc) - timedelta(hours=created_hours_ago)
    
    return {
        "id": post_id,
        "content": f"This is mock post content for post {post_id}. #trending #social",
        "author": {
            "id": f"user_{post_id}",
            "username": f"user{post_id}",
            "display_name": f"User {post_id}",
            "follower_count": 1000 + int(post_id) * 100,
            "verified": int(post_id) % 3 == 0
        },
        "engagement": {
            "like_count": base_likes,
            "reply_count": base_replies,
            "repost_count": base_reposts
        },
        "like_count": base_likes,
        "reply_count": base_replies,
        "repost_count": base_reposts,
        "tags": ["trending", "social", "test"],
        "created_at": created_time.isoformat(),
        "collected_at": datetime.now(timezone.utc).isoformat()
    }

def generate_mock_batch(batch_id: str, post_count: int = 10, engagement_boost: float = 1.0) -> Dict:
    """Generate mock data batch"""
    posts = []
    
    for i in range(1, post_count + 1):
        # Vary engagement levels
        base_likes = int(50 * engagement_boost * (1 + i * 0.2))
        base_replies = int(10 * engagement_boost * (1 + i * 0.1))
        base_reposts = int(5 * engagement_boost * (1 + i * 0.15))
        
        post = generate_mock_post(
            post_id=str(i),
            base_likes=base_likes,
            base_replies=base_replies,
            base_reposts=base_reposts,
            created_hours_ago=2
        )
        posts.append(post)
    
    return {
        "batch_id": batch_id,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "posts": posts,
        "metadata": {
            "total_posts": len(posts),
            "collection_source": "mock_generator"
        }
    }

async def test_engagement_intelligence():
    """Test the engagement intelligence system"""
    print("🚀 Testing Social Engagement Intelligence System")
    print("=" * 60)
    
    try:
        # Import the engagement intelligence components
        from worker.features.engagement_intelligence import EngagementIntelligenceAgent, analyze_engagement_snapshots
        
        # Create mock data - previous and current snapshots
        print("\n📊 Step 1: Generating mock data snapshots...")
        
        # Previous snapshot (lower engagement)
        previous_batch = generate_mock_batch("previous_batch", post_count=8, engagement_boost=1.0)
        
        # Current snapshot (higher engagement - simulating growth)
        current_batch = generate_mock_batch("current_batch", post_count=10, engagement_boost=1.5)
        
        # Modify some posts to show specific growth patterns
        current_posts = current_batch["posts"]
        
        # Post 1: High likes growth
        current_posts[0]["like_count"] = 150  # +100 likes from previous 50
        current_posts[0]["engagement"]["like_count"] = 150
        
        # Post 2: High replies growth  
        current_posts[1]["reply_count"] = 45   # +35 replies from previous 10
        current_posts[1]["engagement"]["reply_count"] = 45
        
        # Post 3: High reposts growth
        current_posts[2]["repost_count"] = 25  # +20 reposts from previous 5
        current_posts[2]["engagement"]["repost_count"] = 25
        
        # Add timestamps to simulate time difference
        previous_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        current_time = datetime.now(timezone.utc)
        
        previous_batch["collected_at"] = previous_time.isoformat()
        current_batch["collected_at"] = current_time.isoformat()
        
        # Update collection times for posts
        for post in previous_batch["posts"]:
            post["collected_at"] = previous_time.isoformat()
        
        for post in current_batch["posts"]:
            post["collected_at"] = current_time.isoformat()
        
        print(f"   Previous batch: {len(previous_batch['posts'])} posts")
        print(f"   Current batch: {len(current_batch['posts'])} posts")
        print(f"   Time difference: 30 minutes")
        
        # Step 2: Run engagement analysis
        print("\n🧠 Step 2: Running engagement intelligence analysis...")
        
        batch_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Use the standalone function
        results = await analyze_engagement_snapshots(
            previous_data=previous_batch,
            current_data=current_batch,
            batch_id=batch_id
        )
        
        # Step 3: Display results
        print("\n📈 Step 3: Analysis Results")
        print("-" * 40)
        
        if results.get("error"):
            print(f"❌ Analysis failed: {results.get('error_message')}")
            return
        
        # Summary metrics
        growth_summary = results.get("growth_summary", {})
        print(f"📊 Posts Analyzed: {results.get('matched_posts', 0)}")
        print(f"📈 Average Velocity: +{growth_summary.get('avg_velocity_per_min', 0):.2f} /min")
        print(f"⚡ Average Acceleration: {growth_summary.get('avg_acceleration', 0):.3f}")
        print(f"🔥 Posts with Growth: {growth_summary.get('posts_with_growth', 0)}")
        print(f"📊 Total Delta Engagement: +{growth_summary.get('total_delta_engagement', 0)}")
        
        # Top performers
        print("\n🏆 Top 5 Performers:")
        top_performers = results.get("top_performers", [])
        for performer in top_performers[:5]:
            rank = performer.get("rank", 0)
            author = performer.get("author", "unknown")
            velocity = performer.get("velocity_per_min", 0)
            delta_likes = performer.get("delta_likes", 0)
            delta_replies = performer.get("delta_replies", 0)
            delta_reposts = performer.get("delta_reposts", 0)
            
            details = []
            if delta_likes > 0:
                details.append(f"+{delta_likes} likes")
            if delta_replies > 0:
                details.append(f"+{delta_replies} replies")
            if delta_reposts > 0:
                details.append(f"+{delta_reposts} reposts")
            
            details_text = f" ({', '.join(details)})" if details else ""
            print(f"   {rank}. @{author} — +{velocity:.1f}/min{details_text}")
        
        # Engagement composition
        print("\n📊 Engagement Composition:")
        composition = results.get("engagement_composition", {})
        likes_pct = composition.get("likes_percent", 0)
        replies_pct = composition.get("replies_percent", 0)
        reposts_pct = composition.get("reposts_percent", 0)
        print(f"   ❤️ Likes: {likes_pct}%")
        print(f"   💬 Replies: {replies_pct}%")
        print(f"   🔁 Reposts: {reposts_pct}%")
        
        # Step 4: Display Discord message
        print("\n📢 Step 4: Discord-Formatted Message")
        print("-" * 40)
        discord_message = results.get("discord_message", "")
        print(discord_message)
        
        # Step 5: Test quick update format
        print("\n⚡ Step 5: Quick Update Format")
        print("-" * 40)
        
        agent = EngagementIntelligenceAgent()
        detailed_analysis = results.get("detailed_analysis", {})
        quick_update = await agent.format_quick_engagement_update(detailed_analysis)
        print(quick_update)
        
        print("\n✅ Test completed successfully!")
        print("=" * 60)
        
        return results
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the engagement intelligence modules are in the correct location")
        return None
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_engagement_task():
    """Test the complete engagement intelligence task"""
    print("\n🔄 Testing Complete Engagement Intelligence Task")
    print("=" * 60)
    
    try:
        from worker.tasks.engagement_intelligence_task import EngagementIntelligenceTask
        
        # Create task instance
        task = EngagementIntelligenceTask()
        
        # Test quick engagement check
        print("\n⚡ Testing quick engagement check...")
        quick_result = await task.quick_engagement_check()
        print(quick_result)
        
        print("\n✅ Task test completed!")
        
    except ImportError as e:
        print(f"❌ Task import error: {e}")
        print("Task components may not be available in this environment")
        
    except Exception as e:
        print(f"❌ Task test failed: {e}")
        import traceback
        traceback.print_exc()

async def demonstrate_engagement_scenarios():
    """Demonstrate different engagement growth scenarios"""
    print("\n🎯 Demonstrating Different Engagement Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Viral Growth",
            "description": "Post experiences viral growth with high likes",
            "previous_engagement": {"likes": 100, "replies": 20, "reposts": 10},
            "current_engagement": {"likes": 500, "replies": 80, "reposts": 60}
        },
        {
            "name": "Discussion Starter", 
            "description": "Post generates lots of discussion (replies)",
            "previous_engagement": {"likes": 50, "replies": 15, "reposts": 5},
            "current_engagement": {"likes": 80, "replies": 150, "reposts": 20}
        },
        {
            "name": "Share Magnet",
            "description": "Post gets shared frequently (reposts)",
            "previous_engagement": {"likes": 75, "replies": 25, "reposts": 8},
            "current_engagement": {"likes": 120, "replies": 40, "reposts": 85}
        }
    ]
    
    from worker.features.engagement_intelligence import analyze_engagement_snapshots
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📊 Scenario {i}: {scenario['name']}")
        print(f"   {scenario['description']}")
        
        # Create mock data for scenario
        prev_data = {
            "posts": [{
                "id": "scenario_post",
                "like_count": scenario["previous_engagement"]["likes"],
                "reply_count": scenario["previous_engagement"]["replies"],
                "repost_count": scenario["previous_engagement"]["reposts"],
                "author": {"username": "test_user"},
                "content": f"Scenario {i} test post",
                "collected_at": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
            }]
        }
        
        curr_data = {
            "posts": [{
                "id": "scenario_post",
                "like_count": scenario["current_engagement"]["likes"],
                "reply_count": scenario["current_engagement"]["replies"],
                "repost_count": scenario["current_engagement"]["reposts"],
                "author": {"username": "test_user"},
                "content": f"Scenario {i} test post",
                "collected_at": datetime.now(timezone.utc).isoformat()
            }]
        }
        
        # Analyze scenario
        result = await analyze_engagement_snapshots(prev_data, curr_data, f"scenario_{i}")
        
        if not result.get("error"):
            growth = result.get("growth_summary", {})
            velocity = growth.get("avg_velocity_per_min", 0)
            composition = result.get("engagement_composition", {})
            
            print(f"   🚀 Velocity: +{velocity:.1f}/min")
            print(f"   📊 Composition: {composition.get('likes_percent', 0)}% likes, {composition.get('replies_percent', 0)}% replies, {composition.get('reposts_percent', 0)}% reposts")
            
            # Show mini Discord message
            discord_msg = result.get("discord_message", "").split('\n')[:3]  # First 3 lines
            for line in discord_msg:
                if line.strip():
                    print(f"   💬 {line}")
        else:
            print(f"   ❌ Analysis failed: {result.get('error_message')}")

if __name__ == "__main__":
    async def main():
        # Run all tests
        print("🧪 Starting Engagement Intelligence System Tests")
        print("=" * 70)
        
        # Test 1: Core engagement analysis
        await test_engagement_intelligence()
        
        # Test 2: Complete task workflow  
        await test_engagement_task()
        
        # Test 3: Different scenarios
        await demonstrate_engagement_scenarios()
        
        print("\n🎉 All tests completed!")
        print("=" * 70)
    
    # Run the tests
    asyncio.run(main())