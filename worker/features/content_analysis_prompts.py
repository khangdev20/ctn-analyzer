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
    
    async def generate_content_analysis_discord_report(self, posts: List[Dict]) -> Optional[str]:
        """
        Generate a Discord-ready content analysis report using AI
        
        This is the main method that implements the user's requested functionality:
        - Analyzes content quality, tone, and structure
        - Produces Discord-formatted summary with emojis and metrics
        """
        try:
            logger.info(f"[CONTENT_PROMPT] Generating Discord content analysis for {len(posts)} posts")
            
            # Prepare posts data for analysis
            posts_summary = self._prepare_posts_for_analysis(posts)
            
            system_prompt = """You are an expert social media content analyst. 

Your task is to analyze social media posts and create a Discord-ready report with specific formatting requirements.

Focus on:
1. Content quality and messaging effectiveness
2. Sentiment polarity and emotional tone analysis  
3. Narrative style and readability assessment
4. Hashtag effectiveness and usage patterns
5. Overall engagement potential

Always format your response as a Discord message with:
- Emoji headers ([TARGET], [TRENDING_UP], [CHAT], [ANALYTICS], [IDEA])
- Bullet points with key metrics
- Clear, actionable insights
- Professional but engaging tone"""

            user_prompt = f"""Analyze these social media posts and create a CONCISE Discord report (under 1500 characters):

{posts_summary}

Format:
[TARGET] **Content Analysis Summary**
• Posts analyzed: [number]
• Avg Readability: [score/100]
• Dominant Tone: [tone]
• Common Emotions: [top 3]
• Top Hashtags: [list]

� **Key Insights:**
• [2-3 bullet points with actionable recommendations]

Keep it very concise. Use emojis and bold text. Must be under 1500 characters total."""

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
                logger.info("[SUCCESS] Generated Discord content analysis report")
                return response
            else:
                logger.warning("[FALLBACK] Using basic template due to LLM failure")
                return self._generate_fallback_discord_report(posts)
                
        except Exception as e:
            logger.error(f"Content analysis prompt failed: {e}")
            return self._generate_fallback_discord_report(posts)
    
    def _prepare_posts_for_analysis(self, posts: List[Dict]) -> str:
        """Prepare posts data for LLM analysis"""
        analysis_data = []
        
        for i, post in enumerate(posts[:10], 1):  # Limit to 10 posts to avoid token limits
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
    
    def _generate_fallback_discord_report(self, posts: List[Dict]) -> str:
        """Generate basic Discord report when LLM fails"""
        total_posts = len(posts)
        avg_engagement = sum(
            post.get("engagement", {}).get("like_count", 0) + 
            post.get("engagement", {}).get("reply_count", 0) + 
            post.get("engagement", {}).get("repost_count", 0) 
            for post in posts
        ) / max(1, total_posts)
        
        # Extract hashtags
        all_tags = []
        for post in posts:
            all_tags.extend(post.get("tags", []))
        
        top_tags = list(set(all_tags))[:3] if all_tags else ["None"]
        
        timestamp = datetime.now(timezone.utc).strftime('%H:%M UTC')
        
        return f"""[TARGET] **Content Analysis Summary**
• Posts analyzed: **{total_posts}**
• Avg Engagement: **{avg_engagement:.1f}**
• Top Hashtags: {', '.join(top_tags)}

[IDEA] **Quick Insights:**
• Content variety detected
• Mixed engagement patterns
• Monitor trends for optimization

*Basic report: {timestamp}*"""

    async def generate_sentiment_analysis_prompt(self, posts: List[Dict]) -> Optional[str]:
        """Generate specialized prompt for sentiment analysis"""
        system_prompt = """You are a sentiment analysis expert for social media content.

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

        user_prompt = f"""Analyze sentiment and emotional patterns in these posts:

{posts_text}

Provide:
1. SENTIMENT_BREAKDOWN: Percentage breakdown of positive/neutral/negative
2. EMOTIONAL_THEMES: Top 3 emotional themes detected
3. PSYCHOLOGICAL_TRIGGERS: What motivates engagement
4. AUDIENCE_RESONANCE: How well content connects with audience

Format as structured analysis with clear categories."""

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

        system_prompt = """You are a hashtag strategy expert for social media marketing.

Analyze hashtag usage patterns and their correlation with engagement metrics.

Focus on:
1. Hashtag relevance to content
2. Optimal hashtag quantity 
3. Trending vs niche hashtag performance
4. Strategic hashtag recommendations"""

        hashtag_summary = "\n".join([
            f"Post: {data['content_preview']}...\nHashtags: {', '.join(data['tags'])}\nEngagement: {data['engagement']}"
            for data in hashtag_data[:10]
        ])

        user_prompt = f"""Analyze hashtag effectiveness in these posts:

{hashtag_summary}

Provide strategic analysis:
1. HASHTAG_PATTERNS: What hashtag strategies are working
2. OPTIMAL_QUANTITY: Best number of hashtags per post
3. RELEVANCE_ANALYSIS: How well hashtags match content
4. STRATEGIC_RECOMMENDATIONS: Actionable hashtag improvement tips

Focus on data-driven insights and practical recommendations."""

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
        
        system_prompt = """You are a content readability expert specializing in social media optimization.

Analyze text complexity, clarity, and accessibility of social media content.

Focus on:
1. Sentence structure and length
2. Word choice and complexity  
3. Clarity of messaging
4. Accessibility for diverse audiences"""

        posts_text = "\n\n".join([
            f"Post {i+1}:\nContent: {post.get('content', '')}\nWord Count: {post.get('word_count', 0)}\nEngagement: {sum(post.get('engagement', {}).values())}"
            for i, post in enumerate(sample_posts)
        ])

        user_prompt = f"""Analyze readability and suggest improvements for these posts:

{posts_text}

Provide structured analysis:
1. READABILITY_ASSESSMENT: Overall readability levels
2. COMPLEXITY_ISSUES: Areas that are too complex/simple
3. CLARITY_IMPROVEMENTS: Specific suggestions for clearer messaging
4. ACCESSIBILITY_TIPS: How to reach broader audiences

Give concrete, actionable recommendations for improvement."""

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