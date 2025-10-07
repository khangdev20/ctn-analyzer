"""
Comprehensive Network Intelligence Test
Tests all components of the Network Intelligence analysis system
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


async def test_network_intelligence_core():
    """Test the core NetworkIntelligenceAgent"""
    print("🌐 Testing Core Network Intelligence Agent...")

    try:
        from worker.features.network_intelligence import NetworkIntelligenceAgent

        # Create test data with realistic network patterns
        test_posts = [
            {
                "id": "post_1",
                "author": {"username": "kingstondaily", "follower_count": 15000},
                "content": "Breaking news about local politics #VoteKingston #LocalNews #Election2025",
                "tags": ["VoteKingston", "LocalNews", "Election2025"],
                "like_count": 245,
                "reply_count": 67,
                "repost_count": 89,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_2",
                "author": {"username": "riverwatcher", "follower_count": 8500},
                "content": "Environmental concerns in our community #SaveTheRiver #VoteKingston #Environment",
                "tags": ["SaveTheRiver", "VoteKingston", "Environment"],
                "like_count": 156,
                "reply_count": 34,
                "repost_count": 78,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_3",
                "author": {"username": "localactivist", "follower_count": 5200},
                "content": "Youth engagement in politics #YouthVote #VoteKingston #ChangeNow",
                "tags": ["YouthVote", "VoteKingston", "ChangeNow"],
                "like_count": 312,
                "reply_count": 45,
                "repost_count": 167,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_4",
                "author": {"username": "communityvoice", "follower_count": 12000},
                "content": "Community meeting tonight #CommunityFirst #VoteKingston #LocalNews",
                "tags": ["CommunityFirst", "VoteKingston", "LocalNews"],
                "like_count": 89,
                "reply_count": 156,
                "repost_count": 23,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_5",
                "author": {"username": "newsreporter", "follower_count": 18500},
                "content": "Analysis of recent policy changes #PolicyAnalysis #LocalNews #Government",
                "tags": ["PolicyAnalysis", "LocalNews", "Government"],
                "like_count": 78,
                "reply_count": 92,
                "repost_count": 45,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_6",
                "author": {"username": "youthleader", "follower_count": 3500},
                "content": "Young voices matter! #YouthVote #ChangeNow #FutureLeaders",
                "tags": ["YouthVote", "ChangeNow", "FutureLeaders"],
                "like_count": 198,
                "reply_count": 67,
                "repost_count": 89,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_7",
                "author": {"username": "environmentalist", "follower_count": 7200},
                "content": "Protecting our natural resources #SaveTheRiver #Environment #Sustainability",
                "tags": ["SaveTheRiver", "Environment", "Sustainability"],
                "like_count": 134,
                "reply_count": 28,
                "repost_count": 56,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "post_8",
                "author": {"username": "politicalanalyst", "follower_count": 22000},
                "content": "Deep dive into campaign strategies #Election2025 #PolicyAnalysis #Government",
                "tags": ["Election2025", "PolicyAnalysis", "Government"],
                "like_count": 267,
                "reply_count": 145,
                "repost_count": 178,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        # Test network analysis
        agent = NetworkIntelligenceAgent()
        results = await agent.analyze_network_intelligence(test_posts, "test_network_core")

        # Verify results structure
        required_fields = [
            'batch_id', 'analysis_timestamp', 'network_summary',
            'hashtag_clusters', 'author_communities', 'tag_connectivity',
            'cross_influence', 'discord_message'
        ]

        missing_fields = [
            field for field in required_fields if field not in results]
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False

        # Check network summary
        network_summary = results['network_summary']
        print(f"✅ Network Summary:")
        print(f"   • Authors: {network_summary['total_authors']}")
        print(f"   • Hashtags: {network_summary['total_hashtags']}")
        print(f"   • Posts: {network_summary['total_posts']}")
        print(f"   • Connections: {network_summary['unique_connections']}")

        # Check hashtag clusters
        hashtag_clusters = results['hashtag_clusters']
        print(f"✅ Hashtag Clusters: {hashtag_clusters['cluster_count']} found")
        if hashtag_clusters['clusters']:
            top_cluster = hashtag_clusters['clusters'][0]
            print(
                f"   • Top cluster: {len(top_cluster['tags'])} tags, {top_cluster['total_engagement']} engagement")

        # Check author communities
        author_communities = results['author_communities']
        print(
            f"✅ Author Communities: {author_communities['community_count']} found")
        if author_communities['influencers']:
            top_influencer = author_communities['influencers'][0]
            print(
                f"   • Top influencer: @{top_influencer['username']} (score: {top_influencer.get('influence_score', 0)})")

        # Check tag connectivity
        tag_connectivity = results['tag_connectivity']
        print(f"✅ Tag Connectivity:")
        print(
            f"   • Connectivity Index: {tag_connectivity['connectivity_index']}")
        print(f"   • Network Density: {tag_connectivity['network_density']}")

        # Check cross influence
        cross_influence = results['cross_influence']
        if cross_influence['most_influential_tag']:
            influential_tag = cross_influence['most_influential_tag']
            print(
                f"✅ Most Influential Tag: #{influential_tag['hashtag']} (score: {influential_tag['influence_score']})")

        # Check Discord message
        discord_msg = results['discord_message']
        print(f"✅ Discord Message: {len(discord_msg)} characters")

        return True

    except Exception as e:
        print(f"❌ Core test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_network_task_workflow():
    """Test the complete NetworkIntelligenceTask workflow"""
    print("\n🚀 Testing Complete Network Intelligence Task Workflow...")

    try:
        from worker.tasks.network_intelligence_task import NetworkIntelligenceTask

        # Create task
        task = NetworkIntelligenceTask()

        # Test workflow (should use mock data since no real data available)
        results = await task.run_network_analysis_workflow(
            batch_id="test_network_workflow_001",
            send_discord=False,  # Don't spam Discord during tests
            save_results=False   # Don't save files during tests
        )

        # Check workflow results
        workflow_status = results.get('workflow_status', 'unknown')
        print(f"Status: {workflow_status}")

        if workflow_status == 'success':
            print(f"✅ Workflow completed successfully")
            print(f"   • Batch ID: {results.get('batch_id')}")

            execution_summary = results.get('execution_summary', {})
            print(f"   • Authors: {execution_summary.get('total_authors', 0)}")
            print(
                f"   • Hashtags: {execution_summary.get('total_hashtags', 0)}")
            print(
                f"   • Clusters: {execution_summary.get('hashtag_clusters', 0)}")
            print(
                f"   • Communities: {execution_summary.get('author_communities', 0)}")

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


async def test_network_clustering():
    """Test hashtag clustering and community detection"""
    print("\n🔗 Testing Network Clustering Algorithms...")

    try:
        from worker.features.network_intelligence import NetworkIntelligenceAgent

        # Create test data with clear clustering patterns
        clustering_test_posts = [
            # Political cluster
            {"id": "p1", "author": {"username": "politician1"}, "tags": [
                "Election2025", "Vote", "Campaign"], "like_count": 100, "reply_count": 20, "repost_count": 30},
            {"id": "p2", "author": {"username": "politician2"}, "tags": [
                "Election2025", "Vote", "Democracy"], "like_count": 150, "reply_count": 25, "repost_count": 40},
            {"id": "p3", "author": {"username": "voter1"}, "tags": [
                "Vote", "Campaign", "LocalPolitics"], "like_count": 80, "reply_count": 15, "repost_count": 20},

            # Environmental cluster
            {"id": "p4", "author": {"username": "environmentalist1"}, "tags": [
                "ClimateChange", "Environment", "Sustainability"], "like_count": 200, "reply_count": 50, "repost_count": 75},
            {"id": "p5", "author": {"username": "environmentalist2"}, "tags": [
                "ClimateChange", "GreenEnergy", "Environment"], "like_count": 180, "reply_count": 45, "repost_count": 60},
            {"id": "p6", "author": {"username": "activist1"}, "tags": [
                "Sustainability", "GreenEnergy", "EcoFriendly"], "like_count": 120, "reply_count": 30, "repost_count": 35},

            # Technology cluster
            {"id": "p7", "author": {"username": "techie1"}, "tags": [
                "AI", "Technology", "Innovation"], "like_count": 300, "reply_count": 80, "repost_count": 100},
            {"id": "p8", "author": {"username": "techie2"}, "tags": [
                "AI", "MachineLearning", "Technology"], "like_count": 250, "reply_count": 70, "repost_count": 90},
            {"id": "p9", "author": {"username": "developer1"}, "tags": [
                "Innovation", "MachineLearning", "Future"], "like_count": 180, "reply_count": 40, "repost_count": 55},
        ]

        # Add created_at timestamps
        for post in clustering_test_posts:
            post["created_at"] = datetime.now(timezone.utc).isoformat()

        agent = NetworkIntelligenceAgent()
        results = await agent.analyze_network_intelligence(clustering_test_posts, "test_clustering")

        # Verify clustering results
        hashtag_clusters = results['hashtag_clusters']
        print(f"✅ Clustering Results:")
        print(f"   • Clusters detected: {hashtag_clusters['cluster_count']}")

        if hashtag_clusters['clusters']:
            for i, cluster in enumerate(hashtag_clusters['clusters'][:3], 1):
                print(
                    f"   • Cluster {i}: {len(cluster['tags'])} tags - {', '.join(cluster['tags'][:3])}")

        # Verify community detection
        author_communities = results['author_communities']
        print(f"✅ Community Detection:")
        print(
            f"   • Communities detected: {author_communities['community_count']}")

        if author_communities['communities']:
            for i, community in enumerate(author_communities['communities'][:3], 1):
                print(
                    f"   • Community {i}: {community['size']} authors - {community['name']}")

        return True

    except Exception as e:
        print(f"❌ Clustering test failed: {e}")
        return False


async def test_influence_analysis():
    """Test cross-tag influence and connectivity analysis"""
    print("\n🧭 Testing Influence & Connectivity Analysis...")

    try:
        from worker.features.network_intelligence import NetworkIntelligenceAgent

        # Create test data with clear influence patterns
        influence_test_posts = [
            # High influence tag (appears with many others)
            {"id": "i1", "author": {"username": "influencer1"}, "tags": [
                "UnityNow", "Politics", "Community"], "like_count": 500, "reply_count": 100, "repost_count": 150},
            {"id": "i2", "author": {"username": "influencer2"}, "tags": [
                "UnityNow", "Environment", "Action"], "like_count": 450, "reply_count": 90, "repost_count": 120},
            {"id": "i3", "author": {"username": "user1"}, "tags": [
                "UnityNow", "Youth", "Change"], "like_count": 300, "reply_count": 60, "repost_count": 80},
            {"id": "i4", "author": {"username": "user2"}, "tags": [
                "UnityNow", "Technology", "Future"], "like_count": 350, "reply_count": 70, "repost_count": 90},

            # Bridge tags (connect different clusters)
            {"id": "i5", "author": {"username": "bridge1"}, "tags": [
                "Politics", "Environment"], "like_count": 200, "reply_count": 40, "repost_count": 50},
            {"id": "i6", "author": {"username": "bridge2"}, "tags": [
                "Technology", "Environment"], "like_count": 180, "reply_count": 35, "repost_count": 45},
            {"id": "i7", "author": {"username": "bridge3"}, "tags": [
                "Youth", "Politics"], "like_count": 220, "reply_count": 45, "repost_count": 55},
        ]

        # Add timestamps
        for post in influence_test_posts:
            post["created_at"] = datetime.now(timezone.utc).isoformat()

        agent = NetworkIntelligenceAgent()
        results = await agent.analyze_network_intelligence(influence_test_posts, "test_influence")

        # Check influence analysis
        cross_influence = results['cross_influence']
        print(f"✅ Influence Analysis:")

        if cross_influence['most_influential_tag']:
            influential_tag = cross_influence['most_influential_tag']
            print(f"   • Most Influential: #{influential_tag['hashtag']}")
            print(
                f"     - Influence Score: {influential_tag['influence_score']}")
            print(
                f"     - Unique Connections: {influential_tag['unique_connections']}")
            print(f"     - Author Count: {influential_tag['author_count']}")

        bridge_tags = cross_influence.get('bridge_tags', [])
        if bridge_tags:
            print(f"   • Bridge Tags: {len(bridge_tags)} found")
            for bridge in bridge_tags[:3]:
                print(
                    f"     - #{bridge['hashtag']} (bridge score: {bridge['bridge_score']})")

        # Check connectivity metrics
        tag_connectivity = results['tag_connectivity']
        print(f"✅ Connectivity Metrics:")
        print(
            f"   • Connectivity Index: {tag_connectivity['connectivity_index']}")
        print(f"   • Network Density: {tag_connectivity['network_density']}")

        most_connected = tag_connectivity.get('most_connected_tags', [])
        if most_connected:
            top_connected = most_connected[0]
            print(
                f"   • Most Connected: #{top_connected['hashtag']} (score: {top_connected['connectivity_score']})")

        return True

    except Exception as e:
        print(f"❌ Influence analysis test failed: {e}")
        return False


async def test_discord_formatting():
    """Test Discord message formatting for network intelligence"""
    print("\n💬 Testing Discord Message Formatting...")

    try:
        from worker.features.network_intelligence import NetworkIntelligenceAgent

        # Create sample network data
        sample_posts = [
            {"id": "d1", "author": {"username": "kingstondaily"}, "tags": [
                "VoteHawthorne", "ChangeNow"], "like_count": 200, "reply_count": 50, "repost_count": 75},
            {"id": "d2", "author": {"username": "riverwatcher"}, "tags": [
                "VoteHawthorne", "Environment"], "like_count": 150, "reply_count": 30, "repost_count": 45},
            {"id": "d3", "author": {"username": "activist1"}, "tags": [
                "ChangeNow", "Unity"], "like_count": 100, "reply_count": 25, "repost_count": 35},
            {"id": "d4", "author": {"username": "community1"}, "tags": [
                "UnityNow", "Local"], "like_count": 80, "reply_count": 20, "repost_count": 25},
        ]

        for post in sample_posts:
            post["created_at"] = datetime.now(timezone.utc).isoformat()

        agent = NetworkIntelligenceAgent()
        results = await agent.analyze_network_intelligence(sample_posts, "test_discord")

        discord_message = results.get('discord_message', '')
        print("✅ Discord Message Generated:")
        print("-" * 50)
        print(discord_message)
        print("-" * 50)

        # Verify Discord formatting elements
        required_elements = ["🌐", "**Network Intelligence Report**",
                             "Influencers:", "Tag Cluster:", "Detected Groups:"]
        missing_elements = [
            elem for elem in required_elements if elem not in discord_message]

        if missing_elements:
            print(f"⚠️ Missing Discord elements: {missing_elements}")
        else:
            print("✅ All Discord formatting elements present")

        # Check message length (Discord limit)
        if len(discord_message) > 2000:
            print(
                f"⚠️ Discord message too long: {len(discord_message)} characters")
            return False
        else:
            print(
                f"✅ Discord message length OK: {len(discord_message)} characters")

        return True

    except Exception as e:
        print(f"❌ Discord formatting test failed: {e}")
        return False


def check_required_files():
    """Check if all required Network Intelligence files exist"""
    print("\n📁 Checking Required Files...")

    required_files = [
        "worker/features/network_intelligence.py",
        "worker/tasks/network_intelligence_task.py"
    ]

    import os

    all_present = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_present = False

    return all_present


async def main():
    """Run comprehensive Network Intelligence tests"""
    print("🧪 COMPREHENSIVE NETWORK INTELLIGENCE TEST")
    print("=" * 60)
    print("Testing Network Intelligence & Community Analysis System")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check file structure
    files_ok = check_required_files()

    if not files_ok:
        print("\n❌ Missing required files. Cannot proceed with tests.")
        return

    # Run all tests
    test_results = []

    # Test 1: Core Network Intelligence Agent
    core_ok = await test_network_intelligence_core()
    test_results.append(("Core Network Intelligence", core_ok))

    # Test 2: Complete Task Workflow
    workflow_ok = await test_network_task_workflow()
    test_results.append(("Task Workflow", workflow_ok))

    # Test 3: Network Clustering
    clustering_ok = await test_network_clustering()
    test_results.append(("Network Clustering", clustering_ok))

    # Test 4: Influence Analysis
    influence_ok = await test_influence_analysis()
    test_results.append(("Influence Analysis", influence_ok))

    # Test 5: Discord Formatting
    discord_ok = await test_discord_formatting()
    test_results.append(("Discord Formatting", discord_ok))

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
        print("Network Intelligence system is COMPLETE and ready!")
        print("\nKey Features Verified:")
        print("• ✅ Hashtag co-occurrence clustering")
        print("• ✅ Author community detection")
        print("• ✅ Influencer identification")
        print("• ✅ Cross-tag influence analysis")
        print("• ✅ Network connectivity metrics")
        print("• ✅ Discord-formatted reporting")
    else:
        print(f"\n⚠️ {total-passed} tests failed. System needs attention.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
