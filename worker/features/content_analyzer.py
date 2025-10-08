"""
Advanced Social Media Content Analysis Module
Provides comprehensive content quality, sentiment, and effectiveness analysis
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import Counter, defaultdict

from llms.llm_models import LLMModels

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Advanced social media content analysis with AI-powered insights"""

    def __init__(self):
        self.llm = LLMModels()

        # Sentiment keywords for basic classification
        self.positive_keywords = {
            'excited', 'amazing', 'great', 'awesome', 'love', 'fantastic',
            'incredible', 'wonderful', 'perfect', 'brilliant', 'outstanding',
            'thrilled', 'delighted', 'happy', 'joy', 'celebrate', 'victory',
            'success', 'win', 'proud', 'blessed', 'grateful', 'hope'
        }

        self.negative_keywords = {
            'terrible', 'awful', 'hate', 'disgusting', 'horrible', 'worst',
            'disaster', 'failure', 'disappointed', 'angry', 'frustrated',
            'sad', 'depressed', 'worried', 'fear', 'crisis', 'problem',
            'issue', 'concern', 'threat', 'danger', 'attack', 'corrupt'
        }

        # Emotion categories
        self.emotion_patterns = {
            'inspirational': ['inspire', 'motivate', 'dream', 'achieve', 'believe', 'overcome', 'strength'],
            'excitement': ['excited', 'thrilled', 'amazing', 'incredible', 'wow', 'fantastic'],
            'pride': ['proud', 'achievement', 'accomplish', 'success', 'victory', 'win'],
            'hope': ['hope', 'future', 'change', 'better', 'improve', 'progress'],
            'unity': ['together', 'unite', 'community', 'support', 'solidarity', 'team'],
            'concern': ['worry', 'concern', 'problem', 'issue', 'challenge', 'difficulty'],
            'anger': ['angry', 'outraged', 'disgusted', 'furious', 'mad', 'rage'],
            'fear': ['afraid', 'scared', 'worry', 'threat', 'danger', 'risk']
        }

    async def analyze_content_batch(self, posts: List[Dict]) -> Dict:
        """
        Analyze a batch of posts for content quality, sentiment, and effectiveness

        Args:
            posts: List of post dictionaries with required fields:
                   {"id", "author", "content", "created_at", "like_count", "reply_count", "repost_count", "tags"}

        Returns:
            Dictionary with individual post analyses and aggregate metrics
        """
        logger.info(
            f"[CONTENT_ANALYSIS] Starting analysis of {len(posts)} posts")

        try:
            # Analyze each post individually
            analyzed_posts = []
            for post in posts:
                analysis = await self._analyze_single_post(post)
                if analysis:
                    analyzed_posts.append(analysis)

            # Generate aggregate metrics
            aggregate_metrics = self._calculate_aggregate_metrics(
                analyzed_posts)

            # Generate Discord-ready summary
            discord_summary = self._format_discord_summary(
                analyzed_posts, aggregate_metrics)

            result = {
                "analyzed_posts": analyzed_posts,
                "aggregate_metrics": aggregate_metrics,
                "discord_summary": discord_summary,
                "analysis_metadata": {
                    "total_posts": len(posts),
                    "analyzed_posts": len(analyzed_posts),
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "success_rate": len(analyzed_posts) / len(posts) if posts else 0
                }
            }

            logger.info(
                f"[SUCCESS] Content analysis completed: {len(analyzed_posts)}/{len(posts)} posts")
            return result

        except Exception as e:
            logger.error(f"[ERROR] Content analysis failed: {e}")
            return {
                "analyzed_posts": [],
                "aggregate_metrics": {},
                "discord_summary": "[ERROR] Content analysis failed",
                "error": str(e)
            }

    async def _analyze_single_post(self, post: Dict) -> Optional[Dict]:
        """Analyze individual post for content quality metrics"""
        try:
            content = post.get("content", "").strip()
            if not content or len(content) < 10:
                return None

            # Basic text metrics
            word_count = len(content.split())
            char_count = len(content)
            sentence_count = len(re.split(r'[.!?]+', content)) - 1

            # Sentiment analysis
            sentiment_data = self._analyze_sentiment(content)

            # Emotion analysis
            emotion_data = self._analyze_emotions(content)

            # Tone analysis
            tone_data = self._analyze_tone(content)

            # Readability analysis
            readability_score = self._calculate_readability(
                content, word_count, sentence_count)

            # Content quality analysis
            content_quality = self._analyze_content_quality(
                post, content, word_count)

            # Hashtag effectiveness
            hashtag_effectiveness = self._analyze_hashtag_effectiveness(
                post.get("tags", []), content)

            # Emotional impact score
            emotional_impact = self._calculate_emotional_impact(
                sentiment_data, emotion_data, content)

            return {
                "post_id": post.get("id"),
                "author_username": post.get("author", {}).get("username", "unknown"),
                "content_preview": content[:100] + "..." if len(content) > 100 else content,

                # Core metrics
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["score"],
                "emotion": emotion_data["primary_emotion"],
                "emotion_intensity": emotion_data["intensity"],
                "tone": tone_data["tone"],
                "tone_confidence": tone_data["confidence"],

                # Scored metrics (0-100)
                "readability": min(100, max(0, readability_score)),
                "content_quality": min(100, max(0, content_quality)),
                "emotional_impact": min(100, max(0, emotional_impact)),
                "hashtag_effectiveness": min(100, max(0, hashtag_effectiveness)),

                # Additional data
                "text_metrics": {
                    "word_count": word_count,
                    "char_count": char_count,
                    "sentence_count": max(1, sentence_count),
                    "avg_word_length": sum(len(word) for word in content.split()) / max(1, word_count),
                    "hashtag_count": len(post.get("tags", []))
                },

                "engagement_data": {
                    "like_count": post.get("like_count", 0),
                    "reply_count": post.get("reply_count", 0),
                    "repost_count": post.get("repost_count", 0),
                    "total_engagement": post.get("like_count", 0) + post.get("reply_count", 0) + post.get("repost_count", 0)
                }
            }

        except Exception as e:
            logger.warning(
                f"Failed to analyze post {post.get('id', 'unknown')}: {e}")
            return None

    def _analyze_sentiment(self, content: str) -> Dict:
        """Analyze sentiment polarity using keyword-based approach"""
        content_lower = content.lower()
        words = set(re.findall(r'\b\w+\b', content_lower))

        positive_matches = len(words.intersection(self.positive_keywords))
        negative_matches = len(words.intersection(self.negative_keywords))

        # Calculate sentiment score (-1 to 1)
        if positive_matches + negative_matches == 0:
            sentiment = "neutral"
            score = 0.0
        elif positive_matches > negative_matches:
            sentiment = "positive"
            score = min(1.0, (positive_matches - negative_matches) /
                        max(1, len(words) / 10))
        elif negative_matches > positive_matches:
            sentiment = "negative"
            score = max(-1.0, (positive_matches -
                        negative_matches) / max(1, len(words) / 10))
        else:
            sentiment = "neutral"
            score = 0.0

        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "positive_signals": positive_matches,
            "negative_signals": negative_matches
        }

    def _analyze_emotions(self, content: str) -> Dict:
        """Analyze emotional content and intensity"""
        content_lower = content.lower()
        words = set(re.findall(r'\b\w+\b', content_lower))

        emotion_scores = {}
        for emotion, keywords in self.emotion_patterns.items():
            matches = len(words.intersection(set(keywords)))
            emotion_scores[emotion] = matches

        if not any(emotion_scores.values()):
            return {
                "primary_emotion": "neutral",
                "intensity": 0,
                "emotion_scores": emotion_scores
            }

        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        intensity = min(100, primary_emotion[1] * 20)  # Scale to 0-100

        return {
            "primary_emotion": primary_emotion[0],
            "intensity": intensity,
            "emotion_scores": emotion_scores
        }

    def _analyze_tone(self, content: str) -> Dict:
        """Analyze tone and voice characteristics"""
        content_lower = content.lower()

        # Tone indicators
        tone_patterns = {
            "confident": [r'\b(will|shall|definitely|certainly|absolutely)\b', r'!', r'\b(know|sure|confident)\b'],
            "questioning": [r'\?', r'\b(why|how|what|when|where|should|could|would)\b'],
            "urgent": [r'!!+', r'\b(urgent|now|immediately|asap|quickly)\b', r'\b(must|need|require)\b'],
            "casual": [r'\b(hey|hi|yeah|ok|cool|awesome)\b', r'😊|😎|👍', r'\b(gonna|wanna|gotta)\b'],
            "formal": [r'\b(furthermore|moreover|therefore|however|consequently)\b', r'\b(respectfully|sincerely)\b'],
            "emotional": [r'!!+|\?\?+', r'❤️|💕|😭|😡', r'\b(love|hate|amazing|terrible)\b']
        }

        tone_scores = {}
        for tone, patterns in tone_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower))
                score += matches
            tone_scores[tone] = score

        if not any(tone_scores.values()):
            return {"tone": "neutral", "confidence": 50, "tone_scores": tone_scores}

        primary_tone = max(tone_scores.items(), key=lambda x: x[1])
        confidence = min(100, primary_tone[1] * 25)

        return {
            "tone": primary_tone[0],
            "confidence": confidence,
            "tone_scores": tone_scores
        }

    def _calculate_readability(self, content: str, word_count: int, sentence_count: int) -> float:
        """Calculate readability score (simplified Flesch-Kincaid approach)"""
        if word_count == 0 or sentence_count == 0:
            return 50.0

        # Average sentence length
        avg_sentence_length = word_count / sentence_count

        # Average syllables per word (approximated)
        syllable_count = sum(
            max(1, len(re.findall(r'[aeiouAEIOU]', word))) for word in content.split())
        avg_syllables_per_word = syllable_count / word_count

        # Simplified readability score (higher = more readable)
        readability = 100 - (1.015 * avg_sentence_length) - \
            (84.6 * avg_syllables_per_word)

        # Normalize to 0-100 range
        return max(0, min(100, readability + 50))

    def _analyze_content_quality(self, post: Dict, content: str, word_count: int) -> float:
        """Analyze overall content quality"""
        quality_score = 50.0  # Base score

        # Length factors
        if 20 <= word_count <= 200:  # Optimal length
            quality_score += 20
        elif word_count < 10:  # Too short
            quality_score -= 30
        elif word_count > 300:  # Too long
            quality_score -= 10

        # Structure factors
        if '?' in content:  # Questions engage audience
            quality_score += 10
        if '!' in content:  # Exclamation shows enthusiasm
            quality_score += 5
        if any(char.isupper() for char in content) and not content.isupper():  # Mixed case is good
            quality_score += 5
        if content.isupper():  # All caps is bad
            quality_score -= 20

        # Engagement potential
        engagement_score = post.get(
            "like_count", 0) + post.get("reply_count", 0) + post.get("repost_count", 0)
        if engagement_score > 10:
            quality_score += min(20, engagement_score / 5)

        # Tag usage
        tag_count = len(post.get("tags", []))
        if 1 <= tag_count <= 5:  # Optimal tag count
            quality_score += 10
        elif tag_count > 10:  # Too many tags
            quality_score -= 15

        return max(0, min(100, quality_score))

    def _analyze_hashtag_effectiveness(self, tags: List[str], content: str) -> float:
        """Analyze hashtag effectiveness"""
        if not tags:
            return 30.0  # Neutral score for no hashtags

        effectiveness_score = 50.0

        # Optimal number of hashtags
        tag_count = len(tags)
        if 1 <= tag_count <= 3:
            effectiveness_score += 25
        elif 4 <= tag_count <= 7:
            effectiveness_score += 15
        elif tag_count > 10:
            effectiveness_score -= 20

        # Hashtag relevance (check if hashtag concepts appear in content)
        relevant_tags = 0
        content_lower = content.lower()
        for tag in tags:
            tag_clean = tag.lower().replace('#', '')
            if tag_clean in content_lower or any(word in content_lower for word in tag_clean.split()):
                relevant_tags += 1

        if tag_count > 0:
            relevance_ratio = relevant_tags / tag_count
            effectiveness_score += relevance_ratio * 25

        return max(0, min(100, effectiveness_score))

    def _calculate_emotional_impact(self, sentiment_data: Dict, emotion_data: Dict, content: str) -> float:
        """Calculate emotional impact score"""
        impact_score = 50.0  # Base score

        # Sentiment contribution
        sentiment_intensity = abs(sentiment_data["score"])
        impact_score += sentiment_intensity * 30

        # Emotion intensity contribution
        impact_score += emotion_data["intensity"] * 0.3

        # Emotional language indicators
        emotional_indicators = ['!', '?', '...', 'wow',
                                'amazing', 'incredible', 'unbelievable']
        for indicator in emotional_indicators:
            if indicator in content.lower():
                impact_score += 5

        # ALL CAPS reduces impact (seen as shouting)
        if content.isupper() and len(content) > 20:
            impact_score -= 20

        return max(0, min(100, impact_score))

    def _calculate_aggregate_metrics(self, analyzed_posts: List[Dict]) -> Dict:
        """Calculate aggregate metrics across all analyzed posts"""
        if not analyzed_posts:
            return {}

        # Extract all scores
        readability_scores = [post["readability"] for post in analyzed_posts]
        content_quality_scores = [post["content_quality"]
                                  for post in analyzed_posts]
        emotional_impact_scores = [post["emotional_impact"]
                                   for post in analyzed_posts]
        hashtag_effectiveness_scores = [
            post["hashtag_effectiveness"] for post in analyzed_posts]

        # Sentiment distribution
        sentiment_counts = Counter(post["sentiment"]
                                   for post in analyzed_posts)

        # Emotion distribution
        emotion_counts = Counter(post["emotion"] for post in analyzed_posts)

        # Tone distribution
        tone_counts = Counter(post["tone"] for post in analyzed_posts)

        # Top hashtags from all posts
        all_hashtags = []
        for post in analyzed_posts:
            # Extract hashtags from the original post data if available
            if "hashtag_count" in post.get("text_metrics", {}):
                # This would need to be populated from the original post data
                pass

        return {
            "total_posts_analyzed": len(analyzed_posts),

            # Average scores
            "avg_readability": round(np.mean(readability_scores), 1),
            "avg_content_quality": round(np.mean(content_quality_scores), 1),
            "avg_emotional_impact": round(np.mean(emotional_impact_scores), 1),
            "avg_hashtag_effectiveness": round(np.mean(hashtag_effectiveness_scores), 1),

            # Score distributions
            "readability_distribution": {
                "high": len([s for s in readability_scores if s >= 80]),
                "medium": len([s for s in readability_scores if 60 <= s < 80]),
                "low": len([s for s in readability_scores if s < 60])
            },

            # Sentiment analysis
            "sentiment_distribution": dict(sentiment_counts),
            "dominant_sentiment": sentiment_counts.most_common(1)[0][0] if sentiment_counts else "neutral",

            # Emotion analysis
            "emotion_distribution": dict(emotion_counts),
            "top_emotions": [emotion for emotion, count in emotion_counts.most_common(3)],

            # Tone analysis
            "tone_distribution": dict(tone_counts),
            "dominant_tone": tone_counts.most_common(1)[0][0] if tone_counts else "neutral",

            # Content characteristics
            "avg_word_count": round(np.mean([post["text_metrics"]["word_count"] for post in analyzed_posts]), 1),
            "avg_engagement": round(np.mean([post["engagement_data"]["total_engagement"] for post in analyzed_posts]), 1)
        }

    def _format_discord_summary(self, analyzed_posts: List[Dict], aggregate_metrics: Dict) -> str:
        """Format analysis results into Discord-ready message"""
        if not analyzed_posts or not aggregate_metrics:
            return "[ERROR] **Content Analysis Failed** - No data to analyze"

        # Get metrics
        total_posts = aggregate_metrics["total_posts_analyzed"]
        avg_readability = aggregate_metrics["avg_readability"]
        avg_quality = aggregate_metrics["avg_content_quality"]
        avg_impact = aggregate_metrics["avg_emotional_impact"]
        dominant_sentiment = aggregate_metrics["dominant_sentiment"]
        dominant_tone = aggregate_metrics["dominant_tone"]
        top_emotions = aggregate_metrics["top_emotions"]
        avg_engagement = aggregate_metrics["avg_engagement"]

        # Quality indicators
        quality_emoji = "[GREEN]" if avg_quality >= 70 else "[YELLOW]" if avg_quality >= 50 else "[RED]"
        sentiment_emoji = {"positive": "😊", "negative": "😔",
                           "neutral": "😐"}.get(dominant_sentiment, "😐")

        # Format top emotions
        emotion_text = ", ".join(top_emotions[:3]) if top_emotions else "Mixed"

        # Create Discord message
        discord_message = f"""[TARGET] **Content Analysis Summary**

[ANALYTICS] **Overview:**
• Posts analyzed: **{total_posts}**
• Avg Content Quality: **{avg_quality}/100** {quality_emoji}
• Avg Readability: **{avg_readability}/100**
• Avg Emotional Impact: **{avg_impact}/100**

{sentiment_emoji} **Sentiment & Tone:**
• Dominant Sentiment: **{dominant_sentiment.title()}**
• Primary Tone: **{dominant_tone.title()}**
• Top Emotions: **{emotion_text}**

[TRENDING_UP] **Engagement Metrics:**
• Average Engagement: **{avg_engagement:.1f}** interactions per post
• High-Quality Content: **{aggregate_metrics['readability_distribution']['high']}** posts (80+ readability)

[IDEA] **Quick Insights:**
"""

        # Add insights based on analysis
        insights = []

        if avg_quality >= 75:
            insights.append("[OK] Strong content quality across posts")
        elif avg_quality < 50:
            insights.append("[WARNING] Content quality needs improvement")

        if avg_readability >= 80:
            insights.append("📖 Highly readable content")
        elif avg_readability < 60:
            insights.append(
                "📚 Consider simplifying language for better readability")

        if dominant_sentiment == "positive":
            insights.append(
                "😊 Positive sentiment dominates - good for engagement")
        elif dominant_sentiment == "negative":
            insights.append("😔 High negative sentiment detected")

        if avg_impact >= 70:
            insights.append("[HOT] Strong emotional impact across posts")

        # Add insights to message
        for insight in insights[:4]:  # Limit to 4 insights
            discord_message += f"• {insight}\n"

        if not insights:
            discord_message += "• Analysis completed - mixed content performance\n"

        # Add timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        discord_message += f"\n*Report generated: {timestamp}*"

        return discord_message

    async def generate_enhanced_analysis_with_llm(self, posts: List[Dict], context: str = "social_media_analysis") -> Optional[str]:
        """Generate enhanced content analysis using LLM for deeper insights"""
        try:
            # Prepare sample posts for LLM analysis
            # Analyze top 5 posts to avoid token limits
            sample_posts = posts[:5]

            posts_text = "\n\n".join([
                f"Post {i+1}:\nAuthor: {post.get('author', {}).get('username', 'unknown')}\n"
                f"Content: {post.get('content', '')[:200]}...\n"
                f"Engagement: {post.get('like_count', 0)} likes, {post.get('reply_count', 0)} replies\n"
                f"Tags: {', '.join(post.get('tags', [])[:3])}"
                for i, post in enumerate(sample_posts)
            ])

            system_prompt = """You are an expert social media content analyst. Analyze the provided posts for:
1. Content quality and messaging effectiveness
2. Emotional tone and audience engagement potential  
3. Strategic insights and improvement recommendations
4. Trending patterns and viral potential

Provide concise, actionable insights in a professional tone."""

            user_prompt = f"""Analyze these social media posts and provide strategic insights:

{posts_text}

Focus on:
- Content strategy effectiveness
- Emotional resonance and engagement potential
- Recommended improvements
- Trending opportunities

Keep the analysis concise and actionable."""

            # Use fallback system to ensure we get a response
            response = self.llm.generate_response_with_fallback(
                prompt=user_prompt,
                system_prompt=system_prompt,
                primary_provider="openai",
                fallback_providers=["anthropic", "google"],
                max_tokens=800,
                temperature=0.7
            )

            if response:
                logger.info(
                    f"[LLM_SUCCESS] Generated enhanced content analysis")
                return response
            else:
                logger.warning(
                    "[LLM_FALLBACK] All LLM providers failed, using basic analysis")
                return None

        except Exception as e:
            logger.error(f"[LLM_ERROR] Enhanced analysis failed: {e}")
            return None
