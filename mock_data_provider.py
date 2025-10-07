#!/usr/bin/env python3
"""
Mock data provider for testing when external API is unavailable
"""

import json
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List


def generate_mock_trending_data(num_posts: int = 20) -> Dict:
    """Generate mock trending data for testing"""

    # Sample topics and tags
    trending_topics = [
        "AI", "Technology", "Innovation", "StartupLife", "TechNews",
        "MachineLearning", "DataScience", "Programming", "SoftwareEngineering",
        "DigitalTransformation", "CloudComputing", "Cybersecurity", "Blockchain",
        "IoT", "5G", "QuantumComputing", "AR", "VR", "Sustainability"
    ]

    sample_usernames = [
        "tech_guru", "ai_researcher", "startup_founder", "data_scientist",
        "code_ninja", "innovation_hub", "future_tech", "digital_nomad",
        "tech_analyst", "cloud_expert", "security_pro", "blockchain_dev"
    ]

    sample_content_templates = [
        "Breaking: {} technology is revolutionizing the industry! #{}",
        "Just discovered an amazing {} solution that could change everything #{}",
        "The future of {} is here, and it's incredible! #{}",
        "New research shows {} has 40% better performance #{}",
        "Game-changing {} announcement at today's conference #{}",
        "Why {} is the next big thing in technology #{}",
        "Exclusive: {} startup raises $10M Series A #{}",
        "Thread: Everything you need to know about {} 🧵 #{}"
    ]

    posts = []
    base_time = datetime.now(timezone.utc)

    for i in range(num_posts):
        # Generate random engagement metrics
        like_count = random.randint(50, 2500)
        reply_count = random.randint(5, 150)
        repost_count = random.randint(10, 300)

        # Calculate engagement score based on metrics
        engagement_score = min(
            100, (like_count * 0.1 + reply_count * 2 + repost_count * 1.5) / 10)

        # Select random topic and create content
        topic = random.choice(trending_topics)
        tag = topic.lower()
        content_template = random.choice(sample_content_templates)
        content = content_template.format(topic, tag)

        # Create timestamp (last 24 hours)
        hours_ago = random.randint(1, 24)
        timestamp = (base_time - timedelta(hours=hours_ago))

        # Generate hashtags with network relationships
        hashtags = [tag, "tech", "innovation"] + \
            random.sample(trending_topics[:5], 2)
        hashtags = [h.lower() for h in hashtags]

        post = {
            "id": f"post_{i+1:03d}",
            "content": content,
            "author": {
                "username": random.choice(sample_usernames),
                "display_name": f"Tech User {i+1}",
                "verified": random.choice([True, False]),
                "follower_count": random.randint(500, 50000)
            },
            "engagement": {
                "like_count": like_count,
                "reply_count": reply_count,
                "repost_count": repost_count
            },
            # Network Intelligence format compatibility
            "like_count": like_count,
            "reply_count": reply_count,
            "repost_count": repost_count,
            "tags": hashtags,
            "created_at": timestamp.isoformat(),
            "metadata": {
                "created_at": timestamp.isoformat(),
                "hashtags": hashtags,
                "mentions": [],
                "links": []
            },
            "scores": {
                "engagement_score": round(engagement_score, 1),
                "viral_potential": round(random.uniform(20, 95), 1),
                "performance_score": round(random.uniform(30, 90), 1)
            }
        }

        posts.append(post)

    # Sort by engagement score (highest first)
    posts.sort(key=lambda x: x["scores"]["engagement_score"], reverse=True)

    # Create the full mock data structure
    mock_data = {
        "status": "success",
        "source": "mock_data_generator",
        "generated_at": base_time.isoformat(),
        "data": posts,
        "total_items": len(posts),
        "cleaned_items_count": len(posts),
        "metadata": {
            "collection_method": "mock_generation",
            "pages_collected": 1,
            "api_status": "mock_data_fallback",
            "trending_topics": trending_topics[:10],
            "sample_period": "last_24_hours"
        }
    }

    return mock_data


def save_mock_data_to_file(filename: str = "mock_trending_data.json") -> str:
    """Generate and save mock data to file"""
    mock_data = generate_mock_trending_data(25)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=2)

    print(f"[MOCK] Mock data saved to {filename}")
    print(f"[INFO] Generated {len(mock_data['data'])} mock posts")
    print(
        f"[INFO] Top post engagement: {mock_data['data'][0]['scores']['engagement_score']}%")

    return filename


if __name__ == "__main__":
    # Generate and save mock data
    filename = save_mock_data_to_file()

    # Load and display summary
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n[SUMMARY] Mock Data Generated:")
    print(f"  - Total posts: {data['total_items']}")
    print(
        f"  - Average engagement: {sum(p['scores']['engagement_score'] for p in data['data']) / len(data['data']):.1f}%")
    print(
        f"  - Top hashtags: {', '.join(data['metadata']['trending_topics'][:5])}")
    print(f"  - Generated at: {data['generated_at']}")
