"""
Mock Data Provider for Debate Strategy Testing

Provides sample social media posts with debate-related content
for testing the Debate Strategy AI Agent functionality.
"""

import json
import random
from datetime import datetime, timezone
from typing import List, Dict


def generate_mock_debate_posts(count: int = 20) -> List[Dict]:
    """
    Generate mock social media posts with debate-related content.

    Args:
        count: Number of posts to generate

    Returns:
        List of mock post dictionaries
    """

    # Mock debate-related posts with varying stances and engagement
    mock_posts = [
        {
            "id": "post_001",
            "content": "Castillo2025 economic policy will create 50,000 new jobs! Finally, real change for our community. #VoteForProgress",
            "like_count": 45,
            "reply_count": 12,
            "hashtags": ["#VoteForProgress", "#Jobs2025"],
            "embed_link": "https://social.legitreal.com/posts/001",
            "timestamp": "2025-10-09T10:15:00Z"
        },
        {
            "id": "post_002",
            "content": "The current debate shows politicians making empty promises. Where are the specific policy details? #DebateDay",
            "like_count": 67,
            "reply_count": 23,
            "hashtags": ["#DebateDay", "#PolicyDetails"],
            "embed_link": "https://social.legitreal.com/posts/002",
            "timestamp": "2025-10-09T09:45:00Z"
        },
        {
            "id": "post_003",
            "content": "Just watched the policy argument on healthcare. Need to see actual budget numbers, not just slogans. #Accountability",
            "like_count": 89,
            "reply_count": 34,
            "hashtags": ["#Accountability", "#Healthcare"],
            "embed_link": "https://social.legitreal.com/posts/003",
            "timestamp": "2025-10-09T09:30:00Z"
        },
        {
            "id": "post_004",
            "content": "Castillo2025 debate performance was weak. No concrete plans for infrastructure spending. Where's the evidence?",
            "like_count": 23,
            "reply_count": 8,
            "hashtags": ["#Infrastructure", "#Evidence"],
            "embed_link": "https://social.legitreal.com/posts/004",
            "timestamp": "2025-10-09T09:00:00Z"
        },
        {
            "id": "post_005",
            "content": "Best slogan of the debate: 'Data over Drama'. Finally someone talking sense about measurable outcomes!",
            "like_count": 156,
            "reply_count": 67,
            "hashtags": ["#DataOverDrama", "#MeasurableOutcomes"],
            "embed_link": "https://social.legitreal.com/posts/005",
            "timestamp": "2025-10-09T08:45:00Z"
        },
        {
            "id": "post_006",
            "content": "Political argument getting heated but no one showing real statistics. Debate should focus on facts! #FactCheck",
            "like_count": 78,
            "reply_count": 29,
            "hashtags": ["#FactCheck", "#Statistics"],
            "embed_link": "https://social.legitreal.com/posts/006",
            "timestamp": "2025-10-09T08:30:00Z"
        },
        {
            "id": "post_007",
            "content": "My morning coffee thoughts: politicians need policy workshops, not just debate practice. #PolicyWorkshop",
            "like_count": 12,
            "reply_count": 3,
            "hashtags": ["#PolicyWorkshop"],
            "embed_link": "https://social.legitreal.com/posts/007",
            "timestamp": "2025-10-09T08:15:00Z"
        },
        {
            "id": "post_008",
            "content": "Castillo2025 economic argument makes sense but where are the peer-reviewed studies? Show me the research! #Research",
            "like_count": 92,
            "reply_count": 41,
            "hashtags": ["#Research", "#Economics"],
            "embed_link": "https://social.legitreal.com/posts/008",
            "timestamp": "2025-10-09T08:00:00Z"
        },
        {
            "id": "post_009",
            "content": "Beautiful sunrise today! Perfect weather for our weekend hiking trip. Can't wait to hit the trails! #Nature",
            "like_count": 34,
            "reply_count": 8,
            "hashtags": ["#Nature", "#Hiking"],
            "embed_link": "https://social.legitreal.com/posts/009",
            "timestamp": "2025-10-09T07:45:00Z"
        },
        {
            "id": "post_010",
            "content": "Debate analysis: Strong arguments on both sides but missing fiscal impact data. Need CBO-style scoring! #FiscalAnalysis",
            "like_count": 134,
            "reply_count": 56,
            "hashtags": ["#FiscalAnalysis", "#CBO"],
            "embed_link": "https://social.legitreal.com/posts/010",
            "timestamp": "2025-10-09T07:30:00Z"
        },
        {
            "id": "post_011",
            "content": "The policy debate format needs improvement. More time for detailed argument, less for sound bites. #DebateFormat",
            "like_count": 67,
            "reply_count": 22,
            "hashtags": ["#DebateFormat", "#PolicyDetails"],
            "embed_link": "https://social.legitreal.com/posts/011",
            "timestamp": "2025-10-09T07:15:00Z"
        },
        {
            "id": "post_012",
            "content": "Excited about new restaurant opening downtown! Great reviews and the menu looks amazing. #FoodLove",
            "like_count": 18,
            "reply_count": 5,
            "hashtags": ["#FoodLove", "#Downtown"],
            "embed_link": "https://social.legitreal.com/posts/012",
            "timestamp": "2025-10-09T07:00:00Z"
        },
        {
            "id": "post_013",
            "content": "Castillo2025 slogan is catchy but substance matters more. What's the implementation timeline for these policies?",
            "like_count": 71,
            "reply_count": 28,
            "hashtags": ["#Implementation", "#Timeline"],
            "embed_link": "https://social.legitreal.com/posts/013",
            "timestamp": "2025-10-09T06:45:00Z"
        },
        {
            "id": "post_014",
            "content": "Watching kids play soccer at the park. Such pure joy and teamwork! Sport teaches great life lessons. #Soccer",
            "like_count": 25,
            "reply_count": 7,
            "hashtags": ["#Soccer", "#Kids"],
            "embed_link": "https://social.legitreal.com/posts/014",
            "timestamp": "2025-10-09T06:30:00Z"
        },
        {
            "id": "post_015",
            "content": "Policy argument tonight was intense! Both sides presented compelling cases but need more economic modeling. #EconomicModeling",
            "like_count": 103,
            "reply_count": 47,
            "hashtags": ["#EconomicModeling", "#PolicyDebate"],
            "embed_link": "https://social.legitreal.com/posts/015",
            "timestamp": "2025-10-09T06:15:00Z"
        }
    ]

    # Add some variation and randomization
    selected_posts = random.sample(mock_posts, min(count, len(mock_posts)))

    # Add engagement score calculation
    for post in selected_posts:
        post['engagement_score'] = post['like_count'] + \
            (post['reply_count'] * 2)

    return selected_posts


def save_mock_data_to_file(posts: List[Dict], filename: str = None) -> str:
    """
    Save mock posts to JSON file for testing.

    Args:
        posts: List of post dictionaries
        filename: Optional filename (auto-generated if not provided)

    Returns:
        Filename of saved data
    """
    if not filename:
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"mock_debate_posts_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "posts": posts,
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_posts": len(posts),
                "debate_posts": len([p for p in posts if any(
                    keyword in p['content'].lower()
                    for keyword in ['debate', 'policy', 'argument', 'slogan', 'castillo2025']
                )])
            }
        }, f, indent=2, ensure_ascii=False)

    return filename


def get_mock_api_response() -> Dict:
    """
    Generate a mock API response similar to the real kingstondaily endpoint.

    Returns:
        Mock API response dictionary
    """
    posts = generate_mock_debate_posts(15)

    return {
        "status": "success",
        "posts": posts,
        "pagination": {
            "total": len(posts),
            "page": 1,
            "per_page": 15
        },
        "metadata": {
            "fetch_time": datetime.now(timezone.utc).isoformat(),
            "source": "mock_data_provider"
        }
    }


if __name__ == "__main__":
    print("🎭 Mock Data Provider for Debate Strategy Agent")
    print("=" * 50)

    # Generate mock posts
    posts = generate_mock_debate_posts(15)
    print(f"Generated {len(posts)} mock posts")

    # Count debate-related posts
    debate_keywords = ['debate', 'policy',
                       'argument', 'slogan', 'castillo2025']
    debate_posts = [
        p for p in posts
        if any(keyword in p['content'].lower() for keyword in debate_keywords)
    ]
    print(f"Found {len(debate_posts)} debate-related posts")

    # Show sample posts
    print("\n📝 Sample Debate Posts:")
    for i, post in enumerate(debate_posts[:3], 1):
        print(
            f"\n{i}. [Engagement: {post['engagement_score']}] {post['content'][:80]}...")
        print(f"   Hashtags: {', '.join(post['hashtags'])}")

    # Save to file
    filename = save_mock_data_to_file(posts)
    print(f"\n💾 Mock data saved to: {filename}")

    print("\n🧪 Usage in tests:")
    print("from mock_debate_data import get_mock_api_response")
    print("mock_data = get_mock_api_response()")
