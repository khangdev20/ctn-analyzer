# 🟨 Stage 4: Score Estimation — Calculate Raw Story and Engagement Scores

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import re
import math

logger = logging.getLogger(__name__)


class ScoreEstimationStage:
    """
    Task: Estimate raw Story Score and Engagement Score for each post
    - Input: cleaned post data
    - Output: score JSON file (data/score/YYYY/MM/DD/batch_<timestamp>.score.json)
    - Steps:
      1. Analyze text content for sentiment, clarity, and narrative tone
      2. Compute numeric features (likes, replies, reposts, follower count)
      3. Combine into story_score (0–100) and engagement_score (0–100)
    - Return: average story_score and engagement_score for batch
    """

    def __init__(self, config):
        self.config = config
        
        # Story scoring weights
        self.story_weights = {
            'clarity': 0.25,
            'narrative_strength': 0.30,
            'emotional_appeal': 0.20,
            'uniqueness': 0.15,
            'readability': 0.10
        }
        
        # Engagement scoring weights
        self.engagement_weights = {
            'like_ratio': 0.30,
            'reply_ratio': 0.25,
            'repost_ratio': 0.20,
            'velocity': 0.15,
            'reach_potential': 0.10
        }

    async def execute(self, batch_id: str, growth_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute score estimation stage"""
        logger.info("📈 Stage 4: Calculating performance scores...")
        
        try:
            posts = growth_data.get("posts", [])
            scored_posts = []
            
            for post in posts:
                # Calculate story score
                story_score = await self._calculate_story_score(post)
                
                # Calculate engagement score
                engagement_score = await self._calculate_engagement_score(post)
                
                # Add scores to post data
                scored_post = {
                    **post,
                    "story_score": round(story_score, 2),
                    "engagement_score": round(engagement_score, 2),
                    "combined_score": round((story_score + engagement_score) / 2, 2),
                    "score_breakdown": {
                        "story_components": await self._get_story_components(post),
                        "engagement_components": await self._get_engagement_components(post)
                    }
                }
                
                scored_posts.append(scored_post)
            
            # Create scored data structure
            scored_data = {
                "batch_id": batch_id,
                "scored_at": datetime.now(timezone.utc).isoformat(),
                "posts": scored_posts,
                "metadata": {
                    "total_posts": len(scored_posts),
                    "scoring_weights": {
                        "story_weights": self.story_weights,
                        "engagement_weights": self.engagement_weights
                    }
                }
            }
            
            # Save scored data
            output_path = await self._save_scored_data(scored_data, batch_id)
            
            # Generate summary
            summary = self._generate_summary(scored_data, batch_id)
            
            logger.info(f"✅ Stage 4 completed: Scores calculated for {len(scored_posts)} posts")
            logger.info(f"🎯 Average story score: {summary['average_story_score']:.2f}")
            logger.info(f"🎯 Average engagement score: {summary['average_engagement_score']:.2f}")
            
            return {
                **summary,
                "scored_data": scored_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"❌ Stage 4 error: {e}")
            return None

    async def _calculate_story_score(self, post: Dict) -> float:
        """Calculate story score (0-100) based on content analysis"""
        content = post.get("content", "")
        
        if not content:
            return 0
        
        # Component scores (0-100 each)
        clarity_score = self._analyze_clarity(content)
        narrative_score = self._analyze_narrative_strength(content)
        emotional_score = self._analyze_emotional_appeal(content)
        uniqueness_score = self._analyze_uniqueness(content, post)
        readability_score = self._analyze_readability(content)
        
        # Weighted combination
        story_score = (
            clarity_score * self.story_weights['clarity'] +
            narrative_score * self.story_weights['narrative_strength'] +
            emotional_score * self.story_weights['emotional_appeal'] +
            uniqueness_score * self.story_weights['uniqueness'] +
            readability_score * self.story_weights['readability']
        )
        
        return min(100, max(0, story_score))

    async def _calculate_engagement_score(self, post: Dict) -> float:
        """Calculate engagement score (0-100) based on numeric metrics"""
        
        # Get engagement metrics
        like_count = post.get("like_count", 0)
        reply_count = post.get("reply_count", 0)
        repost_count = post.get("repost_count", 0)
        total_engagement = post.get("total_engagement", 0)
        velocity = post.get("velocity_per_min", 0)
        
        # Calculate component scores (0-100 each)
        like_ratio_score = self._calculate_like_ratio_score(like_count, total_engagement)
        reply_ratio_score = self._calculate_reply_ratio_score(reply_count, total_engagement)
        repost_ratio_score = self._calculate_repost_ratio_score(repost_count, total_engagement)
        velocity_score = self._calculate_velocity_score(velocity)
        reach_score = self._calculate_reach_potential_score(post)
        
        # Weighted combination
        engagement_score = (
            like_ratio_score * self.engagement_weights['like_ratio'] +
            reply_ratio_score * self.engagement_weights['reply_ratio'] +
            repost_ratio_score * self.engagement_weights['repost_ratio'] +
            velocity_score * self.engagement_weights['velocity'] +
            reach_score * self.engagement_weights['reach_potential']
        )
        
        return min(100, max(0, engagement_score))

    def _analyze_clarity(self, content: str) -> float:
        """Analyze content clarity (0-100)"""
        if not content:
            return 0
        
        score = 50  # Base score
        
        # Positive factors
        if len(content.split()) >= 5:  # Sufficient length
            score += 10
        if '.' in content or '!' in content or '?' in content:  # Proper punctuation
            score += 10
        if content[0].isupper():  # Proper capitalization
            score += 5
        
        # Negative factors
        if len(re.findall(r'[!]{2,}', content)) > 0:  # Excessive exclamation
            score -= 10
        if len(re.findall(r'[?]{2,}', content)) > 0:  # Excessive questions
            score -= 10
        if len(re.findall(r'[A-Z]{5,}', content)) > 0:  # Excessive caps
            score -= 15
        
        return min(100, max(0, score))

    def _analyze_narrative_strength(self, content: str) -> float:
        """Analyze narrative strength and storytelling (0-100)"""
        if not content:
            return 0
        
        score = 40  # Base score
        
        # Story indicators
        story_words = ['story', 'happened', 'experience', 'remember', 'once', 'today', 'yesterday']
        if any(word in content.lower() for word in story_words):
            score += 15
        
        # Sequential indicators
        sequence_words = ['first', 'then', 'next', 'finally', 'after', 'before']
        if any(word in content.lower() for word in sequence_words):
            score += 10
        
        # Dialogue or quotes
        if '"' in content or "'" in content:
            score += 10
        
        # Personal pronouns (indicates personal narrative)
        personal_pronouns = ['i', 'me', 'my', 'we', 'us', 'our']
        pronoun_count = sum(1 for word in content.lower().split() if word in personal_pronouns)
        if pronoun_count > 0:
            score += min(15, pronoun_count * 3)
        
        return min(100, max(0, score))

    def _analyze_emotional_appeal(self, content: str) -> float:
        """Analyze emotional appeal (0-100)"""
        if not content:
            return 0
        
        score = 30  # Base score
        
        # Positive emotions
        positive_words = ['love', 'amazing', 'incredible', 'wonderful', 'happy', 'excited', 'proud']
        positive_count = sum(1 for word in content.lower().split() if word in positive_words)
        score += min(20, positive_count * 5)
        
        # Strong emotions
        strong_words = ['shocking', 'unbelievable', 'devastating', 'hilarious', 'terrifying']
        strong_count = sum(1 for word in content.lower().split() if word in strong_words)
        score += min(15, strong_count * 8)
        
        # Emotional punctuation
        if '!' in content:
            score += 10
        if '😍' in content or '❤️' in content or '😂' in content:  # Common emotional emojis
            score += 10
        
        return min(100, max(0, score))

    def _analyze_uniqueness(self, content: str, post: Dict) -> float:
        """Analyze content uniqueness (0-100)"""
        if not content:
            return 0
        
        score = 50  # Base score
        
        # Length variety
        content_length = len(content)
        if 50 <= content_length <= 200:  # Sweet spot
            score += 10
        elif content_length > 300:  # Very detailed
            score += 15
        
        # Tag usage
        tag_count = post.get("tag_count", 0)
        if 1 <= tag_count <= 3:  # Optimal tag usage
            score += 10
        elif tag_count > 5:  # Over-tagging
            score -= 10
        
        # Special content indicators
        if 'http' in content.lower():  # Contains links
            score += 5
        if '@' in content:  # Mentions others
            score += 5
        
        return min(100, max(0, score))

    def _analyze_readability(self, content: str) -> float:
        """Analyze readability (0-100)"""
        if not content:
            return 0
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        if not words:
            return 0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Average sentence length
        avg_sentence_length = len(words) / max(1, len([s for s in sentences if s.strip()]))
        
        # Scoring based on readability metrics
        score = 70  # Base score
        
        # Optimal word length (4-6 characters average)
        if 4 <= avg_word_length <= 6:
            score += 15
        elif avg_word_length > 8:
            score -= 10
        
        # Optimal sentence length (10-20 words)
        if 10 <= avg_sentence_length <= 20:
            score += 15
        elif avg_sentence_length > 30:
            score -= 15
        
        return min(100, max(0, score))

    def _calculate_like_ratio_score(self, like_count: int, total_engagement: int) -> float:
        """Calculate like ratio score (0-100)"""
        if total_engagement == 0:
            return 0
        
        like_ratio = like_count / total_engagement
        # Typical like ratio is 60-80% of total engagement
        if 0.6 <= like_ratio <= 0.8:
            return 100
        elif 0.4 <= like_ratio < 0.6:
            return 75
        elif 0.8 < like_ratio <= 0.9:
            return 85
        else:
            return 50

    def _calculate_reply_ratio_score(self, reply_count: int, total_engagement: int) -> float:
        """Calculate reply ratio score (0-100)"""
        if total_engagement == 0:
            return 0
        
        reply_ratio = reply_count / total_engagement
        # High reply ratio indicates discussion/controversy
        if 0.2 <= reply_ratio <= 0.4:
            return 100
        elif 0.1 <= reply_ratio < 0.2:
            return 80
        elif 0.4 < reply_ratio <= 0.6:
            return 90
        else:
            return 60

    def _calculate_repost_ratio_score(self, repost_count: int, total_engagement: int) -> float:
        """Calculate repost ratio score (0-100)"""
        if total_engagement == 0:
            return 0
        
        repost_ratio = repost_count / total_engagement
        # Higher repost ratio indicates shareability
        if 0.1 <= repost_ratio <= 0.3:
            return 100
        elif 0.05 <= repost_ratio < 0.1:
            return 80
        elif 0.3 < repost_ratio <= 0.5:
            return 90
        else:
            return 50

    def _calculate_velocity_score(self, velocity: float) -> float:
        """Calculate velocity score (0-100)"""
        if velocity <= 0:
            return 0
        
        # Logarithmic scaling for velocity
        velocity_score = min(100, math.log10(velocity + 1) * 25)
        return velocity_score

    def _calculate_reach_potential_score(self, post: Dict) -> float:
        """Calculate reach potential score (0-100)"""
        score = 50  # Base score
        
        # Tag usage (helps discoverability)
        tag_count = post.get("tag_count", 0)
        if tag_count > 0:
            score += min(20, tag_count * 5)
        
        # Content length (optimal for sharing)
        content_length = post.get("content_length", 0)
        if 50 <= content_length <= 200:
            score += 15
        
        # Has mentions (network effect)
        if '@' in post.get("content", ""):
            score += 10
        
        # Time factors
        if post.get("velocity_per_min", 0) > 1:
            score += 5
        
        return min(100, max(0, score))

    async def _get_story_components(self, post: Dict) -> Dict:
        """Get detailed story score components"""
        content = post.get("content", "")
        
        return {
            "clarity": round(self._analyze_clarity(content), 2),
            "narrative_strength": round(self._analyze_narrative_strength(content), 2),
            "emotional_appeal": round(self._analyze_emotional_appeal(content), 2),
            "uniqueness": round(self._analyze_uniqueness(content, post), 2),
            "readability": round(self._analyze_readability(content), 2)
        }

    async def _get_engagement_components(self, post: Dict) -> Dict:
        """Get detailed engagement score components"""
        like_count = post.get("like_count", 0)
        reply_count = post.get("reply_count", 0)
        repost_count = post.get("repost_count", 0)
        total_engagement = post.get("total_engagement", 0)
        velocity = post.get("velocity_per_min", 0)
        
        return {
            "like_ratio": round(self._calculate_like_ratio_score(like_count, total_engagement), 2),
            "reply_ratio": round(self._calculate_reply_ratio_score(reply_count, total_engagement), 2),
            "repost_ratio": round(self._calculate_repost_ratio_score(repost_count, total_engagement), 2),
            "velocity": round(self._calculate_velocity_score(velocity), 2),
            "reach_potential": round(self._calculate_reach_potential_score(post), 2)
        }

    async def _save_scored_data(self, data: Dict, batch_id: str) -> str:
        """Save scored data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/score/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.score.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, scored_data: Dict, batch_id: str) -> Dict:
        """Generate summary with average scores as specified in AI Agent Prompts"""
        posts = scored_data.get("posts", [])
        
        if not posts:
            return {
                "batch_id": batch_id,
                "average_story_score": 0,
                "average_engagement_score": 0
            }
        
        # Calculate averages
        total_story = sum(post.get("story_score", 0) for post in posts)
        total_engagement = sum(post.get("engagement_score", 0) for post in posts)
        total_combined = sum(post.get("combined_score", 0) for post in posts)
        
        avg_story = total_story / len(posts)
        avg_engagement = total_engagement / len(posts)
        avg_combined = total_combined / len(posts)
        
        # Get top scoring posts
        top_story_posts = sorted(posts, key=lambda p: p.get("story_score", 0), reverse=True)[:3]
        top_engagement_posts = sorted(posts, key=lambda p: p.get("engagement_score", 0), reverse=True)[:3]
        
        return {
            "batch_id": batch_id,
            "average_story_score": round(avg_story, 2),
            "average_engagement_score": round(avg_engagement, 2),
            "average_combined_score": round(avg_combined, 2),
            "score_distribution": {
                "high_story_posts": sum(1 for p in posts if p.get("story_score", 0) >= 70),
                "high_engagement_posts": sum(1 for p in posts if p.get("engagement_score", 0) >= 70),
                "high_combined_posts": sum(1 for p in posts if p.get("combined_score", 0) >= 70)
            },
            "top_story_posts": [{"id": p["id"], "score": p["story_score"]} for p in top_story_posts],
            "top_engagement_posts": [{"id": p["id"], "score": p["engagement_score"]} for p in top_engagement_posts]
        }