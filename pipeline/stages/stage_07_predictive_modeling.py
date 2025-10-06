# 🟫 Stage 7: Predictive Modeling — Forecast Future Trending Posts

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import math

logger = logging.getLogger(__name__)


class PredictiveModelingStage:
    """
    Task: Predict trending probability for each post
    - Input: combined rubric, score, and growth data
    - Output: prediction JSON file (data/predict/YYYY/MM/DD/batch_<timestamp>.predict.json)
    - Steps:
      1. Merge data sources by post_id
      2. Compute trending_probability using rule-based or ML model
      3. Highlight posts with probability >= 0.8
    - Return: {post_id, trending_probability, key_factors}
    """

    def __init__(self, config):
        self.config = config
        
        # Prediction model weights (rule-based model)
        self.prediction_weights = {
            'final_score': 0.25,          # Rubric final score
            'velocity': 0.20,             # Engagement velocity
            'growth_rate': 0.15,          # Growth rate
            'engagement_ratio': 0.15,     # Engagement to follower ratio estimate
            'timing_factor': 0.10,        # Posting time optimization
            'network_factor': 0.10,       # Network amplification potential
            'content_factor': 0.05        # Content virality indicators
        }
        
        # High probability threshold
        self.high_probability_threshold = 0.8

    async def execute(self, batch_id: str, network_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute predictive modeling stage"""
        logger.info("🔮 Stage 7: Forecasting trending potential...")
        
        try:
            # Extract posts from network data (they should contain all previous stage data)
            posts = []
            if "posts" in network_data:
                posts = network_data["posts"]
            else:
                # Fallback: try to reconstruct from network analysis
                logger.warning("Posts not found in network_data, attempting to reconstruct...")
                return None
            
            predicted_posts = []
            
            for post in posts:
                # Calculate trending probability
                trending_probability = await self._calculate_trending_probability(post)
                
                # Identify key factors
                key_factors = await self._identify_key_factors(post, trending_probability)
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(post)
                
                # Add prediction data to post
                predicted_post = {
                    **post,
                    "trending_probability": round(trending_probability, 3),
                    "key_factors": key_factors,
                    "confidence_score": round(confidence_score, 3),
                    "prediction_tier": self._classify_prediction_tier(trending_probability),
                    "predicted_at": datetime.now(timezone.utc).isoformat()
                }
                
                predicted_posts.append(predicted_post)
            
            # Create prediction data structure
            prediction_data = {
                "batch_id": batch_id,
                "predicted_at": datetime.now(timezone.utc).isoformat(),
                "posts": predicted_posts,
                "prediction_model": {
                    "type": "rule_based_weighted",
                    "weights": self.prediction_weights,
                    "version": "1.0"
                },
                "metadata": {
                    "total_posts": len(predicted_posts),
                    "high_probability_threshold": self.high_probability_threshold
                }
            }
            
            # Save prediction data
            output_path = await self._save_prediction_data(prediction_data, batch_id)
            
            # Generate summary
            summary = self._generate_summary(prediction_data, batch_id)
            
            logger.info(f"✅ Stage 7 completed: Predictions for {len(predicted_posts)} posts")
            logger.info(f"🎯 High probability posts: {summary['high_probability_count']}")
            logger.info(f"📈 Average trending probability: {summary['average_probability']:.3f}")
            
            return {
                **summary,
                "prediction_data": prediction_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"❌ Stage 7 error: {e}")
            return None

    async def _calculate_trending_probability(self, post: Dict) -> float:
        """Calculate trending probability using weighted rule-based model"""
        
        # Extract features
        final_score = post.get("final_score", 0) / 100  # Normalize to 0-1
        velocity = min(1.0, post.get("velocity_per_min", 0) / 10)  # Cap at 10 for normalization
        growth_rate = min(1.0, post.get("growth_rate", 0) / 100)  # Normalize percentage
        
        # Engagement ratio (simplified - based on engagement vs content length)
        engagement = post.get("total_engagement", 0)
        content_length = max(1, post.get("content_length", 1))
        engagement_ratio = min(1.0, engagement / content_length)
        
        # Timing factor (based on posting hour analysis)
        timing_factor = self._calculate_timing_factor(post)
        
        # Network factor (based on tags, mentions, shareability)
        network_factor = self._calculate_network_factor(post)
        
        # Content factor (virality indicators)
        content_factor = self._calculate_content_factor(post)
        
        # Weighted combination
        probability = (
            final_score * self.prediction_weights['final_score'] +
            velocity * self.prediction_weights['velocity'] +
            growth_rate * self.prediction_weights['growth_rate'] +
            engagement_ratio * self.prediction_weights['engagement_ratio'] +
            timing_factor * self.prediction_weights['timing_factor'] +
            network_factor * self.prediction_weights['network_factor'] +
            content_factor * self.prediction_weights['content_factor']
        )
        
        # Apply sigmoid function for better distribution
        probability = 1 / (1 + math.exp(-5 * (probability - 0.5)))
        
        return min(1.0, max(0.0, probability))

    def _calculate_timing_factor(self, post: Dict) -> float:
        """Calculate timing factor based on posting time and velocity"""
        # Base timing score
        timing_score = 0.5
        
        # Velocity bonus (posts gaining traction quickly)
        velocity = post.get("velocity_per_min", 0)
        if velocity > 5:
            timing_score += 0.3
        elif velocity > 2:
            timing_score += 0.2
        elif velocity > 1:
            timing_score += 0.1
        
        # Growth momentum bonus
        growth_rate = post.get("growth_rate", 0)
        if growth_rate > 50:
            timing_score += 0.2
        elif growth_rate > 20:
            timing_score += 0.1
        
        return min(1.0, timing_score)

    def _calculate_network_factor(self, post: Dict) -> float:
        """Calculate network amplification factor"""
        network_score = 0.3  # Base score
        
        # Tag usage (discoverability)
        tag_count = post.get("tag_count", 0)
        if 1 <= tag_count <= 3:  # Optimal
            network_score += 0.3
        elif 4 <= tag_count <= 5:
            network_score += 0.2
        elif tag_count > 5:  # Over-optimization penalty
            network_score += 0.1
        
        # Mention usage (network effects)
        content = post.get("content", "")
        if '@' in content:
            network_score += 0.2
        
        # Repost ratio (shareability indicator)
        repost_count = post.get("repost_count", 0)
        total_engagement = max(1, post.get("total_engagement", 1))
        repost_ratio = repost_count / total_engagement
        
        if repost_ratio > 0.2:
            network_score += 0.2
        elif repost_ratio > 0.1:
            network_score += 0.1
        
        return min(1.0, network_score)

    def _calculate_content_factor(self, post: Dict) -> float:
        """Calculate content virality factor"""
        content_score = 0.4  # Base score
        content = post.get("content", "").lower()
        
        # Emotional indicators
        emotional_words = ['amazing', 'incredible', 'shocking', 'unbelievable', 'hilarious']
        if any(word in content for word in emotional_words):
            content_score += 0.2
        
        # Question format (engagement hook)
        if '?' in content:
            content_score += 0.1
        
        # Call to action
        cta_words = ['share', 'like', 'comment', 'thoughts', 'agree']
        if any(word in content for word in cta_words):
            content_score += 0.1
        
        # Length optimization
        content_length = post.get("content_length", 0)
        if 50 <= content_length <= 200:  # Sweet spot for virality
            content_score += 0.2
        
        return min(1.0, content_score)

    async def _identify_key_factors(self, post: Dict, probability: float) -> List[str]:
        """Identify key factors contributing to trending probability"""
        factors = []
        
        # High final score
        if post.get("final_score", 0) >= 70:
            factors.append("high_rubric_score")
        
        # High velocity
        if post.get("velocity_per_min", 0) > 2:
            factors.append("strong_velocity")
        
        # Growth momentum
        if post.get("growth_rate", 0) > 20:
            factors.append("growth_momentum")
        
        # High engagement
        if post.get("total_engagement", 0) > 50:
            factors.append("high_engagement")
        
        # Optimal content length
        content_length = post.get("content_length", 0)
        if 50 <= content_length <= 200:
            factors.append("optimal_length")
        
        # Good tag usage
        tag_count = post.get("tag_count", 0)
        if 1 <= tag_count <= 3:
            factors.append("optimal_tagging")
        
        # Network potential
        if '@' in post.get("content", "") or post.get("repost_count", 0) > 0:
            factors.append("network_potential")
        
        # Content quality indicators
        story_score = post.get("story_score", 0)
        if story_score >= 70:
            factors.append("quality_content")
        
        return factors

    def _calculate_confidence_score(self, post: Dict) -> float:
        """Calculate confidence in the prediction"""
        confidence = 0.5  # Base confidence
        
        # More data points increase confidence
        if post.get("velocity_per_min", 0) > 0:
            confidence += 0.1
        
        if post.get("growth_rate") is not None:
            confidence += 0.1
        
        if post.get("total_engagement", 0) > 10:  # Sufficient engagement data
            confidence += 0.2
        
        # Content analysis completeness
        if post.get("story_score", 0) > 0 and post.get("engagement_score", 0) > 0:
            confidence += 0.1
        
        # Rubric evaluation completeness
        if post.get("final_score", 0) > 0:
            confidence += 0.1
        
        return min(1.0, confidence)

    def _classify_prediction_tier(self, probability: float) -> str:
        """Classify prediction into tiers"""
        if probability >= 0.8:
            return "Very High"
        elif probability >= 0.65:
            return "High"
        elif probability >= 0.5:
            return "Moderate"
        elif probability >= 0.3:
            return "Low"
        else:
            return "Very Low"

    async def _save_prediction_data(self, data: Dict, batch_id: str) -> str:
        """Save prediction data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/predict/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.predict.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, prediction_data: Dict, batch_id: str) -> Dict:
        """Generate summary with high probability posts as specified in AI Agent Prompts"""
        posts = prediction_data.get("posts", [])
        
        if not posts:
            return {
                "batch_id": batch_id,
                "high_probability_posts": [],
                "average_probability": 0
            }
        
        # Calculate statistics
        probabilities = [post.get("trending_probability", 0) for post in posts]
        average_probability = sum(probabilities) / len(probabilities)
        
        # Get high probability posts (>= 0.8)
        high_probability_posts = [
            post for post in posts 
            if post.get("trending_probability", 0) >= self.high_probability_threshold
        ]
        
        # Sort by probability
        high_probability_posts.sort(key=lambda x: x.get("trending_probability", 0), reverse=True)
        
        # Format high probability posts for summary
        high_prob_summary = []
        for post in high_probability_posts[:10]:  # Top 10
            high_prob_summary.append({
                "post_id": post.get("id"),
                "trending_probability": post.get("trending_probability"),
                "key_factors": post.get("key_factors", []),
                "prediction_tier": post.get("prediction_tier"),
                "confidence_score": post.get("confidence_score"),
                "content_preview": post.get("content", "")[:100] + "..." if len(post.get("content", "")) > 100 else post.get("content", "")
            })
        
        # Tier distribution
        tier_distribution = {}
        for post in posts:
            tier = post.get("prediction_tier", "Unknown")
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        return {
            "batch_id": batch_id,
            "high_probability_posts": high_prob_summary,
            "high_probability_count": len(high_probability_posts),
            "average_probability": round(average_probability, 3),
            "tier_distribution": tier_distribution,
            "prediction_insights": {
                "total_predictions": len(posts),
                "very_high_tier": tier_distribution.get("Very High", 0),
                "high_tier": tier_distribution.get("High", 0),
                "actionable_posts": len([p for p in posts if p.get("trending_probability", 0) >= 0.5])
            }
        }