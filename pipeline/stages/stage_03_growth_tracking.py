# 🟧 Stage 3: Growth Tracking — Compute Engagement Growth and Velocity

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GrowthTrackingStage:
    """
    Task: Compute engagement deltas and growth velocity between current and previous batches
    - Input: cleaned batch JSONs (current and previous)
    - Output: growth JSON file (data/growth/YYYY/MM/DD/batch_<timestamp>.growth.json)
    - Steps:
      1. Join datasets by post_id
      2. Calculate Δlikes, Δreplies, Δreposts, Δtotal
      3. Compute velocity = delta_total / delta_time
      4. Save and log top 5 velocity posts
    - Return: summary dict {avg_velocity_per_min, top_velocity_posts}
    """

    def __init__(self, config):
        self.config = config

    async def execute(self, batch_id: str, cleaned_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute growth tracking stage"""
        logger.info("📈 Stage 3: Computing engagement growth and velocity...")
        
        try:
            current_posts = cleaned_data.get("posts", [])
            
            # Find previous batch data
            previous_data = await self._load_previous_batch_data(batch_id)
            
            if not previous_data:
                logger.info("📊 No previous batch data found - computing baseline metrics")
                growth_data = await self._compute_baseline_metrics(current_posts, batch_id)
            else:
                # Compute growth deltas with previous batch
                growth_data = await self._compute_growth_deltas(current_posts, previous_data, batch_id)
            
            # Save growth data
            output_path = await self._save_growth_data(growth_data, batch_id)
            
            # Generate summary
            summary = self._generate_summary(growth_data, batch_id)
            
            logger.info(f"✅ Stage 3 completed: Growth analysis for {len(growth_data.get('posts', []))} posts")
            logger.info(f"📁 Growth data saved to: {output_path}")
            
            return {
                **summary,
                "growth_data": growth_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"❌ Stage 3 error: {e}")
            return None

    async def _load_previous_batch_data(self, current_batch_id: str) -> Optional[Dict]:
        """Load the most recent previous batch for comparison"""
        try:
            # Look for previous batch files in data/clean directory
            now = datetime.now(timezone.utc)
            base_dir = "data/clean"
            
            # Search recent directories (last 3 days)
            for days_back in range(1, 4):
                search_date = now.replace(day=now.day - days_back)
                dir_path = f"{base_dir}/{search_date.year:04d}/{search_date.month:02d}/{search_date.day:02d}"
                
                if os.path.exists(dir_path):
                    # Find most recent batch file in this directory
                    batch_files = [f for f in os.listdir(dir_path) if f.endswith('.clean.json')]
                    if batch_files:
                        # Sort by filename (batch_id) and take the most recent
                        batch_files.sort(reverse=True)
                        latest_file = os.path.join(dir_path, batch_files[0])
                        
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            previous_data = json.load(f)
                        
                        logger.info(f"📊 Found previous batch: {previous_data.get('batch_id')}")
                        return previous_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to load previous batch data: {e}")
            return None

    async def _compute_baseline_metrics(self, posts: List[Dict], batch_id: str) -> Dict:
        """Compute baseline metrics when no previous data exists"""
        baseline_posts = []
        
        for post in posts:
            baseline_post = {
                **post,
                # Growth deltas (all zero for baseline)
                "delta_likes": 0,
                "delta_replies": 0,
                "delta_reposts": 0,
                "delta_total": 0,
                "velocity_per_min": 0,
                "growth_rate": 0,
                "is_baseline": True,
                "previous_total_engagement": 0
            }
            baseline_posts.append(baseline_post)
        
        return {
            "batch_id": batch_id,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "is_baseline": True,
            "posts": baseline_posts,
            "metadata": {
                "current_count": len(posts),
                "previous_count": 0,
                "matched_posts": 0,
                "new_posts": len(posts)
            }
        }

    async def _compute_growth_deltas(self, current_posts: List[Dict], previous_data: Dict, batch_id: str) -> Dict:
        """Compute growth deltas between current and previous batch"""
        previous_posts = {p["id"]: p for p in previous_data.get("posts", [])}
        growth_posts = []
        
        for current_post in current_posts:
            post_id = current_post.get("id")
            previous_post = previous_posts.get(post_id)
            
            if previous_post:
                # Calculate deltas
                delta_likes = current_post.get("like_count", 0) - previous_post.get("like_count", 0)
                delta_replies = current_post.get("reply_count", 0) - previous_post.get("reply_count", 0)
                delta_reposts = current_post.get("repost_count", 0) - previous_post.get("repost_count", 0)
                delta_total = delta_likes + delta_replies + delta_reposts
                
                # Calculate velocity (delta per minute)
                velocity_per_min = self._calculate_velocity(current_post, previous_post, delta_total)
                
                # Calculate growth rate
                prev_total = previous_post.get("total_engagement", 1)
                growth_rate = (delta_total / prev_total * 100) if prev_total > 0 else 0
                
                growth_post = {
                    **current_post,
                    "delta_likes": delta_likes,
                    "delta_replies": delta_replies,
                    "delta_reposts": delta_reposts,
                    "delta_total": delta_total,
                    "velocity_per_min": round(velocity_per_min, 2),
                    "growth_rate": round(growth_rate, 2),
                    "is_baseline": False,
                    "previous_total_engagement": prev_total,
                    "time_since_previous": self._calculate_time_delta(current_post, previous_post)
                }
            else:
                # New post (no previous data)
                growth_post = {
                    **current_post,
                    "delta_likes": current_post.get("like_count", 0),
                    "delta_replies": current_post.get("reply_count", 0),
                    "delta_reposts": current_post.get("repost_count", 0),
                    "delta_total": current_post.get("total_engagement", 0),
                    "velocity_per_min": current_post.get("engagement_per_min", 0),
                    "growth_rate": 0,
                    "is_baseline": False,
                    "is_new_post": True,
                    "previous_total_engagement": 0
                }
            
            growth_posts.append(growth_post)
        
        return {
            "batch_id": batch_id,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "is_baseline": False,
            "previous_batch_id": previous_data.get("batch_id"),
            "posts": growth_posts,
            "metadata": {
                "current_count": len(current_posts),
                "previous_count": len(previous_data.get("posts", [])),
                "matched_posts": sum(1 for p in growth_posts if not p.get("is_new_post", False)),
                "new_posts": sum(1 for p in growth_posts if p.get("is_new_post", False))
            }
        }

    def _calculate_velocity(self, current_post: Dict, previous_post: Dict, delta_total: int) -> float:
        """Calculate velocity = delta_total / delta_time"""
        try:
            current_time = datetime.fromisoformat(current_post.get("collected_at", "").replace('Z', '+00:00'))
            previous_time = datetime.fromisoformat(previous_post.get("collected_at", "").replace('Z', '+00:00'))
            
            delta_minutes = max(1, (current_time - previous_time).total_seconds() / 60)
            return delta_total / delta_minutes
            
        except:
            return 0

    def _calculate_time_delta(self, current_post: Dict, previous_post: Dict) -> Optional[float]:
        """Calculate time difference in minutes between measurements"""
        try:
            current_time = datetime.fromisoformat(current_post.get("collected_at", "").replace('Z', '+00:00'))
            previous_time = datetime.fromisoformat(previous_post.get("collected_at", "").replace('Z', '+00:00'))
            
            return (current_time - previous_time).total_seconds() / 60
            
        except:
            return None

    async def _save_growth_data(self, data: Dict, batch_id: str) -> str:
        """Save growth data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/growth/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.growth.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, growth_data: Dict, batch_id: str) -> Dict:
        """Generate summary with top velocity posts as specified in AI Agent Prompts"""
        posts = growth_data.get("posts", [])
        
        if not posts:
            return {
                "batch_id": batch_id,
                "avg_velocity_per_min": 0,
                "top_velocity_posts": []
            }
        
        # Calculate average velocity
        total_velocity = sum(post.get("velocity_per_min", 0) for post in posts)
        avg_velocity = total_velocity / len(posts)
        
        # Get top 5 velocity posts
        sorted_posts = sorted(posts, key=lambda p: p.get("velocity_per_min", 0), reverse=True)
        top_velocity_posts = []
        
        for post in sorted_posts[:5]:
            top_velocity_posts.append({
                "id": post.get("id"),
                "author": post.get("author"),
                "content_preview": post.get("content", "")[:100] + "..." if len(post.get("content", "")) > 100 else post.get("content", ""),
                "velocity_per_min": post.get("velocity_per_min", 0),
                "delta_total": post.get("delta_total", 0),
                "growth_rate": post.get("growth_rate", 0),
                "total_engagement": post.get("total_engagement", 0)
            })
        
        return {
            "batch_id": batch_id,
            "avg_velocity_per_min": round(avg_velocity, 2),
            "top_velocity_posts": top_velocity_posts,
            "total_delta_engagement": sum(p.get("delta_total", 0) for p in posts),
            "posts_with_growth": sum(1 for p in posts if p.get("delta_total", 0) > 0),
            "posts_with_decline": sum(1 for p in posts if p.get("delta_total", 0) < 0),
            "new_posts_count": sum(1 for p in posts if p.get("is_new_post", False))
        }