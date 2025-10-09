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

    def generate_strategic_dataset(self, num_posts: int = 30) -> List[Dict]:
        """Generate dataset optimized for strategic intelligence testing"""
        posts = []
        base_time = datetime.now(timezone.utc)

        # Strategic content templates with different framings
        strategic_content = {
            "attack": [
                "The corrupt {candidate} administration has failed our {issue} completely. This disaster must end!",
                "Lies and scandals from {candidate} have destroyed our trust in {issue}. Time for change!",
                "The incompetent {candidate} policies are ruining our {issue}. We need new leadership now.",
                "{candidate}'s dangerous agenda threatens our {issue}. We can't afford four more years!"
            ],
            "support": [
                "Amazing progress on {issue} under {candidate}! Our successful policies are working.",
                "Proud of {candidate}'s excellent achievements in {issue}. Great leadership delivers results.",
                "Strong {issue} growth shows {candidate}'s effective strategy is bringing prosperity.",
                "{candidate} continues to champion {issue} with dedication and results that matter."
            ],
            "call_to_action": [
                "Vote for {candidate}! Register now and make your voice heard on {issue}.",
                "Join {candidate}'s campaign! Volunteer, donate, and help spread the message on {issue}.",
                "Take action today! Support {candidate} and demand better {issue} policies.",
                "Stand with {candidate}! Share this message and fight for better {issue} solutions."
            ],
            "emotional_appeal": [
                "Our children deserve better {issue} under {candidate}. Together we can build hope.",
                "Families are struggling with {issue}. {candidate} understands and will fight for justice.",
                "The American dream depends on strong {issue}. {candidate} will restore our future.",
                "Hope for {issue} lives with {candidate}. Let's unite for freedom and prosperity."
            ]
        }

        # Strategic themes
        issues = ["economy", "healthcare", "education",
                  "immigration", "environment", "security"]
        candidates = ["CastilloReform",
                      "ProgressiveHope", "FutureFirst", "UnityNow"]

        # Authors with coordination patterns
        coordinated_authors = {
            "team_castillo1": "CastilloReform",
            "team_castillo2": "CastilloReform",
            "castillo_supporter": "CastilloReform",
            "progressive_voice1": "ProgressiveHope",
            "progressive_voice2": "ProgressiveHope",
            "future_advocate": "FutureFirst",
            "unity_supporter": "UnityNow"
        }

        individual_authors = [
            "independent_voter", "policy_expert", "citizen_advocate", "local_activist",
            "concerned_parent", "small_business", "community_leader", "veteran_voice"
        ]

        all_authors = list(coordinated_authors.keys()) + individual_authors

        for i in range(num_posts):
            # Select framing type with realistic distribution
            framing_weights = {"attack": 0.25, "support": 0.35,
                               "call_to_action": 0.20, "emotional_appeal": 0.20}
            framing = random.choices(
                list(framing_weights.keys()), weights=list(framing_weights.values()))[0]

            # Select content template and fill it
            template = random.choice(strategic_content[framing])
            issue = random.choice(issues)
            candidate = random.choice(candidates)
            content = template.format(candidate=candidate, issue=issue)

            # Select author
            author = random.choice(all_authors)

            # Coordination timing for team members
            if author in coordinated_authors:
                # Coordinated authors post closer together
                base_hours = i * 2.1
                # Within 3-hour window
                coordination_offset = random.uniform(-1.5, 1.5)
                hours_offset = base_hours + coordination_offset
            else:
                hours_offset = i * 3.2  # More spread out

            post_time = base_time - timedelta(hours=hours_offset)

            # Generate engagement metrics with some bias toward coordinated content
            base_engagement = random.randint(40, 120)
            if author in coordinated_authors:
                # Coordinated content gets more engagement
                base_engagement *= random.uniform(1.2, 1.8)

            like_count = int(base_engagement * random.uniform(0.5, 0.7))
            reply_count = int(base_engagement * random.uniform(0.15, 0.35))
            repost_count = int(base_engagement * random.uniform(0.1, 0.25))

            # Tags based on content
            tags = ["politics", "campaign", issue]
            if candidate.lower() in content.lower():
                tags.append(candidate.lower())

            post = {
                "id": f"strategic_post_{i:03d}",
                "created_at": post_time.isoformat(),
                "content": content,
                "like_count": like_count,
                "reply_count": reply_count,
                "repost_count": repost_count,
                "author": {
                    "username": author,
                    "follower_count": random.randint(800, 15000)
                },
                "tags": tags,
                "engagement": {
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "repost_count": repost_count
                },
                "metadata": {
                    "created_at": post_time.isoformat(),
                    "platform": "strategic_test",
                    "framing_type": framing,
                    "candidate_mentioned": candidate,
                    "issue_focus": issue,
                    "is_coordinated": author in coordinated_authors
                }
            }

            posts.append(post)

        # Sort by timestamp for realistic analysis
        posts.sort(key=lambda p: p["created_at"], reverse=True)

        return posts

    def generate_trending_dataset(self, count: int = 25) -> List[Dict]:
        """Generate dataset optimized for trending prediction testing"""
        posts = []

        # High-potential trending content templates
        trending_templates = [
            "[ALERT] BREAKING: {} just announced revolutionary changes! This could affect millions #{}",
            "VIRAL: {} story is spreading like wildfire across social media #{}",
            "[HOT] HOT TAKE: Why {} is about to explode in popularity #{}",
            "EXCLUSIVE: Inside sources reveal {} will transform everything #{}",
            "[FAST] URGENT: {} development could change the game forever #{}",
            "MASSIVE: {} reaches unprecedented milestone today #{}",
            "SHOCKING: {} reveals surprising truth about {} #{}",
            "MUST READ: {} expert drops truth bombs about {} #{}"
        ]

        # Viral topics for trending content
        viral_topics = [
            "AI", "Elections", "Climate", "Innovation", "Healthcare", "Economy",
            "Technology", "Social Justice", "Education", "Environment", "Politics",
            "Space", "Science", "Culture", "Sports", "Entertainment", "Finance"
        ]

        # Authors with varying influence levels
        trending_authors = [
            {"name": "viral_content_creator",
                "influence": 0.9, "engagement_boost": 15},
            {"name": "trending_influencer", "influence": 0.85, "engagement_boost": 12},
            {"name": "news_breaker", "influence": 0.8, "engagement_boost": 10},
            {"name": "thought_leader", "influence": 0.75, "engagement_boost": 8},
            {"name": "community_voice", "influence": 0.7, "engagement_boost": 6},
            {"name": "rising_creator", "influence": 0.6, "engagement_boost": 4},
            {"name": "regular_user", "influence": 0.4, "engagement_boost": 2},
            {"name": "new_account", "influence": 0.2, "engagement_boost": 0}
        ]

        for i in range(count):
            # Select author (higher influence authors more likely for trending)
            author_weights = [author["influence"]
                              for author in trending_authors]
            author = random.choices(
                trending_authors, weights=author_weights)[0]

            # Generate content with viral potential
            topic = random.choice(viral_topics)
            hashtag = topic.lower()
            template = random.choice(trending_templates)
            content = template.format(topic, hashtag, topic, hashtag)

            # Base scores with some randomness
            base_story_score = random.randint(40, 100)
            base_engagement = random.randint(30, 95)
            base_velocity = random.uniform(0.5, 10.0)
            base_timing = random.randint(35, 100)
            base_strategic = random.randint(25, 95)

            # Apply author influence boosts
            story_score = min(100, base_story_score +
                              author["engagement_boost"])
            engagement_score = min(
                100, base_engagement + author["engagement_boost"])
            velocity = min(10.0, base_velocity + (author["influence"] * 2))
            timing_score = min(100, base_timing + (author["influence"] * 10))
            strategic_score = min(100, base_strategic +
                                  author["engagement_boost"])

            # Create trending-optimized post
            post = {
                'id': f'trending_{i+1:03d}',
                'content': content,
                'author': author["name"],
                'created_at': (datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 720))).isoformat(),
                'story_score': story_score,
                'engagement_score': engagement_score,
                'velocity': round(velocity, 2),
                'network_influence': round(author["influence"], 2),
                'timing_score': timing_score,
                'strategic_score': strategic_score,
                'hashtags': [f"#{hashtag}", f"#{topic.lower()}trend", "#viral"],
                'metrics': {
                    'likes': random.randint(10, 10000),
                    'shares': random.randint(5, 5000),
                    'comments': random.randint(2, 2000),
                    'reach': random.randint(100, 50000)
                },
                'trending_factors': {
                    'viral_keywords': content.count('[ALERT]') + content.count('[HOT]') + content.count('[FAST]'),
                    'urgency_indicators': content.count('BREAKING') + content.count('URGENT') + content.count('EXCLUSIVE'),
                    'emotional_triggers': content.count('SHOCKING') + content.count('VIRAL') + content.count('MASSIVE'),
                    'engagement_signals': author["influence"] * 100
                }
            }

            posts.append(post)

        # Sort by trending potential (higher scores first)
        posts.sort(key=lambda p: p['story_score'] +
                   p['engagement_score'] + (p['velocity'] * 10), reverse=True)

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
    print(
        f"  - Time span: {(datetime.fromisoformat(temporal_data[0]['created_at'].replace('Z', '+00:00')) - datetime.fromisoformat(temporal_data[-1]['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600:.1f} hours")