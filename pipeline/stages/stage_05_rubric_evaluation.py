# 🟥 Stage 5: Rubric Evaluation — Apply Viral Post Rubric

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RubricEvaluationStage:
    """
    Task: Evaluate each post using viral rubric weights
    - Input: story_score, engagement_score, growth metrics
    - Output: rubric JSON file (data/rubric/YYYY/MM/DD/batch_<timestamp>.rubric.json)
    - Weights:
      Content Quality: 0.30
      Engagement: 0.25
      Timing & Trend: 0.20
      Network Amplification: 0.15
      Strategy Crafting: 0.10
    - Steps:
      1. Compute weighted final_score
      2. Classify post as Trending / High Engagement / Moderate
      3. Save rubric results and log summary distribution
    - Return: average_final_score, top_posts
    """

    def __init__(self, config):
        self.config = config
        
        # Viral post rubric weights as specified in AI Agent Prompts
        self.rubric_weights = {
            'content_quality': 0.30,
            'engagement': 0.25,
            'timing_trend': 0.20,
            'network_amplification': 0.15,
            'strategy_crafting': 0.10
        }
        
        # Classification thresholds
        self.thresholds = {
            'trending': 80,      # 80+ = Trending
            'high_engagement': 65, # 65-79 = High Engagement
            'moderate': 45,      # 45-64 = Moderate
            # Below 45 = Low
        }

    async def execute(self, batch_id: str, scored_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute rubric evaluation stage"""
        logger.info("[TARGET] Stage 5: Applying viral post rubric evaluation...")
        
        try:
            posts = scored_data.get("posts", [])
            rubric_posts = []
            
            for post in posts:
                # Calculate rubric components
                rubric_components = await self._calculate_rubric_components(post)
                
                # Calculate weighted final score
                final_score = self._calculate_weighted_final_score(rubric_components)
                
                # Classify post
                classification = self._classify_post(final_score)
                
                # Add rubric evaluation to post
                rubric_post = {
                    **post,
                    "rubric_components": rubric_components,
                    "final_score": round(final_score, 2),
                    "classification": classification,
                    "viral_potential": self._assess_viral_potential(final_score, rubric_components),
                    "improvement_suggestions": await self._generate_improvement_suggestions(post, rubric_components)
                }
                
                rubric_posts.append(rubric_post)
            
            # Create rubric data structure
            rubric_data = {
                "batch_id": batch_id,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "posts": rubric_posts,
                "rubric_weights": self.rubric_weights,
                "classification_thresholds": self.thresholds,
                "metadata": {
                    "total_posts": len(rubric_posts),
                    "evaluation_version": "1.0"
                }
            }
            
            # Save rubric data
            output_path = await self._save_rubric_data(rubric_data, batch_id)
            
            # Generate summary
            summary = self._generate_summary(rubric_data, batch_id)
            
            logger.info(f"[OK] Stage 5 completed: Rubric evaluation for {len(rubric_posts)} posts")
            logger.info(f"[TARGET] Average final score: {summary['average_final_score']:.2f}")
            logger.info(f"[ANALYTICS] Classification distribution: {summary['classification_distribution']}")
            
            return {
                **summary,
                "rubric_data": rubric_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"[ERROR] Stage 5 error: {e}")
            return None

    async def _calculate_rubric_components(self, post: Dict) -> Dict:
        """Calculate all rubric components (0-100 each)"""
        
        # 1. Content Quality (30%) - Based on story score and content metrics
        content_quality = self._evaluate_content_quality(post)
        
        # 2. Engagement (25%) - Based on engagement score and metrics
        engagement = self._evaluate_engagement(post)
        
        # 3. Timing & Trend (20%) - Based on velocity and growth metrics
        timing_trend = self._evaluate_timing_trend(post)
        
        # 4. Network Amplification (15%) - Based on reach and sharing potential
        network_amplification = self._evaluate_network_amplification(post)
        
        # 5. Strategy Crafting (10%) - Based on hashtags, mentions, and optimization
        strategy_crafting = self._evaluate_strategy_crafting(post)
        
        return {
            "content_quality": round(content_quality, 2),
            "engagement": round(engagement, 2),
            "timing_trend": round(timing_trend, 2),
            "network_amplification": round(network_amplification, 2),
            "strategy_crafting": round(strategy_crafting, 2)
        }

    def _evaluate_content_quality(self, post: Dict) -> float:
        """Evaluate content quality component (0-100)"""
        # Base on story score (primary)
        story_score = post.get("story_score", 0)
        
        # Additional content quality factors
        content_length = post.get("content_length", 0)
        has_tags = post.get("has_tags", False)
        
        score = story_score  # Base score from story analysis
        
        # Length optimization bonus
        if 50 <= content_length <= 300:  # Optimal range
            score += 5
        elif content_length > 500:  # Very detailed
            score += 3
        
        # Tag usage bonus
        if has_tags:
            score += 3
        
        return min(100, max(0, score))

    def _evaluate_engagement(self, post: Dict) -> float:
        """Evaluate engagement component (0-100)"""
        # Base on engagement score (primary)
        engagement_score = post.get("engagement_score", 0)
        
        # Additional engagement factors
        total_engagement = post.get("total_engagement", 0)
        engagement_per_min = post.get("engagement_per_min", 0)
        
        score = engagement_score  # Base score
        
        # High absolute engagement bonus
        if total_engagement > 100:
            score += 10
        elif total_engagement > 50:
            score += 5
        
        # High velocity bonus
        if engagement_per_min > 5:
            score += 5
        elif engagement_per_min > 2:
            score += 3
        
        return min(100, max(0, score))

    def _evaluate_timing_trend(self, post: Dict) -> float:
        """Evaluate timing and trend component (0-100)"""
        score = 50  # Base score
        
        # Velocity factors
        velocity = post.get("velocity_per_min", 0)
        if velocity > 5:
            score += 30
        elif velocity > 2:
            score += 20
        elif velocity > 1:
            score += 10
        
        # Growth factors
        growth_rate = post.get("growth_rate", 0)
        if growth_rate > 50:  # 50%+ growth
            score += 20
        elif growth_rate > 20:
            score += 10
        elif growth_rate > 0:
            score += 5
        
        # Delta engagement
        delta_total = post.get("delta_total", 0)
        if delta_total > 20:
            score += 15
        elif delta_total > 10:
            score += 10
        elif delta_total > 0:
            score += 5
        
        return min(100, max(0, score))

    def _evaluate_network_amplification(self, post: Dict) -> float:
        """Evaluate network amplification component (0-100)"""
        score = 40  # Base score
        
        # Repost ratio (shareability)
        repost_count = post.get("repost_count", 0)
        total_engagement = post.get("total_engagement", 1)
        repost_ratio = repost_count / total_engagement
        
        if repost_ratio > 0.2:  # High shareability
            score += 25
        elif repost_ratio > 0.1:
            score += 15
        elif repost_ratio > 0.05:
            score += 10
        
        # Reply ratio (discussion generation)
        reply_count = post.get("reply_count", 0)
        reply_ratio = reply_count / total_engagement
        
        if reply_ratio > 0.3:  # High discussion
            score += 20
        elif reply_ratio > 0.15:
            score += 10
        elif reply_ratio > 0.05:
            score += 5
        
        # Mention usage (network effects)
        content = post.get("content", "")
        if '@' in content:
            score += 10
        
        # Tag reach potential
        tag_count = post.get("tag_count", 0)
        if tag_count > 0:
            score += min(15, tag_count * 3)
        
        return min(100, max(0, score))

    def _evaluate_strategy_crafting(self, post: Dict) -> float:
        """Evaluate strategy crafting component (0-100)"""
        score = 50  # Base score
        content = post.get("content", "")
        
        # Hashtag strategy
        tag_count = post.get("tag_count", 0)
        if 1 <= tag_count <= 3:  # Optimal hashtag usage
            score += 20
        elif 4 <= tag_count <= 5:
            score += 15
        elif tag_count > 5:  # Over-optimization penalty
            score -= 10
        
        # Content optimization
        content_length = post.get("content_length", 0)
        if 100 <= content_length <= 200:  # Sweet spot
            score += 15
        
        # Engagement hooks
        if '?' in content:  # Questions engage audience
            score += 10
        if '!' in content:  # Excitement/urgency
            score += 5
        
        # Call to action indicators
        cta_words = ['check', 'follow', 'share', 'like', 'comment', 'thoughts']
        if any(word in content.lower() for word in cta_words):
            score += 10
        
        # Timing optimization (posting at optimal times - would need more data)
        # For now, bonus for posts with immediate engagement
        if post.get("engagement_per_min", 0) > 1:
            score += 10
        
        return min(100, max(0, score))

    def _calculate_weighted_final_score(self, components: Dict) -> float:
        """Calculate weighted final score using rubric weights"""
        final_score = (
            components["content_quality"] * self.rubric_weights["content_quality"] +
            components["engagement"] * self.rubric_weights["engagement"] +
            components["timing_trend"] * self.rubric_weights["timing_trend"] +
            components["network_amplification"] * self.rubric_weights["network_amplification"] +
            components["strategy_crafting"] * self.rubric_weights["strategy_crafting"]
        )
        
        return final_score

    def _classify_post(self, final_score: float) -> str:
        """Classify post based on final score"""
        if final_score >= self.thresholds["trending"]:
            return "Trending"
        elif final_score >= self.thresholds["high_engagement"]:
            return "High Engagement"
        elif final_score >= self.thresholds["moderate"]:
            return "Moderate"
        else:
            return "Low"

    def _assess_viral_potential(self, final_score: float, components: Dict) -> Dict:
        """Assess viral potential and identify key factors"""
        potential = "Low"
        key_factors = []
        
        if final_score >= 80:
            potential = "Very High"
        elif final_score >= 70:
            potential = "High"
        elif final_score >= 60:
            potential = "Moderate"
        elif final_score >= 50:
            potential = "Low-Moderate"
        
        # Identify top performing components
        sorted_components = sorted(components.items(), key=lambda x: x[1], reverse=True)
        key_factors = [comp[0] for comp in sorted_components[:2]]
        
        return {
            "level": potential,
            "score": final_score,
            "key_strengths": key_factors,
            "recommendations": self._get_viral_recommendations(final_score, components)
        }

    def _get_viral_recommendations(self, final_score: float, components: Dict) -> List[str]:
        """Get recommendations for increasing viral potential"""
        recommendations = []
        
        # Find weakest components
        sorted_components = sorted(components.items(), key=lambda x: x[1])
        
        for component, score in sorted_components:
            if score < 60:  # Room for improvement
                if component == "content_quality":
                    recommendations.append("Improve content clarity and narrative strength")
                elif component == "engagement":
                    recommendations.append("Focus on creating more engaging, interactive content")
                elif component == "timing_trend":
                    recommendations.append("Post during peak engagement hours and leverage trending topics")
                elif component == "network_amplification":
                    recommendations.append("Increase shareability with compelling hooks and mentions")
                elif component == "strategy_crafting":
                    recommendations.append("Optimize hashtag usage and include clear calls-to-action")
        
        if final_score < 70:
            recommendations.append("Consider trending topics and current events for better timing")
        
        return recommendations[:3]  # Top 3 recommendations

    async def _generate_improvement_suggestions(self, post: Dict, components: Dict) -> List[str]:
        """Generate specific improvement suggestions for the post"""
        suggestions = []
        
        # Content quality improvements
        if components["content_quality"] < 70:
            if post.get("content_length", 0) < 50:
                suggestions.append("Expand content with more details or context")
            if not post.get("has_tags", False):
                suggestions.append("Add 1-3 relevant hashtags for better discoverability")
        
        # Engagement improvements
        if components["engagement"] < 60:
            suggestions.append("Add questions or calls-to-action to encourage interaction")
            if '@' not in post.get("content", ""):
                suggestions.append("Consider mentioning relevant accounts to increase reach")
        
        # Timing improvements
        if components["timing_trend"] < 50:
            suggestions.append("Monitor trending topics and align content timing")
        
        return suggestions[:3]  # Limit to top 3 suggestions

    async def _save_rubric_data(self, data: Dict, batch_id: str) -> str:
        """Save rubric data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/rubric/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.rubric.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, rubric_data: Dict, batch_id: str) -> Dict:
        """Generate summary with average final score and top posts as specified in AI Agent Prompts"""
        posts = rubric_data.get("posts", [])
        
        if not posts:
            return {
                "batch_id": batch_id,
                "average_final_score": 0,
                "top_posts": []
            }
        
        # Calculate average final score
        total_score = sum(post.get("final_score", 0) for post in posts)
        average_final_score = total_score / len(posts)
        
        # Classification distribution
        classification_counts = {}
        for post in posts:
            classification = post.get("classification", "Unknown")
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
        
        # Get top posts by final score
        top_posts = sorted(posts, key=lambda p: p.get("final_score", 0), reverse=True)[:5]
        top_posts_summary = []
        
        for post in top_posts:
            top_posts_summary.append({
                "id": post.get("id"),
                "final_score": post.get("final_score"),
                "classification": post.get("classification"),
                "viral_potential": post.get("viral_potential", {}).get("level"),
                "content_preview": post.get("content", "")[:100] + "..." if len(post.get("content", "")) > 100 else post.get("content", "")
            })
        
        return {
            "batch_id": batch_id,
            "average_final_score": round(average_final_score, 2),
            "top_posts": top_posts_summary,
            "classification_distribution": classification_counts,
            "viral_candidates": len([p for p in posts if p.get("final_score", 0) >= 80]),
            "high_potential_posts": len([p for p in posts if p.get("final_score", 0) >= 70]),
            "component_averages": {
                "content_quality": round(sum(p.get("rubric_components", {}).get("content_quality", 0) for p in posts) / len(posts), 2),
                "engagement": round(sum(p.get("rubric_components", {}).get("engagement", 0) for p in posts) / len(posts), 2),
                "timing_trend": round(sum(p.get("rubric_components", {}).get("timing_trend", 0) for p in posts) / len(posts), 2),
                "network_amplification": round(sum(p.get("rubric_components", {}).get("network_amplification", 0) for p in posts) / len(posts), 2),
                "strategy_crafting": round(sum(p.get("rubric_components", {}).get("strategy_crafting", 0) for p in posts) / len(posts), 2)
            }
        }