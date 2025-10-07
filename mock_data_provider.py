#!/usr/bin/env python3
"""
Mock data provider for testing when external API is unavailable
"""

import json
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List


class MockDataProvider:
    """Mock data provider for system testing"""

    def __init__(self):
        self.trending_topics = [
            "AI", "Technology", "Innovation", "StartupLife", "TechNews",
            "MachineLearning", "DataScience", "Programming", "SoftwareEngineering",
            "DigitalTransformation", "CloudComputing", "Cybersecurity", "Blockchain",
            "IoT", "5G", "QuantumComputing", "AR", "VR", "Sustainability",
            "RemoteWork", "ProductivityHacks", "Leadership", "Marketing",
            "SocialMedia", "ContentCreation", "BrandStrategy", "CustomerExperience"
        ]
        
        self.sample_usernames = [
            "tech_guru", "ai_researcher", "startup_founder", "data_scientist",
            "code_ninja", "innovation_hub", "future_tech", "digital_nomad",
            "tech_analyst", "cloud_expert", "security_pro", "blockchain_dev"
        ]

        self.sample_content_templates = [
            "Breaking: {} technology is revolutionizing the industry! #{}",
            "Just discovered an amazing {} solution that could change everything #{}",
            "The future of {} is here, and it's incredible! #{}",
            "New research shows {} has 40% better performance #{}",
            "Game-changing {} announcement at today's conference #{}",
            "Why {} is the next big thing in technology #{}",
            "Exclusive: {} startup raises $10M Series A #{}",
            "Thread: Everything you need to know about {} 🧵 #{}"
        ]

    def generate_mock_data(self, num_posts: int = 25) -> Dict:
        """Generate mock trending data"""
        return generate_mock_trending_data(num_posts)

    def generate_temporal_dataset(self, num_posts: int = 50) -> List[Dict]:
        """Generate dataset optimized for temporal analytics testing"""
        posts = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(num_posts):
            # Distribute posts across time with realistic patterns
            hours_offset = (i * 3.7) % 168  # Spread across a week
            post_time = base_time - timedelta(hours=hours_offset)
            
            # Simulate engagement patterns based on posting time
            hour = post_time.hour
            day = post_time.weekday()
            
            # Higher engagement during peak hours and weekdays
            base_engagement = random.randint(30, 80)
            if 17 <= hour <= 19:  # Evening peak
                base_engagement *= random.uniform(2.0, 3.0)
            elif 12 <= hour <= 14:  # Lunch time
                base_engagement *= random.uniform(1.3, 1.8)
            elif 9 <= hour <= 11:  # Morning
                base_engagement *= random.uniform(1.2, 1.6)
            
            if day < 5:  # Weekdays (Monday=0, Friday=4)
                base_engagement *= random.uniform(1.2, 1.5)
            
            # Apply random variation
            total_engagement = int(base_engagement * random.uniform(0.7, 1.8))
            
            # Distribute engagement across metrics
            like_count = int(total_engagement * random.uniform(0.5, 0.7))
            reply_count = int(total_engagement * random.uniform(0.15, 0.35))
            repost_count = int(total_engagement * random.uniform(0.1, 0.25))
            
            # Select topic and author
            topic = random.choice(self.trending_topics)
            author = random.choice(self.sample_usernames)
            
            # Generate content
            template = random.choice(self.sample_content_templates)
            content = template.format(topic, topic.lower())
            
            post = {
                "id": f"temporal_post_{i:03d}",
                "created_at": post_time.isoformat(),
                "content": content,
                "like_count": like_count,
                "reply_count": reply_count,
                "repost_count": repost_count,
                "author": {
                    "username": author,
                    "follower_count": random.randint(500, 10000)
                },
                "tags": [topic.lower(), "temporal_test"],
                "engagement": {
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "repost_count": repost_count
                },
                "metadata": {
                    "created_at": post_time.isoformat(),
                    "platform": "temporal_test",
                    "hour": hour,
                    "day_of_week": day,
                    "total_engagement": like_count + reply_count + repost_count
                }
            }
            
            posts.append(post)
        
        # Sort by timestamp for realistic temporal analysis
        posts.sort(key=lambda p: p["created_at"], reverse=True)
        
        return posts


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


def generate_temporal_dataset(num_posts: int = 50) -> List[Dict]:
    """Generate dataset optimized for temporal analytics testing"""
    
    trending_topics = [
        "AI", "Technology", "Innovation", "StartupLife", "TechNews",
        "MachineLearning", "DataScience", "Programming", "SoftwareEngineering",
        "DigitalTransformation", "CloudComputing", "Cybersecurity"
    ]
    
    sample_usernames = [
        "tech_guru", "ai_researcher", "startup_founder", "data_scientist",
        "code_ninja", "innovation_hub", "future_tech", "digital_nomad"
    ]
    
    sample_content_templates = [
        "Breaking: {} technology is revolutionizing the industry! #{}",
        "Just discovered an amazing {} solution that could change everything #{}",
        "The future of {} is here, and it's incredible! #{}",
        "New research shows {} has 40% better performance #{}"
    ]
    
    posts = []
    base_time = datetime.now(timezone.utc)
    
    for i in range(num_posts):
        # Distribute posts across time with realistic patterns
        hours_offset = (i * 3.7) % 168  # Spread across a week
        post_time = base_time - timedelta(hours=hours_offset)
        
        # Simulate engagement patterns based on posting time
        hour = post_time.hour
        day = post_time.weekday()
        
        # Higher engagement during peak hours and weekdays
        base_engagement = random.randint(30, 80)
        if 17 <= hour <= 19:  # Evening peak
            base_engagement *= random.uniform(2.0, 3.0)
        elif 12 <= hour <= 14:  # Lunch time
            base_engagement *= random.uniform(1.3, 1.8)
        elif 9 <= hour <= 11:  # Morning
            base_engagement *= random.uniform(1.2, 1.6)
        
        if day < 5:  # Weekdays (Monday=0, Friday=4)
            base_engagement *= random.uniform(1.2, 1.5)
        
        # Apply random variation
        total_engagement = int(base_engagement * random.uniform(0.7, 1.8))
        
        # Distribute engagement across metrics
        like_count = int(total_engagement * random.uniform(0.5, 0.7))
        reply_count = int(total_engagement * random.uniform(0.15, 0.35))
        repost_count = int(total_engagement * random.uniform(0.1, 0.25))
        
        # Select topic and author
        topic = random.choice(trending_topics)
        author = random.choice(sample_usernames)
        
        # Generate content
        template = random.choice(sample_content_templates)
        content = template.format(topic, topic.lower())
        
        post = {
            "id": f"temporal_post_{i:03d}",
            "created_at": post_time.isoformat(),
            "content": content,
            "like_count": like_count,
            "reply_count": reply_count,
            "repost_count": repost_count,
            "author": {
                "username": author,
                "follower_count": random.randint(500, 10000)
            },
            "tags": [topic.lower(), "temporal_test"],
            "engagement": {
                "like_count": like_count,
                "reply_count": reply_count,
                "repost_count": repost_count
            },
            "metadata": {
                "created_at": post_time.isoformat(),
                "platform": "temporal_test",
                "hour": hour,
                "day_of_week": day,
                "total_engagement": like_count + reply_count + repost_count
            }
        }
        
        posts.append(post)
    
    # Sort by timestamp for realistic temporal analysis
    posts.sort(key=lambda p: p["created_at"], reverse=True)
    
    return posts


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
    
    # Also generate temporal dataset
    print(f"\n[TEMPORAL] Generating temporal dataset...")
    temporal_data = generate_temporal_dataset()
    
    with open("mock_temporal_data.json", "w", encoding="utf-8") as f:
        json.dump(temporal_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"  - Generated temporal dataset with {len(temporal_data)} posts")
    print(f"  - Saved to mock_temporal_data.json")
    print(f"  - Time span: {(datetime.fromisoformat(temporal_data[0]['created_at'].replace('Z', '+00:00')) - datetime.fromisoformat(temporal_data[-1]['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600:.1f} hours")
