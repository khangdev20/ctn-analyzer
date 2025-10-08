"""
Redis Database Integration for Trending Intelligence System
Provides caching, pub/sub, and data persistence capabilities

Author: AI Assistant
Date: October 7, 2025
"""

import asyncio
import json
import logging
import os
import redis.asyncio as redis
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import pickle

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis integration manager for caching and pub/sub
    """

    def __init__(self, config: Dict = None):
        """Initialize Redis manager"""
        self.config = config or self._get_default_config()
        self.redis_client = None
        self.pubsub = None

    def _get_default_config(self) -> Dict:
        """Get default Redis configuration with environment variable support"""
        return {
            "host": os.getenv("REDIS_HOST", "redis-11099.c296.ap-southeast-2-1.ec2.redns.redis-cloud.com"),
            "port": int(os.getenv("REDIS_PORT", "11099")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD", "btkL8Cbz19z3aTcOve2S1v6CW9bnlBTw"),
            "username": os.getenv("REDIS_USERNAME", "default"),
            "decode_responses": True,
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
            "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", "10")),
            "socket_connect_timeout": int(os.getenv("REDIS_CONNECT_TIMEOUT", "10")),

            # Cache settings
            "default_ttl": 3600,  # 1 hour
            "trending_data_ttl": 900,  # 15 minutes
            "analysis_cache_ttl": 1800,  # 30 minutes
            "metrics_ttl": 300,  # 5 minutes

            # Key prefixes
            "key_prefixes": {
                "trending": "trending:",
                "analysis": "analysis:",
                "metrics": "metrics:",
                "cache": "cache:",
                "session": "session:",
                "rate_limit": "rate_limit:"
            }
        }

    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            connection_params = {
                "host": self.config["host"],
                "port": self.config["port"],
                "db": self.config["db"],
                "password": self.config["password"],
                "decode_responses": self.config["decode_responses"],
                "max_connections": self.config["max_connections"],
                "socket_timeout": self.config["socket_timeout"],
                "socket_connect_timeout": self.config["socket_connect_timeout"]
            }

            # Add username if provided (for Redis Cloud ACL)
            if self.config.get("username"):
                connection_params["username"] = self.config["username"]

            self.redis_client = redis.Redis(**connection_params)

            # Test connection
            await self.redis_client.ping()
            logger.info(
                f"[OK] Connected to Redis at {self.config['host']}:{self.config['port']}")

            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Redis: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        try:
            if self.pubsub:
                await self.pubsub.aclose()

            if self.redis_client:
                await self.redis_client.aclose()

            logger.info("[OK] Disconnected from Redis")

        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {str(e)}")

    # ==================== CACHING METHODS ====================

    async def cache_trending_data(self, data: Dict, timestamp: str = None) -> bool:
        """Cache trending data with automatic expiration"""
        try:
            if not timestamp:
                timestamp = datetime.now(
                    timezone.utc).strftime("%Y%m%dT%H%M%SZ")

            key = f"{self.config['key_prefixes']['trending']}{timestamp}"

            # Store as JSON
            await self.redis_client.setex(
                key,
                self.config["trending_data_ttl"],
                json.dumps(data, default=str)
            )

            # Also store latest data pointer
            latest_key = f"{self.config['key_prefixes']['trending']}latest"
            await self.redis_client.setex(
                latest_key,
                self.config["trending_data_ttl"],
                key
            )

            logger.debug(f"[NOTE] Cached trending data: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache trending data: {str(e)}")
            return False

    async def get_trending_data(self, timestamp: str = None) -> Optional[Dict]:
        """Get trending data from cache"""
        try:
            if timestamp:
                key = f"{self.config['key_prefixes']['trending']}{timestamp}"
            else:
                # Get latest data
                latest_key = f"{self.config['key_prefixes']['trending']}latest"
                key = await self.redis_client.get(latest_key)
                if not key:
                    return None

            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get trending data: {str(e)}")
            return None

    async def cache_analysis_result(self, analysis_type: str, content_hash: str, result: Dict) -> bool:
        """Cache LLM analysis results"""
        try:
            key = f"{self.config['key_prefixes']['analysis']}{analysis_type}:{content_hash}"

            await self.redis_client.setex(
                key,
                self.config["analysis_cache_ttl"],
                json.dumps(result, default=str)
            )

            logger.debug(f"[NOTE] Cached analysis result: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache analysis result: {str(e)}")
            return False

    async def get_cached_analysis(self, analysis_type: str, content: str) -> Optional[Dict]:
        """Get cached analysis result"""
        try:
            # Create hash of content for key
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            key = f"{self.config['key_prefixes']['analysis']}{analysis_type}:{content_hash}"

            data = await self.redis_client.get(key)
            if data:
                logger.debug(f"[TARGET] Cache hit for analysis: {key}")
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get cached analysis: {str(e)}")
            return None

    async def cache_metrics(self, metrics: Dict) -> bool:
        """Cache system metrics"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            key = f"{self.config['key_prefixes']['metrics']}{timestamp}"

            await self.redis_client.setex(
                key,
                self.config["metrics_ttl"],
                json.dumps(metrics, default=str)
            )

            # Store latest metrics pointer
            latest_key = f"{self.config['key_prefixes']['metrics']}latest"
            await self.redis_client.setex(
                latest_key,
                self.config["metrics_ttl"],
                key
            )

            return True

        except Exception as e:
            logger.error(f"Failed to cache metrics: {str(e)}")
            return False

    async def get_latest_metrics(self) -> Optional[Dict]:
        """Get latest cached metrics"""
        try:
            latest_key = f"{self.config['key_prefixes']['metrics']}latest"
            key = await self.redis_client.get(latest_key)

            if key:
                data = await self.redis_client.get(key)
                if data:
                    return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get latest metrics: {str(e)}")
            return None

    # ==================== RATE LIMITING ====================

    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> Dict:
        """Check and update rate limiting"""
        try:
            key = f"{self.config['key_prefixes']['rate_limit']}{identifier}"

            # Use Redis pipeline for atomic operations
            async with self.redis_client.pipeline() as pipe:
                await pipe.incr(key)
                await pipe.expire(key, window_seconds)
                results = await pipe.execute()

            current_count = results[0]

            return {
                "allowed": current_count <= limit,
                "current_count": current_count,
                "limit": limit,
                "window_seconds": window_seconds,
                "reset_time": datetime.now(timezone.utc) + timedelta(seconds=window_seconds)
            }

        except Exception as e:
            logger.error(f"Failed to check rate limit: {str(e)}")
            return {"allowed": True, "error": str(e)}

    # ==================== PUB/SUB MESSAGING ====================

    async def publish_notification(self, channel: str, message: Dict) -> bool:
        """Publish notification to channel"""
        try:
            await self.redis_client.publish(
                channel,
                json.dumps(message, default=str)
            )

            logger.debug(
                f"[ANNOUNCE] Published to {channel}: {message.get('type', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish notification: {str(e)}")
            return False

    async def subscribe_to_notifications(self, channels: List[str], callback) -> bool:
        """Subscribe to notification channels"""
        try:
            self.pubsub = self.redis_client.pubsub()

            for channel in channels:
                await self.pubsub.subscribe(channel)

            logger.info(f"[BELL] Subscribed to channels: {channels}")

            # Listen for messages
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await callback(message['channel'], data)
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to notifications: {str(e)}")
            return False

    # ==================== TRENDING DATA METHODS ====================

    async def store_trending_batch(self, batch_id: str, data: Dict) -> bool:
        """Store a complete trending data batch"""
        try:
            key = f"{self.config['key_prefixes']['trending']}batch:{batch_id}"

            # Store with longer TTL for batch data
            await self.redis_client.setex(
                key,
                self.config["trending_data_ttl"] * 4,  # 1 hour
                json.dumps({
                    "batch_id": batch_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": data
                }, default=str)
            )

            # Add to batch index
            batch_index_key = f"{self.config['key_prefixes']['trending']}batches"
            await self.redis_client.lpush(batch_index_key, batch_id)
            # Keep last 100 batches
            await self.redis_client.ltrim(batch_index_key, 0, 99)

            logger.debug(f"[NOTE] Stored trending batch: {batch_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store trending batch: {str(e)}")
            return False

    async def get_trending_batch(self, batch_id: str) -> Optional[Dict]:
        """Get a specific trending data batch"""
        try:
            key = f"{self.config['key_prefixes']['trending']}batch:{batch_id}"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get trending batch: {str(e)}")
            return None

    async def get_recent_batches(self, limit: int = 10) -> List[str]:
        """Get list of recent batch IDs"""
        try:
            batch_index_key = f"{self.config['key_prefixes']['trending']}batches"
            batch_ids = await self.redis_client.lrange(batch_index_key, 0, limit - 1)

            return batch_ids or []

        except Exception as e:
            logger.error(f"Failed to get recent batches: {str(e)}")
            return []

    # ==================== SYSTEM STATUS METHODS ====================

    async def store_system_status(self, status: Dict) -> bool:
        """Store current system status"""
        try:
            key = f"{self.config['key_prefixes']['cache']}system_status"

            await self.redis_client.setex(
                key,
                300,  # 5 minutes
                json.dumps(status, default=str)
            )

            return True

        except Exception as e:
            logger.error(f"Failed to store system status: {str(e)}")
            return False

    async def get_system_status(self) -> Optional[Dict]:
        """Get current system status"""
        try:
            key = f"{self.config['key_prefixes']['cache']}system_status"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return None

    # ==================== UTILITY METHODS ====================

    async def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries matching pattern"""
        try:
            if pattern:
                keys = await self.redis_client.keys(pattern)
            else:
                keys = await self.redis_client.keys("*")

            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"[DELETE] Cleared {deleted} cache entries")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return 0

    async def get_cache_stats(self) -> Dict:
        """Get Redis cache statistics"""
        try:
            info = await self.redis_client.info()

            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {}

    async def health_check(self) -> Dict:
        """Perform Redis health check"""
        try:
            start_time = datetime.now(timezone.utc)

            # Test basic operations
            await self.redis_client.ping()

            # Test write/read
            test_key = "health_check_test"
            await self.redis_client.setex(test_key, 10, "test_value")
            test_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)

            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds() * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "read_write_test": test_value == "test_value",
                "timestamp": end_time.isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global Redis manager instance
redis_manager = None


async def get_redis_manager() -> RedisManager:
    """Get or create Redis manager instance"""
    global redis_manager

    if not redis_manager:
        redis_manager = RedisManager()
        await redis_manager.connect()

    return redis_manager


# Integration functions for the trending intelligence system
async def cache_trending_analysis(analysis_type: str, content: str, result: Dict) -> bool:
    """Cache LLM analysis result for trending intelligence"""
    try:
        redis_mgr = await get_redis_manager()
        return await redis_mgr.cache_analysis_result(analysis_type,
                                                     hashlib.sha256(
                                                         content.encode()).hexdigest()[:16],
                                                     result)
    except Exception as e:
        logger.error(f"Failed to cache trending analysis: {str(e)}")
        return False


async def get_cached_trending_analysis(analysis_type: str, content: str) -> Optional[Dict]:
    """Get cached trending analysis result"""
    try:
        redis_mgr = await get_redis_manager()
        return await redis_mgr.get_cached_analysis(analysis_type, content)
    except Exception as e:
        logger.error(f"Failed to get cached trending analysis: {str(e)}")
        return None


async def publish_trending_update(update_type: str, data: Dict) -> bool:
    """Publish trending data update notification"""
    try:
        redis_mgr = await get_redis_manager()

        message = {
            "type": update_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        return await redis_mgr.publish_notification("trending_updates", message)

    except Exception as e:
        logger.error(f"Failed to publish trending update: {str(e)}")
        return False


# Sync Redis connection for leaderboard tasks
def get_redis_connection():
    """Get synchronous Redis connection for leaderboard tasks"""
    try:
        import redis
        
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis-11099.c296.ap-southeast-2-1.ec2.redns.redis-cloud.com"),
            port=int(os.getenv("REDIS_PORT", "11099")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD", "btkL8Cbz19z3aTcOve2S1v6CW9bnlBTw"),
            username=os.getenv("REDIS_USERNAME", "default"),
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        # Test connection
        redis_client.ping()
        logger.info("[OK] Sync Redis connection established for leaderboard")
        return redis_client
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to get sync Redis connection: {e}")
        return None


if __name__ == "__main__":
    # Test Redis integration
    async def test_redis():
        redis_mgr = RedisManager()

        # Test connection
        connected = await redis_mgr.connect()
        if not connected:
            print("[ERROR] Failed to connect to Redis")
            return

        # Test caching
        test_data = {"test": "data", "timestamp": datetime.now(
            timezone.utc).isoformat()}
        await redis_mgr.cache_trending_data(test_data)

        # Test retrieval
        cached_data = await redis_mgr.get_trending_data()
        print(f"Cached data: {cached_data}")

        # Test health check
        health = await redis_mgr.health_check()
        print(f"Health: {health}")

        # Test cache stats
        stats = await redis_mgr.get_cache_stats()
        print(f"Cache stats: {stats}")

        await redis_mgr.disconnect()

    asyncio.run(test_redis())
