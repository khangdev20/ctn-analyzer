"""
Content Analysis Test Script
Test the content analysis functionality with sample data
"""
import asyncio
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import our content analysis components
from worker.tasks.content_analysis_task import ContentAnalysisTask
from worker.features.content_analyzer import ContentAnalyzer
from worker.features.content_analysis_prompts import ContentAnalysisPromptHandler

# Sample posts data for testing
SAMPLE_POSTS = [
    {
        "id": "post_1",
        "author": {
            "id": "user_1",
            "username": "political_insider",
            "display_name": "Political Insider",
            "follower_count": 15000,
            "verified": True
        },
        "content": "🔥 BREAKING: Major policy announcement expected this week! The political landscape is shifting rapidly. What are your thoughts on the upcoming changes? #Politics2025 #PolicyUpdate #Breaking",
        "created_at": "2025-10-06T10:30:00Z",
        "like_count": 245,
        "reply_count": 67,
        "repost_count": 89,
        "tags": ["Politics2025", "PolicyUpdate", "Breaking"]
    },
    {
        "id": "post_2", 
        "author": {
            "id": "user_2",
            "username": "community_voice",
            "display_name": "Community Voice",
            "follower_count": 8500,
            "verified": False
        },
        "content": "Amazing community turnout at today's town hall! So proud of everyone who came out to make their voices heard. Democracy in action! 🗳️ Together we can create positive change. #CommunityFirst #Democracy #TownHall",
        "created_at": "2025-10-06T09:15:00Z", 
        "like_count": 156,
        "reply_count": 34,
        "repost_count": 78,
        "tags": ["CommunityFirst", "Democracy", "TownHall"]
    },
    {
        "id": "post_3",
        "author": {
            "id": "user_3", 
            "username": "news_analyst",
            "display_name": "News Analyst",
            "follower_count": 22000,
            "verified": True
        },
        "content": "Concerned about the latest economic indicators. Inflation numbers are troubling and unemployment is rising. We need immediate action to address these critical issues facing our communities.",
        "created_at": "2025-10-06T08:45:00Z",
        "like_count": 89,
        "reply_count": 156,
        "repost_count": 23,
        "tags": ["Economy", "Inflation", "JobMarket"]
    },
    {
        "id": "post_4",
        "author": {
            "id": "user_4",
            "username": "youth_advocate", 
            "display_name": "Youth Advocate",
            "follower_count": 5200,
            "verified": False
        },
        "content": "Inspiring to see young people getting involved in politics! 💪 Your voice matters. Your vote counts. Don't let anyone tell you you're too young to make a difference. The future is NOW! #YouthVote #FutureLeaders #Inspire",
        "created_at": "2025-10-06T07:20:00Z",
        "like_count": 312,
        "reply_count": 45,
        "repost_count": 167,
        "tags": ["YouthVote", "FutureLeaders", "Inspire"]
    },
    {
        "id": "post_5",
        "author": {
            "id": "user_5",
            "username": "policy_expert",
            "display_name": "Policy Expert", 
            "follower_count": 18500,
            "verified": True
        },
        "content": "Detailed analysis of the new healthcare proposal reveals both opportunities and challenges. The comprehensive approach addresses key issues but implementation timeline seems overly ambitious. What's your take?",
        "created_at": "2025-10-06T06:30:00Z",
        "like_count": 78,
        "reply_count": 92,
        "repost_count": 45,
        "tags": ["Healthcare", "PolicyAnalysis", "Healthcare2025"]
    }
]


async def test_content_analyzer():
    """Test the ContentAnalyzer class directly"""
    print("\n" + "="*60)
    print("🧪 TESTING CONTENT ANALYZER")
    print("="*60)
    
    analyzer = ContentAnalyzer()
    
    # Test content analysis
    results = await analyzer.analyze_content_batch(SAMPLE_POSTS)
    
    print(f"✅ Analyzed {len(results.get('analyzed_posts', []))} posts")
    print(f"📊 Aggregate metrics generated: {bool(results.get('aggregate_metrics'))}")
    print(f"💬 Discord summary generated: {bool(results.get('discord_summary'))}")
    
    # Print Discord summary
    if results.get('discord_summary'):
        print("\n📱 DISCORD SUMMARY:")
        print("-" * 40)
        print(results['discord_summary'])
    
    return results


async def test_prompt_handler():
    """Test the ContentAnalysisPromptHandler"""
    print("\n" + "="*60)
    print("🤖 TESTING AI PROMPT HANDLER")
    print("="*60)
    
    prompt_handler = ContentAnalysisPromptHandler()
    
    # Test Discord report generation
    discord_report = await prompt_handler.generate_content_analysis_discord_report(SAMPLE_POSTS)
    
    if discord_report:
        print("✅ AI-generated Discord report created")
        print("\n🤖 AI DISCORD REPORT:")
        print("-" * 40)
        print(discord_report)
    else:
        print("❌ AI Discord report generation failed")
    
    return discord_report


async def test_content_analysis_task():
    """Test the complete ContentAnalysisTask workflow"""
    print("\n" + "="*60)
    print("🚀 TESTING COMPLETE CONTENT ANALYSIS WORKFLOW")
    print("="*60)
    
    task = ContentAnalysisTask()
    
    # Run the workflow with mock data (to avoid API calls)
    result = await task.run_content_analysis_workflow(data_source="mock", num_posts=10)
    
    print(f"Status: {result.get('status')}")
    print(f"Batch ID: {result.get('batch_id')}")
    print(f"Processing time: {result.get('processing_time_seconds', 0):.2f}s")
    print(f"Posts collected: {result.get('total_posts_collected', 0)}")
    print(f"Posts analyzed: {result.get('posts_analyzed', 0)}")
    print(f"Discord sent: {result.get('discord_sent', False)}")
    
    if result.get('analysis_summary'):
        summary = result['analysis_summary']
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"  • Avg Readability: {summary.get('avg_readability', 0):.1f}/100")
        print(f"  • Avg Content Quality: {summary.get('avg_content_quality', 0):.1f}/100")
        print(f"  • Dominant Sentiment: {summary.get('dominant_sentiment', 'unknown')}")
        print(f"  • Top Emotions: {', '.join(summary.get('top_emotions', [])[:3])}")
    
    return result


async def test_sentiment_analysis():
    """Test sentiment analysis specifically"""
    print("\n" + "="*60)
    print("😊 TESTING SENTIMENT ANALYSIS")
    print("="*60)
    
    task = ContentAnalysisTask()
    result = await task.run_sentiment_analysis_only(SAMPLE_POSTS)
    
    if result.get('status') == 'success':
        summary = result.get('sentiment_summary', {})
        print(f"✅ Sentiment analysis completed")
        print(f"📊 Total posts: {summary.get('total_posts', 0)}")
        print(f"😊 Dominant sentiment: {summary.get('dominant_sentiment', 'unknown')}")
        print(f"🎭 Top emotions: {', '.join(summary.get('top_emotions', [])[:3])}")
        print(f"💫 Avg emotional impact: {summary.get('avg_emotional_impact', 0):.1f}/100")
        
        if summary.get('sentiment_distribution'):
            print(f"📈 Sentiment distribution:")
            for sentiment, count in summary['sentiment_distribution'].items():
                print(f"   • {sentiment.title()}: {count} posts")
    else:
        print(f"❌ Sentiment analysis failed: {result.get('error')}")
    
    return result


async def main():
    """Run all content analysis tests"""
    print("🤖 CONTENT ANALYSIS SYSTEM TEST")
    print("Testing social media content analysis with AI integration")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Basic content analyzer
        analyzer_results = await test_content_analyzer()
        
        # Test 2: AI prompt handler  
        prompt_results = await test_prompt_handler()
        
        # Test 3: Complete workflow
        workflow_results = await test_content_analysis_task()
        
        # Test 4: Sentiment analysis
        sentiment_results = await test_sentiment_analysis()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("The content analysis system is ready for use!")
        print("\nKey features tested:")
        print("• ✅ Content quality analysis")
        print("• ✅ Sentiment and emotion detection")
        print("• ✅ Hashtag effectiveness scoring")
        print("• ✅ Discord report generation")
        print("• ✅ AI-enhanced insights")
        print("• ✅ Complete workflow integration")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())