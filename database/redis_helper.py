"""
Redis Integration Helper for Trending Intelligence Pipeline
Provides caching and performance optimization for LLM analysis

Author: AI Assistant
Date: October 7, 2025
"""

import asyncio
import logging
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TrendingRedisHelper:
    """
    Helper class to integrate Redis caching with existing trending intelligence pipeline
    """

    def __init__(self, redis_manager=None):
        """Initialize with optional Redis manager"""
        self.redis_manager = redis_manager
        self.cache_enabled = redis_manager is not None

        if not self.cache_enabled:
            logger.warning(
                "⚠️ Redis caching disabled - operating without cache")

    async def get_or_analyze(self, analysis_type: str, content: str, analysis_func, *args, **kwargs) -> Dict:
        """
        Get cached analysis or run analysis function if not cached

        Args:
            analysis_type: Type of analysis (e.g., 'content_strategies', 'engagement_patterns')
            content: Content to analyze (used for cache key)
            analysis_func: Function to call if cache miss
            *args, **kwargs: Arguments to pass to analysis function

        Returns:
            Analysis result (from cache or fresh analysis)
        """
        if not self.cache_enabled:
            # No cache - run analysis directly
            return await analysis_func(*args, **kwargs)

        try:
            # Try to get from cache first
            cached_result = await self.redis_manager.get_cached_analysis(analysis_type, content)

            if cached_result:
                logger.debug(f"🎯 Cache HIT for {analysis_type}")
                return cached_result

            # Cache miss - run analysis
            logger.debug(
                f"💨 Cache MISS for {analysis_type} - running fresh analysis")
            result = await analysis_func(*args, **kwargs)

            # Cache the result
            if result and isinstance(result, dict):
                await self.redis_manager.cache_analysis_result(
                    analysis_type,
                    hashlib.sha256(content.encode()).hexdigest()[:16],
                    result
                )
                logger.debug(f"📝 Cached fresh analysis for {analysis_type}")

            return result

        except Exception as e:
            logger.error(f"Redis cache error for {analysis_type}: {str(e)}")
            # Fallback to direct analysis on Redis errors
            return await analysis_func(*args, **kwargs)

    async def cache_trending_batch(self, batch_id: str, data: Dict) -> bool:
        """Cache trending data batch"""
        if not self.cache_enabled:
            return False

        try:
            return await self.redis_manager.store_trending_batch(batch_id, data)
        except Exception as e:
            logger.error(f"Failed to cache trending batch: {str(e)}")
            return False

    async def get_cached_batch(self, batch_id: str) -> Optional[Dict]:
        """Get cached trending batch"""
        if not self.cache_enabled:
            return None

        try:
            return await self.redis_manager.get_trending_batch(batch_id)
        except Exception as e:
            logger.error(f"Failed to get cached batch: {str(e)}")
            return None

    async def notify_pipeline_stage(self, stage: str, status: str, data: Dict = None) -> bool:
        """Send pipeline stage notification"""
        if not self.cache_enabled:
            return False

        try:
            message = {
                "stage": stage,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data or {}
            }

            return await self.redis_manager.publish_notification("pipeline_stages", message)
        except Exception as e:
            logger.error(f"Failed to notify pipeline stage: {str(e)}")
            return False

    async def store_pipeline_metrics(self, metrics: Dict) -> bool:
        """Store pipeline performance metrics"""
        if not self.cache_enabled:
            return False

        try:
            return await self.redis_manager.cache_metrics({
                "pipeline_metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to store pipeline metrics: {str(e)}")
            return False

    async def get_recent_analysis_patterns(self) -> Dict:
        """Get patterns from recent cached analyses"""
        if not self.cache_enabled:
            return {}

        try:
            # This would require more complex Redis operations
            # For now, return basic stats
            stats = await self.redis_manager.get_cache_stats()

            return {
                "cache_enabled": True,
                "cache_stats": stats,
                "analysis_patterns": "Feature coming soon"
            }
        except Exception as e:
            logger.error(f"Failed to get analysis patterns: {str(e)}")
            return {}


# Decorator for easy caching integration
def with_redis_cache(analysis_type: str):
    """
    Decorator to add Redis caching to analysis functions

    Usage:
        @with_redis_cache("content_strategies")
        async def analyze_content_strategies(content, data):
            # Analysis code here
            return result
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Try to get Redis helper from context
            redis_helper = getattr(wrapper, '_redis_helper', None)

            if not redis_helper:
                # No Redis helper - run function directly
                return await func(*args, **kwargs)

            # Extract content for cache key (assume first string arg is content)
            content = ""
            for arg in args:
                if isinstance(arg, str) and len(arg) > 10:
                    content = arg
                    break

            if not content:
                # Can't determine content - run function directly
                return await func(*args, **kwargs)

            # Use Redis helper for caching
            return await redis_helper.get_or_analyze(
                analysis_type, content, func, *args, **kwargs
            )

        return wrapper
    return decorator


# Global Redis helper instance
_redis_helper_instance = None


async def init_redis_helper():
    """Initialize global Redis helper"""
    global _redis_helper_instance

    try:
        from database.redis_manager import get_redis_manager

        redis_manager = await get_redis_manager()
        _redis_helper_instance = TrendingRedisHelper(redis_manager)

        logger.info("✅ Redis helper initialized successfully")
        return True

    except Exception as e:
        logger.warning(f"⚠️ Redis helper initialization failed: {str(e)}")
        logger.warning("Continuing without Redis caching...")
        _redis_helper_instance = TrendingRedisHelper(None)  # No cache mode
        return False


async def get_redis_helper() -> TrendingRedisHelper:
    """Get global Redis helper instance"""
    global _redis_helper_instance

    if not _redis_helper_instance:
        await init_redis_helper()

    return _redis_helper_instance


# Convenience functions for pipeline integration
async def cache_analysis_result(analysis_type: str, content: str, result: Dict) -> bool:
    """Cache analysis result"""
    redis_helper = await get_redis_helper()

    if redis_helper.cache_enabled:
        return await redis_helper.redis_manager.cache_analysis_result(
            analysis_type,
            hashlib.sha256(content.encode()).hexdigest()[:16],
            result
        )
    return False


async def get_cached_analysis(analysis_type: str, content: str) -> Optional[Dict]:
    """Get cached analysis result"""
    redis_helper = await get_redis_helper()

    if redis_helper.cache_enabled:
        return await redis_helper.redis_manager.get_cached_analysis(analysis_type, content)
    return None


async def publish_trending_notification(notification_type: str, data: Dict) -> bool:
    """Publish trending pipeline notification"""
    redis_helper = await get_redis_helper()

    message = {
        "type": notification_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }

    if redis_helper.cache_enabled:
        return await redis_helper.redis_manager.publish_notification("trending_pipeline", message)
    return False
