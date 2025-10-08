"""
Social Engagement Intelligence Agent
Advanced engagement growth analysis with velocity, acceleration, and Discord formatting
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class EngagementIntelligenceAgent:
    """
    Social Engagement Intelligence Agent
    
    Analyzes engagement growth patterns across two data snapshots:
    - Computes deltas (Δlikes, Δreplies, Δreposts) 
    - Calculates engagement_velocity = Δtotal_engagement / Δtime
    - Determines engagement_acceleration (velocity change rate)
    - Identifies top-5 fastest growing posts
    - Formats results as Discord messages with emojis
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_engagement_growth(self, 
                                      previous_batch: Dict, 
                                      current_batch: Dict,
                                      batch_id: str) -> Dict:
        """
        Analyze engagement growth between two data snapshots
        
        Args:
            previous_batch: Previous data snapshot with posts
            current_batch: Current data snapshot with posts  
            batch_id: Unique identifier for this analysis
            
        Returns:
            Dict with growth analysis and Discord-formatted results
        """
        try:
            self.logger.info(f"[LAUNCH] Starting engagement intelligence analysis for batch {batch_id}")
            
            # Step 1: Extract and validate posts data
            prev_posts = self._extract_posts_data(previous_batch)
            curr_posts = self._extract_posts_data(current_batch)
            
            self.logger.info(f"[ANALYTICS] Data snapshot: {len(prev_posts)} previous posts, {len(curr_posts)} current posts")
            
            # Step 2: Compute engagement deltas and velocities
            growth_analysis = await self._compute_engagement_deltas(prev_posts, curr_posts)
            
            # Step 3: Calculate engagement acceleration  
            acceleration_data = await self._compute_engagement_acceleration(growth_analysis)
            
            # Step 4: Identify top performers
            top_performers = self._identify_top_performers(acceleration_data)
            
            # Step 5: Generate engagement composition analysis
            composition_analysis = self._analyze_engagement_composition(acceleration_data)
            
            # Step 6: Format Discord message
            discord_message = self._format_discord_report(
                top_performers, 
                composition_analysis, 
                acceleration_data,
                batch_id
            )
            
            # Step 7: Compile final results
            results = {
                "batch_id": batch_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_posts_count": len(prev_posts),
                "current_posts_count": len(curr_posts),
                "matched_posts": len(acceleration_data["posts"]),
                "growth_summary": {
                    "avg_velocity_per_min": acceleration_data["avg_velocity"],
                    "avg_acceleration": acceleration_data["avg_acceleration"],
                    "total_delta_engagement": acceleration_data["total_delta"],
                    "posts_with_growth": acceleration_data["posts_with_growth"],
                    "posts_with_acceleration": acceleration_data["posts_with_acceleration"]
                },
                "top_performers": top_performers,
                "engagement_composition": composition_analysis,
                "discord_message": discord_message,
                "detailed_analysis": acceleration_data
            }
            
            self.logger.info(f"[OK] Engagement intelligence analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"[ERROR] Engagement intelligence analysis failed: {e}")
            return self._generate_error_response(batch_id, str(e))

    def _extract_posts_data(self, batch_data: Dict) -> Dict[str, Dict]:
        """Extract posts data from batch and index by ID"""
        posts = {}
        
        batch_posts = batch_data.get("posts", [])
        if not batch_posts:
            # Try alternative data structures
            batch_posts = batch_data.get("data", [])
        
        for post in batch_posts:
            try:
                post_id = str(post.get("id"))
                if not post_id:
                    continue
                    
                # Extract engagement metrics
                engagement = post.get("engagement", {})
                
                posts[post_id] = {
                    "id": post_id,
                    "like_count": max(0, engagement.get("like_count", post.get("like_count", 0))),
                    "reply_count": max(0, engagement.get("reply_count", post.get("reply_count", 0))),
                    "repost_count": max(0, engagement.get("repost_count", post.get("repost_count", 0))),
                    "follower_count": max(0, post.get("author", {}).get("follower_count", 0)),
                    "created_at": post.get("created_at", ""),
                    "collected_at": post.get("collected_at", batch_data.get("collected_at", "")),
                    "author": post.get("author", {}),
                    "content": post.get("content", "")[:100],  # Preview only
                    "total_engagement": max(0, 
                        engagement.get("like_count", post.get("like_count", 0)) +
                        engagement.get("reply_count", post.get("reply_count", 0)) +
                        engagement.get("repost_count", post.get("repost_count", 0))
                    )
                }
                
            except Exception as e:
                self.logger.warning(f"Failed to extract data for post {post.get('id', 'unknown')}: {e}")
                continue
                
        return posts

    async def _compute_engagement_deltas(self, prev_posts: Dict, curr_posts: Dict) -> Dict:
        """Compute engagement deltas and velocities"""
        growth_posts = []
        unmatched_posts = []
        
        for post_id, curr_post in curr_posts.items():
            prev_post = prev_posts.get(post_id)
            
            if prev_post:
                # Calculate deltas
                delta_likes = curr_post["like_count"] - prev_post["like_count"]
                delta_replies = curr_post["reply_count"] - prev_post["reply_count"] 
                delta_reposts = curr_post["repost_count"] - prev_post["repost_count"]
                delta_total = delta_likes + delta_replies + delta_reposts
                
                # Calculate time delta and velocity
                time_delta_minutes = self._calculate_time_delta(curr_post, prev_post)
                velocity_per_min = delta_total / max(time_delta_minutes, 1)
                
                growth_post = {
                    **curr_post,
                    "delta_likes": delta_likes,
                    "delta_replies": delta_replies,
                    "delta_reposts": delta_reposts,
                    "delta_total": delta_total,
                    "time_delta_minutes": time_delta_minutes,
                    "velocity_per_min": velocity_per_min,
                    "previous_total_engagement": prev_post["total_engagement"],
                    "growth_rate_percent": (delta_total / max(prev_post["total_engagement"], 1)) * 100
                }
                
                growth_posts.append(growth_post)
                
            else:
                # New posts - treat all engagement as growth
                unmatched_posts.append({
                    **curr_post,
                    "delta_likes": curr_post["like_count"],
                    "delta_replies": curr_post["reply_count"],
                    "delta_reposts": curr_post["repost_count"],
                    "delta_total": curr_post["total_engagement"],
                    "velocity_per_min": curr_post["total_engagement"] / max(self._calculate_post_age_minutes(curr_post), 1),
                    "is_new_post": True,
                    "previous_total_engagement": 0,
                    "growth_rate_percent": 0
                })
        
        return {
            "matched_posts": growth_posts,
            "new_posts": unmatched_posts,
            "all_posts": growth_posts + unmatched_posts
        }

    async def _compute_engagement_acceleration(self, growth_analysis: Dict) -> Dict:
        """Compute engagement acceleration (velocity change rate)"""
        all_posts = growth_analysis["all_posts"]
        
        # For acceleration, we need velocity trends - simulate with velocity vs growth rate correlation
        for post in all_posts:
            velocity = post.get("velocity_per_min", 0)
            growth_rate = post.get("growth_rate_percent", 0)
            
            # Acceleration approximation: high velocity + high growth rate = positive acceleration
            # This is a simplified model - in real implementation, you'd need multiple time points
            if velocity > 0:
                if growth_rate > 50:  # High growth rate suggests accelerating
                    acceleration = velocity * 0.1  # Positive acceleration
                elif growth_rate > 10:  # Moderate growth
                    acceleration = velocity * 0.02  # Small positive acceleration
                else:  # Low growth rate suggests slowing
                    acceleration = -velocity * 0.05  # Negative acceleration
            else:
                acceleration = 0
            
            post["acceleration"] = acceleration
            post["is_accelerating"] = acceleration > 0.1
        
        # Calculate aggregate metrics
        velocities = [p.get("velocity_per_min", 0) for p in all_posts]
        accelerations = [p.get("acceleration", 0) for p in all_posts]
        deltas = [p.get("delta_total", 0) for p in all_posts]
        
        return {
            "posts": all_posts,
            "avg_velocity": np.mean(velocities) if velocities else 0,
            "avg_acceleration": np.mean(accelerations) if accelerations else 0,
            "total_delta": sum(deltas),
            "posts_with_growth": sum(1 for p in all_posts if p.get("delta_total", 0) > 0),
            "posts_with_acceleration": sum(1 for p in all_posts if p.get("is_accelerating", False)),
            "velocity_std": np.std(velocities) if len(velocities) > 1 else 0
        }

    def _identify_top_performers(self, acceleration_data: Dict) -> List[Dict]:
        """Identify top 5 posts with fastest engagement growth"""
        posts = acceleration_data["posts"]
        
        # Sort by velocity (primary) and acceleration (secondary)
        sorted_posts = sorted(
            posts, 
            key=lambda p: (p.get("velocity_per_min", 0), p.get("acceleration", 0)), 
            reverse=True
        )
        
        top_performers = []
        for i, post in enumerate(sorted_posts[:5]):
            performer = {
                "rank": i + 1,
                "id": post["id"],
                "author": post.get("author", {}).get("username", "unknown"),
                "content_preview": post.get("content", "")[:50] + "..." if len(post.get("content", "")) > 50 else post.get("content", ""),
                "velocity_per_min": round(post.get("velocity_per_min", 0), 2),
                "acceleration": round(post.get("acceleration", 0), 3), 
                "delta_likes": post.get("delta_likes", 0),
                "delta_replies": post.get("delta_replies", 0),
                "delta_reposts": post.get("delta_reposts", 0),
                "delta_total": post.get("delta_total", 0),
                "growth_rate_percent": round(post.get("growth_rate_percent", 0), 1),
                "total_engagement": post.get("total_engagement", 0),
                "is_new_post": post.get("is_new_post", False)
            }
            top_performers.append(performer)
        
        return top_performers

    def _analyze_engagement_composition(self, acceleration_data: Dict) -> Dict:
        """Analyze engagement composition (likes, replies, reposts distribution)"""
        posts = acceleration_data["posts"]
        
        if not posts:
            return {
                "likes_percent": 0,
                "replies_percent": 0,
                "reposts_percent": 0,
                "total_deltas": 0
            }
        
        # Calculate total deltas across all posts
        total_delta_likes = sum(p.get("delta_likes", 0) for p in posts)
        total_delta_replies = sum(p.get("delta_replies", 0) for p in posts)
        total_delta_reposts = sum(p.get("delta_reposts", 0) for p in posts)
        total_delta_all = total_delta_likes + total_delta_replies + total_delta_reposts
        
        if total_delta_all == 0:
            return {
                "likes_percent": 33,
                "replies_percent": 33,
                "reposts_percent": 34,
                "total_deltas": 0
            }
        
        # Calculate percentages
        likes_percent = (total_delta_likes / total_delta_all) * 100
        replies_percent = (total_delta_replies / total_delta_all) * 100
        reposts_percent = (total_delta_reposts / total_delta_all) * 100
        
        return {
            "likes_percent": round(likes_percent),
            "replies_percent": round(replies_percent), 
            "reposts_percent": round(reposts_percent),
            "total_deltas": total_delta_all,
            "delta_breakdown": {
                "likes": total_delta_likes,
                "replies": total_delta_replies,
                "reposts": total_delta_reposts
            }
        }

    def _format_discord_report(self, 
                             top_performers: List[Dict], 
                             composition: Dict, 
                             acceleration_data: Dict,
                             batch_id: str) -> str:
        """Format results as Discord message with emojis"""
        
        avg_velocity = acceleration_data.get("avg_velocity", 0)
        total_posts = len(acceleration_data.get("posts", []))
        posts_with_growth = acceleration_data.get("posts_with_growth", 0)
        
        # Build Discord message
        message_parts = []
        
        # Header
        message_parts.append("[ANALYTICS] **Engagement Growth Report**")
        message_parts.append("")
        
        # Summary metrics
        message_parts.append(f"• **Avg Growth Velocity:** +{avg_velocity:.2f} /min")
        message_parts.append(f"• **Posts Analyzed:** {total_posts} | **Growing:** {posts_with_growth}")
        message_parts.append("")
        
        # Top performers
        if top_performers:
            message_parts.append("[LAUNCH] **Top 5 Fastest Posts:**")
            
            rank_emojis = ["[1]", "[2]", "[3]", "[4]", "[5]"]
            
            for performer in top_performers[:5]:
                rank_emoji = rank_emojis[performer["rank"] - 1]
                post_id = performer["id"]
                author = performer["author"]
                delta_likes = performer["delta_likes"]
                delta_replies = performer["delta_replies"] 
                delta_reposts = performer["delta_reposts"]
                velocity = performer["velocity_per_min"]
                
                # Build engagement details
                engagement_details = []
                if delta_likes > 0:
                    engagement_details.append(f"+{delta_likes} likes")
                if delta_replies > 0:
                    engagement_details.append(f"+{delta_replies} replies")
                if delta_reposts > 0:
                    engagement_details.append(f"+{delta_reposts} reposts")
                
                engagement_text = f" ({', '.join(engagement_details)})" if engagement_details else ""
                
                message_parts.append(f"   {rank_emoji} **@{author}** — +{velocity:.1f}/min{engagement_text}")
            
            message_parts.append("")
        
        # Engagement composition
        likes_pct = composition.get("likes_percent", 0)
        replies_pct = composition.get("replies_percent", 0) 
        reposts_pct = composition.get("reposts_percent", 0)
        
        message_parts.append("[TRENDING_UP] **Engagement Composition:**")
        message_parts.append(f"   ❤️ Likes {likes_pct}% | [CHAT] Replies {replies_pct}% | 🔁 Reposts {reposts_pct}%")
        message_parts.append("")
        
        # Additional insights
        if acceleration_data.get("posts_with_acceleration", 0) > 0:
            accel_count = acceleration_data["posts_with_acceleration"]
            message_parts.append(f"[FAST] **{accel_count} posts showing acceleration**")
        
        # Footer
        message_parts.append(f"📅 *Analysis: {batch_id}*")
        
        # Join and ensure Discord limit
        full_message = "\n".join(message_parts)
        
        # Truncate if too long (Discord 2000 char limit)
        if len(full_message) > 1900:
            full_message = full_message[:1897] + "..."
            
        return full_message

    def _calculate_time_delta(self, curr_post: Dict, prev_post: Dict) -> float:
        """Calculate time difference in minutes between measurements"""
        try:
            curr_time_str = curr_post.get("collected_at", "")
            prev_time_str = prev_post.get("collected_at", "")
            
            if not curr_time_str or not prev_time_str:
                return 15.0  # Default 15 minutes
            
            curr_time = datetime.fromisoformat(curr_time_str.replace('Z', '+00:00'))
            prev_time = datetime.fromisoformat(prev_time_str.replace('Z', '+00:00'))
            
            delta_minutes = (curr_time - prev_time).total_seconds() / 60
            return max(delta_minutes, 1.0)  # Minimum 1 minute
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate time delta: {e}")
            return 15.0  # Default fallback

    def _calculate_post_age_minutes(self, post: Dict) -> float:
        """Calculate post age in minutes"""
        try:
            created_str = post.get("created_at", "")
            if not created_str:
                return 60.0  # Default 1 hour
                
            created_time = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            age_minutes = (now - created_time).total_seconds() / 60
            return max(age_minutes, 1.0)
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate post age: {e}")
            return 60.0  # Default fallback

    def _generate_error_response(self, batch_id: str, error_message: str) -> Dict:
        """Generate error response"""
        return {
            "batch_id": batch_id,
            "error": True,
            "error_message": error_message,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "discord_message": f"[ERROR] **Engagement Analysis Failed**\n\nError: {error_message}\n\n📅 *Batch: {batch_id}*",
            "growth_summary": {
                "avg_velocity_per_min": 0,
                "avg_acceleration": 0,
                "total_delta_engagement": 0,
                "posts_with_growth": 0,
                "posts_with_acceleration": 0
            },
            "top_performers": [],
            "engagement_composition": {
                "likes_percent": 0,
                "replies_percent": 0,
                "reposts_percent": 0
            }
        }

    async def format_quick_engagement_update(self, growth_data: Dict) -> str:
        """Format a quick engagement update for real-time notifications"""
        try:
            velocity = growth_data.get("avg_velocity_per_min", 0)
            posts_growing = growth_data.get("posts_with_growth", 0)
            total_posts = len(growth_data.get("posts", []))
            
            message = f"[FAST] **Quick Engagement Update**\n"
            message += f"[ANALYTICS] Avg Velocity: +{velocity:.2f}/min\n"
            message += f"[TRENDING_UP] Growing Posts: {posts_growing}/{total_posts}\n"
            
            # Add top performer if available
            posts = growth_data.get("posts", [])
            if posts:
                top_post = max(posts, key=lambda p: p.get("velocity_per_min", 0))
                top_velocity = top_post.get("velocity_per_min", 0)
                top_author = top_post.get("author", {}).get("username", "unknown")
                
                if top_velocity > 0:
                    message += f"[LAUNCH] Fastest: @{top_author} (+{top_velocity:.1f}/min)"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to format quick update: {e}")
            return "[FAST] **Engagement Update** - Analysis in progress..."


# Utility function for standalone usage
async def analyze_engagement_snapshots(previous_data: Dict, current_data: Dict, batch_id: str = None) -> Dict:
    """
    Standalone function to analyze engagement between two data snapshots
    
    Args:
        previous_data: Previous data snapshot (JSON with posts)
        current_data: Current data snapshot (JSON with posts)
        batch_id: Optional batch identifier
        
    Returns:
        Dict with complete engagement analysis and Discord-formatted results
    """
    if not batch_id:
        batch_id = f"engagement_{int(datetime.now().timestamp())}"
    
    agent = EngagementIntelligenceAgent()
    return await agent.analyze_engagement_growth(previous_data, current_data, batch_id)