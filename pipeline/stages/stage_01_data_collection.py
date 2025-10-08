# 🟩 Stage 1: Data Collection — Collect Trending and Latest Posts

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import requests

from worker.features.data_collector import collect_trending_data

logger = logging.getLogger(__name__)


class DataCollectionStage:
    """
    Task: Collect latest and trending posts from the feed
    - Input: API endpoint or feed URL
    - Output: raw JSON file (data/raw/YYYY/MM/DD/batch_<timestamp>.json)
    - Steps:
      1. Fetch posts using requests
      2. Extract key fields: id, author, content, created_at, like_count, reply_count, repost_count, tags
      3. Mark duplicate post_ids with "seen" flag
      4. Log summary stats (count, top 5 tags)
    - Return: summary dict {batch_id, collected_count, trending_tags}
    """

    def __init__(self, config):
        self.config = config
        self.seen_post_ids = set()

    async def execute(self, batch_id: str, **kwargs) -> Optional[Dict]:
        """Execute data collection stage"""
        logger.info("[ANALYTICS] Stage 1: Collecting trending data...")
        
        try:
            # Use existing data collector with async wrapper
            def collect_data():
                return collect_trending_data(
                    num_pages=self.config.batch_size, 
                    key='trending'
                )

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            filename = await loop.run_in_executor(None, collect_data)

            if not filename:
                logger.error("[ERROR] No data collected from API")
                return None

            # Read the collected data
            with open(filename, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # Process and enrich data
            processed_data = await self._process_raw_data(raw_data, batch_id)
            
            # Save to structured directory
            output_path = await self._save_structured_data(processed_data, batch_id)

            # Extract summary statistics
            summary = self._generate_summary(processed_data, batch_id)
            
            logger.info(f"[OK] Stage 1 completed: {summary['collected_count']} posts collected")
            logger.info(f"[FOLDER] Data saved to: {output_path}")
            
            return {
                **summary,
                "raw_data": processed_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"[ERROR] Stage 1 error: {e}")
            return None

    async def _process_raw_data(self, raw_data: Dict, batch_id: str) -> Dict:
        """Process raw API data and extract key fields"""
        posts = raw_data.get('data', [])
        processed_posts = []
        
        for post in posts:
            try:
                # Extract key fields as specified in AI Agent Prompts
                processed_post = {
                    "id": post.get("id"),
                    "author": post.get("author", {}).get("username", "unknown"),
                    "content": post.get("text", ""),
                    "created_at": post.get("created_at"),
                    "like_count": post.get("public_metrics", {}).get("like_count", 0),
                    "reply_count": post.get("public_metrics", {}).get("reply_count", 0),
                    "repost_count": post.get("public_metrics", {}).get("retweet_count", 0),
                    "tags": self._extract_hashtags(post.get("text", "")),
                    "seen": post.get("id") in self.seen_post_ids,
                    "batch_id": batch_id,
                    "collected_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Mark as seen for duplicate detection
                if post.get("id"):
                    self.seen_post_ids.add(post.get("id"))
                
                processed_posts.append(processed_post)
                
            except Exception as e:
                logger.warning(f"Failed to process post {post.get('id', 'unknown')}: {e}")
                continue

        return {
            "batch_id": batch_id,
            "source": "trending_feed",
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "posts": processed_posts,
            "metadata": {
                "total_posts": len(processed_posts),
                "duplicate_posts": sum(1 for p in processed_posts if p["seen"]),
                "original_count": len(posts)
            }
        }

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from post text"""
        import re
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, text.lower())
        return [tag[1:] for tag in hashtags]  # Remove # prefix

    async def _save_structured_data(self, data: Dict, batch_id: str) -> str:
        """Save processed data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/raw/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, data: Dict, batch_id: str) -> Dict:
        """Generate summary statistics as specified in AI Agent Prompts"""
        posts = data.get("posts", [])
        
        # Count tags and get top 5
        tag_counts = {}
        for post in posts:
            for tag in post.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        trending_tags = [tag for tag, count in top_tags]
        
        return {
            "batch_id": batch_id,
            "collected_count": len(posts),
            "trending_tags": trending_tags,
            "duplicate_count": data.get("metadata", {}).get("duplicate_posts", 0),
            "top_tags_with_counts": top_tags
        }