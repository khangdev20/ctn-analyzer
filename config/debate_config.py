"""
Debate Strategy Configuration - Integrated with Trending Intelligence System
"""

from typing import Dict, List
import os
from datetime import datetime, timezone


class DebateConfig:
    """Configuration management for debate strategy operations"""

    # Strategic targeting configuration
    SEARCH_TERMS = [
        "debate",
        "Kingston",
        "Victor Hawthorne",
        "election",
        "politics",
        "policy",
        "vote",
        "candidate"
    ]

    # Engagement timing configuration
    CHECK_INTERVAL_SECONDS = 300  # 5 minutes
    POST_RECENT_MINUTES = 30      # 30 minute engagement window
    REPLY_CACHE_LIMIT = 500       # Duplicate prevention cache size

    # Rate limiting and safety
    MAX_ENGAGEMENTS_PER_CYCLE = 50
    DELAY_BETWEEN_POSTS = 3       # seconds
    DELAY_BETWEEN_SEARCHES = 2    # seconds
    API_RATE_LIMIT_DELAY = 60     # seconds when hitting 429

    # Strategic priorities
    VERIFIED_ACCOUNTS_ONLY = True
    MIN_CONTENT_LENGTH = 20
    HIGH_INFLUENCE_THRESHOLD = 10000  # followers
    MEDIUM_INFLUENCE_THRESHOLD = 1000

    # Response generation settings
    MAX_RESPONSE_LENGTH = 280
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 150

    @classmethod
    def get_strategic_prompt(cls) -> str:
        """Get the strategic prompt template for LLM responses"""
        return """
        You are an AI strategic communication agent in the Kingston social simulation.
        
        STRATEGIC OBJECTIVES:
        - Build positive sentiment for Victor Hawthorne
        - Engage undecided voters with factual, respectful discourse  
        - Maintain civil tone while highlighting policy strengths
        - Drive meaningful conversation that showcases leadership qualities
        
        TACTICAL GUIDELINES:
        - Always start with @{username} and end with #TideTurning
        - Reference specific points from the original post
        - Ask engaging follow-up questions to sustain dialogue
        - Focus on policy benefits and community impact
        - Stay under 280 characters total
        
        ENGAGEMENT PSYCHOLOGY:
        - Acknowledge the other person's perspective first
        - Present Victor's position as complementary, not opposing
        - Use inclusive language ("we", "our community", "together")
        - End with invitation for further discussion
        """

    @classmethod
    def get_engagement_metrics_template(cls) -> Dict:
        """Get template for tracking engagement metrics"""
        return {
            'posts_analyzed': 0,
            'replies_sent': 0,
            'likes_given': 0,
            'reposts_made': 0,
            'errors_encountered': 0,
            'high_influence_engagements': 0,
            'medium_influence_engagements': 0,
            'verified_account_engagements': 0,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def get_discord_embed_template(cls) -> Dict:
        """Get Discord embed template for reports"""
        return {
            "title": "🤖 Debate Strategy Report",
            "description": "AI-powered social engagement analysis",
            "color": 0x00ff88,
            "fields": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Kingston AI Agent | Debate Strategy Engine"
            }
        }

    @classmethod
    def validate_environment(cls) -> List[str]:
        """Validate required environment variables"""
        required_vars = [
            'TWOOTER_PASS',
            'USERNAME',
            'TEAM_KEY',
            'OPENAI_API_KEY'
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        return missing_vars
