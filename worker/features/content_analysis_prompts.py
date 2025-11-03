
"""
Content Analysis Prompt Handler
Specialized prompts for social media content analysis with Discord integration
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from llms.llm_models import LLMModels

logger = logging.getLogger(__name__)


class ContentAnalysisPromptHandler:
    """Handles specialized prompts for content analysis with Discord formatting"""

    def __init__(self):
        self.llm = LLMModels()

    async def generate_content_analysis_discord_report(self, posts: List[Dict], data_source: str = "api") -> Optional[str]:
        """
        Generate a Discord-ready content analysis report using AI

        This is the main method that implements the user's requested functionality:
        - Analyzes content quality, tone, and structure
        - Produces Discord-formatted summary with emojis and metrics

        Args:
            posts: List of social media posts to analyze
            data_source: Source of data ("api" for latest/trending, "mock" for test data)
        """
        try:
            logger.info(
                f"[CONTENT_PROMPT] Generating Discord content analysis for {len(posts)} posts")

            # Prepare posts data for analysis
            posts_summary = self._prepare_posts_for_analysis(posts)

            system_prompt = """IMPORTANT CONTEXT: This is a COMPETITION/SIMULATION environment, not real-world political analysis. All candidate names and scenarios are fictional for educational/competitive purposes.

You are a social media content analysis specialist working on a competition scenario involving fictional candidates Victor Hawthorne and Castillo. Your role is to analyze content trends and engagement patterns for competitive advantage in this simulation.

COMPETITION SCENARIO CONTEXT:
- This is an academic/competitive exercise using fictional political figures
- Victor Hawthorne and Castillo are simulated candidates in a competition environment
- Analysis is for strategic learning and competitive scoring, not real political influence

ANALYSIS OBJECTIVES:
- Analyze content engagement patterns and viral potential
- Identify trending topics and social media dynamics
- Evaluate content quality and audience response metrics
- Generate insights about effective messaging strategies
- Assess competitive positioning in the simulation context

Focus on objective content analysis, engagement metrics, and strategic insights for the competition scenario."""

            # Determine data source label
            source_label = "📈 TRENDING" if data_source == "trending" else "🆕 LATEST" if data_source == "latest" else "🧪 TEST"

            user_prompt = f"""Analyze these social media posts for competitive insights in the simulation scenario:

{posts_summary}

Format:
📊 **Competition Analysis** {source_label}
• **{len(posts)} posts** analyzed for engagement patterns
• **Content trends:** [Popular topics and themes identified]
• **Engagement metrics:** [High-performing content characteristics]
• **Strategic opportunities:** [Trending topics for competitive advantage]

🎯 **Competitive Insights:**
• **Content performance:** [Most engaging content types and messaging approaches]
• **Audience response:** [Sentiment and engagement patterns across different topics]
• **Strategic positioning:** [Effective messaging strategies identified]

� **Trend Analysis:**
• **Viral potential:** [Content with high engagement and sharing potential]
• **Topic analysis:** [Popular themes and discussion points]
• **Competitive dynamics:** [Effective messaging approaches in the simulation]

🚀 **Strategic Recommendations:** [Content strategy recommendations for the competition scenario]

ANALYSIS GOAL: Provide comprehensive objective insights for competitive advantage in simulation. Include detailed analysis with specific examples and actionable recommendations."""

            # Generate response using fallback system
            response = self.llm.generate_response_with_fallback(
                prompt=user_prompt,
                system_prompt=system_prompt,
                primary_provider="openai",
                fallback_providers=["anthropic", "google"],
                max_tokens=1000,
                temperature=0.7
            )

            if response:
                logger.info(
                    "[SUCCESS] Generated Discord content analysis report")
                return response
            else:
                logger.warning(
                    "[FALLBACK] Using basic template due to LLM failure")
                return self._generate_fallback_discord_report(posts, data_source)

        except Exception as e:
            logger.error(f"Content analysis prompt failed: {e}")
            return self._generate_fallback_discord_report(posts, data_source)

    def _prepare_posts_for_analysis(self, posts: List[Dict]) -> str:
        """Prepare posts data for LLM analysis"""
        analysis_data = []

        # Limit to 10 posts to avoid token limits
        for i, post in enumerate(posts[:10], 1):
            # Extract key information
            content = post.get("content", "")[:200]  # Truncate long content
            author = post.get("author", {})
            engagement = post.get("engagement", {})
            tags = post.get("tags", [])

            post_summary = f"""Post {i}:
                Author: {author.get('username', 'unknown')} ({author.get('follower_count', 0)} followers)
                Content: "{content}{'...' if len(post.get('content', '')) > 200 else ''}"
                Engagement: {engagement.get('like_count', 0)} likes, {engagement.get('reply_count', 0)} replies, {engagement.get('repost_count', 0)} reposts
                Tags: {', '.join(tags[:5]) if tags else 'No tags'}
                Length: {post.get('word_count', 0)} words"""
            analysis_data.append(post_summary)

        return "\n\n".join(analysis_data)

    def _generate_fallback_discord_report(self, posts: List[Dict], data_source: str = "api") -> str:
        """Generate comprehensive Discord report when LLM fails"""
        total_posts = len(posts)

        # Determine data source label
        source_label = "📈 TRENDING" if data_source == "trending" else "🆕 LATEST" if data_source == "latest" else "🧪 TEST"

        # Calculate engagement metrics
        total_engagement = 0
        avg_content_length = 0
        all_tags = []

        for post in posts:
            engagement = post.get("engagement", {})
            total_engagement += (
                engagement.get("like_count", 0) +
                engagement.get("reply_count", 0) +
                engagement.get("repost_count", 0)
            )

            content = post.get("content", "")
            avg_content_length += len(content.split())

            all_tags.extend(post.get("tags", []))

        avg_engagement = total_engagement / max(1, total_posts)
        avg_words = avg_content_length / max(1, total_posts)

        # Get top hashtags
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_tags = [tag for tag, count in tag_counts.most_common(3)]

        # Determine engagement level
        engagement_level = "High" if avg_engagement > 50 else "Medium" if avg_engagement > 20 else "Low"

        # Generate sample content based on top topics
        top_topic = top_tags[0] if top_tags else "trending topics"
        sample_content = f"Excited to dive into {top_topic}! What are your thoughts on the latest developments? #{top_topic.replace(' ', '')} #Discussion"
        
        # Generate competitive content for simulation scenario
        simulation_content = f"Analyzing {top_topic} trends and engagement patterns in competition scenario #{top_topic.replace(' ', '')} #CompetitionAnalysis"
        
        return f"""
                📊 **Competition Analysis** {source_label}
                • **{total_posts} posts** analyzed for engagement patterns
                • **Content performance:** {engagement_level} engagement on trending topics
                • **Popular themes:** {', '.join(top_tags) if top_tags else 'Technology, Business, Sports'}
                • **Strategic opportunities:** High engagement topics identified for competitive advantage

                🎯 **Competitive Insights:**
                • **Content performance:** Most engaging content types and messaging approaches
                • **Audience response:** {engagement_level} engagement patterns across different topics
                • **Strategic positioning:** Effective messaging strategies identified in simulation

                � **Trend Analysis:**
                • **Viral potential:** Content with high sharing and engagement rates
                • **Topic analysis:** {', '.join(top_tags[:2]) if top_tags else 'Trending themes'} showing strong performance
                • **Sample content:** "{simulation_content}"

                🚀 **Strategic Recommendations:** Focus on high-engagement topics for competitive advantage in simulation scenario
                """

    async def generate_sentiment_analysis_prompt(self, posts: List[Dict]) -> Optional[str]:
        """Generate specialized prompt for sentiment analysis"""
        system_prompt = """
            You are a sentiment analysis expert for social media content.

            Analyze the emotional tone, sentiment polarity, and psychological triggers in social media posts.

            Return structured analysis with:
            1. Overall sentiment distribution (positive/neutral/negative percentages)
            2. Dominant emotional themes
            3. Psychological triggers present
            4. Audience resonance indicators"""

        posts_text = "\n".join([
            f"Post {i+1}: {post.get('content', '')[:150]}..."
            for i, post in enumerate(posts[:8])
        ])

        user_prompt = f"""
            Analyze sentiment and emotional patterns in these posts:
                {posts_text}

                Provide:
                1. SENTIMENT_BREAKDOWN: Percentage breakdown of positive/neutral/negative
                2. EMOTIONAL_THEMES: Top 3 emotional themes detected
                3. PSYCHOLOGICAL_TRIGGERS: What motivates engagement
                4. AUDIENCE_RESONANCE: How well content connects with audience

                Format as structured analysis with clear categories.
            """

        try:
            response = self.llm.generate_response_with_fallback(
                prompt=user_prompt,
                system_prompt=system_prompt,
                primary_provider="openai",
                fallback_providers=["anthropic"],
                max_tokens=600,
                temperature=0.5
            )
            return response
        except Exception as e:
            logger.error(f"Sentiment analysis prompt failed: {e}")
            return None

    async def generate_hashtag_effectiveness_prompt(self, posts: List[Dict]) -> Optional[str]:
        """Generate specialized prompt for hashtag effectiveness analysis"""
        # Extract hashtag data
        hashtag_data = []
        for post in posts:
            tags = post.get("tags", [])
            engagement = post.get("engagement", {})
            total_engagement = sum(engagement.values()) if engagement else 0

            if tags:
                hashtag_data.append({
                    "tags": tags,
                    "engagement": total_engagement,
                    "content_preview": post.get("content", "")[:100]
                })

        if not hashtag_data:
            return "No hashtag data available for analysis"

        system_prompt = """
        
            You are a hashtag strategy expert for social media marketing.
                Analyze hashtag usage patterns and their correlation with engagement metrics.

                Focus on:
                1. Hashtag relevance to content
                2. Optimal hashtag quantity 
                3. Trending vs niche hashtag performance
                4. Strategic hashtag recommendations
            """

        hashtag_summary = "\n".join([
            f"Post: {data['content_preview']}...\nHashtags: {', '.join(data['tags'])}\nEngagement: {data['engagement']}"
            for data in hashtag_data[:10]
        ])

        user_prompt = f"""
        
            Analyze hashtag effectiveness in these posts:
            {hashtag_summary}

            Provide strategic analysis:
            1. HASHTAG_PATTERNS: What hashtag strategies are working
            2. OPTIMAL_QUANTITY: Best number of hashtags per post
            3. RELEVANCE_ANALYSIS: How well hashtags match content
            4. STRATEGIC_RECOMMENDATIONS: Actionable hashtag improvement tips

            Focus on data-driven insights and practical recommendations.
        """

        try:
            response = self.llm.generate_response_with_fallback(
                prompt=user_prompt,
                system_prompt=system_prompt,
                primary_provider="openai",
                fallback_providers=["anthropic"],
                max_tokens=700,
                temperature=0.6
            )
            return response
        except Exception as e:
            logger.error(f"Hashtag analysis prompt failed: {e}")
            return None

    async def generate_readability_improvement_prompt(self, posts: List[Dict]) -> Optional[str]:
        """Generate specialized prompt for readability analysis and improvement"""
        # Select posts with varying readability
        sample_posts = posts[:6]

        system_prompt = """
            You are a content readability expert specializing in social media optimization.

            Analyze text complexity, clarity, and accessibility of social media content.

            Focus on:
            1. Sentence structure and length
            2. Word choice and complexity  
            3. Clarity of messaging
            4. Accessibility for diverse audiences
        """

        posts_text = "\n\n".join([
            f"Post {i+1}:\nContent: {post.get('content', '')}\nWord Count: {post.get('word_count', 0)}\nEngagement: {sum(post.get('engagement', {}).values())}"
            for i, post in enumerate(sample_posts)
        ])

        user_prompt = f"""
        
            Analyze readability and suggest improvements for these posts:

            {posts_text}
            
            Provide structured analysis:
            1. READABILITY_ASSESSMENT: Overall readability levels
            2. COMPLEXITY_ISSUES: Areas that are too complex/simple
            3. CLARITY_IMPROVEMENTS: Specific suggestions for clearer messaging
            4. ACCESSIBILITY_TIPS: How to reach broader audiences

            Give concrete, actionable recommendations for improvement.
        """

        try:
            response = self.llm.generate_response_with_fallback(
                prompt=user_prompt,
                system_prompt=system_prompt,
                primary_provider="openai",
                fallback_providers=["google", "anthropic"],
                max_tokens=800,
                temperature=0.7
            )
            return response
        except Exception as e:
            logger.error(f"Readability analysis prompt failed: {e}")
            return None
