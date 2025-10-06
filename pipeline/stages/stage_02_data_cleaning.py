# 🟦 Stage 2: Data Cleaning — Normalize and Prepare Data

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class DataCleaningStage:
    """
    Task: Clean and normalize collected post data
    - Input: raw JSON batch file
    - Output: cleaned JSON file (data/clean/YYYY/MM/DD/batch_<timestamp>.clean.json)
    - Steps:
      1. Remove deleted or duplicate posts
      2. Standardize field names and data types
      3. Compute derived metrics: total_engagement, engagement_per_min
      4. Log summary metrics (cleaned_count, avg_engagement)
    - Return: summary dict {batch_id, cleaned_count, duplicates_removed, avg_engagement}
    """

    def __init__(self, config):
        self.config = config

    async def execute(self, batch_id: str, raw_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute data cleaning stage"""
        logger.info("🧹 Stage 2: Cleaning and preprocessing data...")
        
        try:
            # Step 1: Remove deleted or duplicate posts
            valid_posts = await self._remove_invalid_posts(raw_data.get("posts", []))
            
            # Step 2: Standardize field names and data types
            standardized_posts = await self._standardize_posts(valid_posts)
            
            # Step 3: Compute derived metrics
            enriched_posts = await self._compute_derived_metrics(standardized_posts)
            
            # Create cleaned data structure
            cleaned_data = {
                "batch_id": batch_id,
                "cleaned_at": datetime.now(timezone.utc).isoformat(),
                "posts": enriched_posts,
                "metadata": {
                    "original_count": len(raw_data.get("posts", [])),
                    "cleaned_count": len(enriched_posts),
                    "duplicates_removed": len(raw_data.get("posts", [])) - len(valid_posts),
                    "invalid_removed": len(valid_posts) - len(enriched_posts)
                }
            }
            
            # Save cleaned data
            output_path = await self._save_cleaned_data(cleaned_data, batch_id)
            
            # Generate summary
            summary = self._generate_summary(cleaned_data, batch_id)
            
            logger.info(f"✅ Stage 2 completed: {summary['cleaned_count']} posts cleaned")
            logger.info(f"📁 Cleaned data saved to: {output_path}")
            
            return {
                **summary,
                "cleaned_data": cleaned_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"❌ Stage 2 error: {e}")
            return None

    async def _remove_invalid_posts(self, posts: List[Dict]) -> List[Dict]:
        """Remove deleted, duplicate, or invalid posts"""
        valid_posts = []
        seen_ids = set()
        
        for post in posts:
            post_id = post.get("id")
            
            # Skip if no ID
            if not post_id:
                continue
                
            # Skip if duplicate
            if post_id in seen_ids:
                continue
                
            # Skip if deleted (no content)
            if not post.get("content", "").strip():
                continue
                
            # Skip if marked as seen (duplicate from previous batches)
            if post.get("seen", False):
                continue
            
            seen_ids.add(post_id)
            valid_posts.append(post)
        
        return valid_posts

    async def _standardize_posts(self, posts: List[Dict]) -> List[Dict]:
        """Standardize field names and data types"""
        standardized = []
        
        for post in posts:
            try:
                # Standardize and validate numeric fields
                like_count = max(0, int(post.get("like_count", 0)))
                reply_count = max(0, int(post.get("reply_count", 0)))
                repost_count = max(0, int(post.get("repost_count", 0)))
                
                # Clean and standardize text content
                content = self._clean_text_content(post.get("content", ""))
                
                # Standardize datetime
                created_at = self._standardize_datetime(post.get("created_at"))
                
                # Standardize tags
                tags = self._standardize_tags(post.get("tags", []))
                
                standardized_post = {
                    "id": str(post.get("id")),
                    "author": str(post.get("author", "unknown")).lower().strip(),
                    "content": content,
                    "content_length": len(content),
                    "created_at": created_at,
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "repost_count": repost_count,
                    "tags": tags,
                    "tag_count": len(tags),
                    "batch_id": post.get("batch_id"),
                    "collected_at": post.get("collected_at")
                }
                
                standardized.append(standardized_post)
                
            except Exception as e:
                logger.warning(f"Failed to standardize post {post.get('id', 'unknown')}: {e}")
                continue
        
        return standardized

    async def _compute_derived_metrics(self, posts: List[Dict]) -> List[Dict]:
        """Compute derived metrics: total_engagement, engagement_per_min"""
        enriched = []
        
        for post in posts:
            try:
                # Calculate total engagement
                total_engagement = (
                    post.get("like_count", 0) + 
                    post.get("reply_count", 0) + 
                    post.get("repost_count", 0)
                )
                
                # Calculate engagement per minute (if created_at is available)
                engagement_per_min = 0
                if post.get("created_at"):
                    try:
                        created_time = datetime.fromisoformat(post["created_at"].replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        minutes_elapsed = max(1, (now - created_time).total_seconds() / 60)
                        engagement_per_min = total_engagement / minutes_elapsed
                    except:
                        engagement_per_min = 0
                
                # Calculate engagement rate (per character)
                content_length = post.get("content_length", 1)
                engagement_rate = total_engagement / max(1, content_length)
                
                # Add derived metrics
                enriched_post = {
                    **post,
                    "total_engagement": total_engagement,
                    "engagement_per_min": round(engagement_per_min, 2),
                    "engagement_rate": round(engagement_rate, 4),
                    "has_tags": post.get("tag_count", 0) > 0,
                    "is_short_form": content_length <= 100,
                    "is_long_form": content_length > 500
                }
                
                enriched.append(enriched_post)
                
            except Exception as e:
                logger.warning(f"Failed to compute metrics for post {post.get('id', 'unknown')}: {e}")
                continue
        
        return enriched

    def _clean_text_content(self, content: str) -> str:
        """Clean and normalize text content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Remove or normalize special characters
        content = re.sub(r'[^\w\s#@.,!?-]', '', content)
        
        return content

    def _standardize_datetime(self, dt_str: str) -> Optional[str]:
        """Standardize datetime format to ISO"""
        if not dt_str:
            return None
        
        try:
            # Try to parse and convert to UTC ISO format
            if 'T' in dt_str:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                dt = dt.replace(tzinfo=timezone.utc)
            
            return dt.isoformat()
        except:
            return None

    def _standardize_tags(self, tags: List[str]) -> List[str]:
        """Standardize and clean hashtags"""
        if not tags:
            return []
        
        cleaned_tags = []
        for tag in tags:
            if isinstance(tag, str):
                # Clean and normalize tag
                clean_tag = re.sub(r'[^\w]', '', tag.lower().strip())
                if len(clean_tag) > 1:  # Skip single character tags
                    cleaned_tags.append(clean_tag)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(cleaned_tags))

    async def _save_cleaned_data(self, data: Dict, batch_id: str) -> str:
        """Save cleaned data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/clean/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/batch_{batch_id}.clean.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, cleaned_data: Dict, batch_id: str) -> Dict:
        """Generate summary metrics as specified in AI Agent Prompts"""
        posts = cleaned_data.get("posts", [])
        metadata = cleaned_data.get("metadata", {})
        
        # Calculate average engagement
        if posts:
            total_engagement = sum(post.get("total_engagement", 0) for post in posts)
            avg_engagement = total_engagement / len(posts)
        else:
            avg_engagement = 0
        
        return {
            "batch_id": batch_id,
            "cleaned_count": len(posts),
            "duplicates_removed": metadata.get("duplicates_removed", 0),
            "avg_engagement": round(avg_engagement, 2),
            "avg_engagement_per_min": round(sum(p.get("engagement_per_min", 0) for p in posts) / max(1, len(posts)), 2),
            "posts_with_tags": sum(1 for p in posts if p.get("has_tags", False)),
            "short_form_posts": sum(1 for p in posts if p.get("is_short_form", False)),
            "long_form_posts": sum(1 for p in posts if p.get("is_long_form", False))
        }