"""
Leaderboard Data Store - S3-based snapshot persistence and idempotency management
Handles reading/writing daily snapshots with S3 storage and Redis locks

Author: AI Assistant
Date: October 8, 2025
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis

from .s3_store import get_s3_store, s3_read_json, s3_write_json, s3_exists, build_key

logger = logging.getLogger(__name__)

# Redis client for locks (optional)
_redis_client = None

def _get_redis_client():
    """Get Redis client if available"""
    global _redis_client
    if _redis_client is None:
        try:
            # Try to connect to Redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("[OK] Redis connected for leaderboard locks")
        except Exception as e:
            logger.warning(f"[WARNING] Redis not available for locks: {e}")
            _redis_client = False  # Mark as unavailable
    
    return _redis_client if _redis_client is not False else None


def snapshot_key(date_str: str) -> str:
    """
    Build S3 key for leaderboard snapshot
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        S3 key for the snapshot
    """
    # Extract year and month from date string
    year = date_str[:4]
    month = date_str[5:7]
    
    return build_key("leaderboard", year, month, f"{date_str}.json")


def read_snapshot(date_str: str) -> Optional[List[Dict]]:
    """
    Read snapshot for given date from S3
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        List of leaderboard entries or None if not found
    """
    key = snapshot_key(date_str)
    
    try:
        # Read from S3
        data = s3_read_json(key)
        
        if data is None:
            logger.info(f"[S3_NOT_FOUND] Snapshot not found: s3://{get_s3_store().bucket}/{key}")
            return None
            
        # Handle both old format (with 'entries' wrapper) and new format (direct list)
        if isinstance(data, dict) and 'entries' in data:
            entries = data['entries']
        elif isinstance(data, list):
            entries = data
        else:
            logger.error(f"[ERROR] Invalid snapshot format in S3 key: {key}")
            return None
            
        if not isinstance(entries, list):
            logger.error(f"[ERROR] Invalid entries format in S3 key: {key}")
            return None
            
        logger.info(f"[OK] Loaded S3 snapshot {date_str}: {len(entries)} entries")
        return entries
        
    except Exception as e:
        logger.error(f"[ERROR] Error reading S3 snapshot {key}: {e}")
        return None


def write_snapshot(date_str: str, entries: List[Dict]) -> bool:
    """
    Write snapshot for given date to S3
    
    Args:
        date_str: Date in YYYY-MM-DD format
        entries: List of leaderboard entries
        
    Returns:
        True if successful, False otherwise
    """
    key = snapshot_key(date_str)
    
    try:
        # Prepare data structure with metadata
        snapshot_data = {
            'date': date_str,
            'entries': entries,
            'count': len(entries),
            'metadata': {
                'timestamp_utc': datetime.utcnow().isoformat(),
                'generated_by': 'leaderboard_worker',
                'version': '2.0',
                'storage': 's3'
            }
        }
        
        # Write to S3 atomically
        result = s3_write_json(key, snapshot_data, compress=True)
        
        if result['success']:
            # Also write pointer to latest snapshot
            _write_latest_pointer(date_str, key)
            
            # Write historical CSV if enabled
            _write_csv_to_s3(date_str, entries)
            
            logger.info(f"[SAVE] Saved S3 snapshot {date_str}: {len(entries)} entries to {result['s3_url']}")
            return True
        else:
            logger.error(f"[ERROR] Failed to write S3 snapshot: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error writing S3 snapshot {key}: {e}")
        return False


def _write_latest_pointer(date_str: str, snapshot_key: str) -> None:
    """Write pointer to latest snapshot"""
    try:
        pointer_key = build_key("_pointers", "leaderboard", "latest.json")
        pointer_data = {
            "date": date_str,
            "key": snapshot_key,
            "timestamp": datetime.utcnow().isoformat(),
            "bucket": get_s3_store().bucket
        }
        
        s3_write_json(pointer_key, pointer_data)
        logger.debug(f"[POINTER] Updated latest pointer: {pointer_key}")
        
    except Exception as e:
        logger.warning(f"[WARNING] Failed to write latest pointer: {e}")


def _write_csv_to_s3(date_str: str, entries: List[Dict]) -> None:
    """Write compact CSV to S3 for historical analysis"""
    try:
        # Create CSV content
        csv_lines = ["date,id,name,score,rank,affiliation"]
        
        # Write top 50 entries to keep file manageable
        for entry in entries[:50]:
            name = str(entry.get('name', '')).replace(',', ' ').replace('\n', ' ')
            affiliation = str(entry.get('affiliation', '')).replace(',', ' ').replace('\n', ' ')
            csv_lines.append(f"{date_str},{entry.get('id', '')},{name},{entry.get('score', 0)},{entry.get('rank', 0)},{affiliation}")
        
        csv_content = "\n".join(csv_lines)
        
        # Write to S3 as partitioned data
        year = date_str[:4]
        month = date_str[5:7]
        csv_key = build_key("history", "leaderboard", f"date={date_str}", "data.csv")
        
        # Use raw text write for CSV
        result = get_s3_store().s3_write_json(csv_key, csv_content, content_type="text/csv")
        if result['success']:
            logger.debug(f"[ANALYTICS] Updated S3 historical CSV: {result['s3_url']}")
        
    except Exception as e:
        logger.warning(f"[WARNING] Failed to write S3 CSV: {e}")


def set_posted_lock(date_str: str) -> bool:
    """
    Set lock to prevent duplicate posting for the same date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        True if lock was set (first time), False if already existed
    """
    # Try Redis first
    redis_client = _get_redis_client()
    if redis_client:
        return _set_redis_lock(redis_client, date_str)
    else:
        return _set_s3_lock(date_str)


def _set_redis_lock(redis_client, date_str: str) -> bool:
    """Set Redis lock"""
    try:
        lock_key = f"lb:posted:{date_str}"
        ttl_seconds = int(os.getenv('LOCK_TTL_SECONDS', '172800'))  # 2 days default
        
        # Use SETNX (set if not exists) with expiry
        result = redis_client.set(lock_key, datetime.utcnow().isoformat(), 
                                nx=True, ex=ttl_seconds)
        
        if result:
            logger.info(f"[LOCKED] Redis lock set for {date_str}")
            return True
        else:
            logger.info(f"[LOCKED] Redis lock already exists for {date_str}")
            return False
            
    except Exception as e:
        logger.warning(f"[WARNING] Redis lock failed, falling back to S3 lock: {e}")
        return _set_s3_lock(date_str)


def _set_s3_lock(date_str: str) -> bool:
    """Set S3-based lock as fallback"""
    try:
        lock_key = build_key("locks", "leaderboard", f"{date_str}.lock")
        
        # Check if lock already exists
        if s3_exists(lock_key):
            logger.info(f"[LOCKED] S3 lock already exists for {date_str}")
            return False
        
        # Create lock object
        lock_data = {
            "date": date_str,
            "locked_at": datetime.utcnow().isoformat(),
            "locked_by": "leaderboard_worker",
            "ttl_hours": 48
        }
        
        result = s3_write_json(lock_key, lock_data)
        if result['success']:
            logger.info(f"[LOCKED] S3 lock set for {date_str}")
            return True
        else:
            logger.error(f"[ERROR] Failed to set S3 lock: {result.get('error')}")
            return False
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to set S3 lock for {date_str}: {e}")
        return False  # Assume already locked to be safe


def cleanup_old_snapshots(keep_days: int = 90) -> int:
    """
    Remove snapshots older than keep_days from S3
    
    Args:
        keep_days: Number of days to keep
        
    Returns:
        Number of objects removed
    """
    try:
        s3_store = get_s3_store()
        cutoff_date = datetime.now().date() - timedelta(days=keep_days)
        removed_count = 0
        
        # List all leaderboard snapshots
        snapshot_prefix = build_key("leaderboard")
        keys = s3_store.s3_list_prefix(snapshot_prefix, max_keys=10000)
        
        for key in keys:
            try:
                # Extract date from key - look for YYYY-MM-DD.json pattern
                if key.endswith('.json'):
                    filename = key.split('/')[-1]  # Get filename part
                    date_str = filename.replace('.json', '')
                    
                    if len(date_str) == 10 and date_str.count('-') == 2:  # YYYY-MM-DD format
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        
                        if file_date < cutoff_date:
                            # Delete the object
                            client = s3_store.get_s3_client()
                            client.delete_object(Bucket=s3_store.bucket, Key=key)
                            removed_count += 1
                            logger.info(f"[DELETE] Removed old S3 snapshot: {date_str}")
                            
            except (ValueError, Exception) as e:
                logger.debug(f"[SKIP] Could not process key {key}: {e}")
                continue
        
        # Clean up old lock files
        lock_prefix = build_key("locks", "leaderboard")
        lock_keys = s3_store.s3_list_prefix(lock_prefix, max_keys=1000)
        
        for key in lock_keys:
            try:
                if key.endswith('.lock'):
                    filename = key.split('/')[-1]
                    date_str = filename.replace('.lock', '')
                    
                    if len(date_str) == 10 and date_str.count('-') == 2:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        
                        if file_date < cutoff_date:
                            client = s3_store.get_s3_client()
                            client.delete_object(Bucket=s3_store.bucket, Key=key)
                            logger.debug(f"[DELETE] Removed old S3 lock: {date_str}")
                            
            except (ValueError, Exception) as e:
                logger.debug(f"[SKIP] Could not process lock key {key}: {e}")
                continue
        
        if removed_count > 0:
            logger.info(f"[CLEANUP] Cleaned up {removed_count} old S3 snapshots")
        
        return removed_count
        
    except Exception as e:
        logger.error(f"[ERROR] Error during S3 cleanup: {e}")
        return 0


def get_available_snapshots() -> List[str]:
    """
    Get list of available snapshot dates from S3
    
    Returns:
        List of date strings (YYYY-MM-DD) sorted chronologically
    """
    try:
        s3_store = get_s3_store()
        snapshot_prefix = build_key("leaderboard")
        keys = s3_store.s3_list_prefix(snapshot_prefix, max_keys=5000)
        
        snapshots = []
        for key in keys:
            try:
                if key.endswith('.json'):
                    filename = key.split('/')[-1]  # Get filename part
                    date_str = filename.replace('.json', '')
                    
                    if len(date_str) == 10 and date_str.count('-') == 2:  # YYYY-MM-DD format
                        snapshots.append(date_str)
                        
            except Exception:
                continue
        
        return sorted(snapshots)
        
    except Exception as e:
        logger.error(f"[ERROR] Error listing S3 snapshots: {e}")
        return []


def get_latest_snapshot_info() -> Optional[Dict]:
    """
    Get information about the latest snapshot from S3 pointer
    
    Returns:
        Dictionary with latest snapshot info or None
    """
    try:
        pointer_key = build_key("_pointers", "leaderboard", "latest.json")
        pointer_data = s3_read_json(pointer_key)
        
        if pointer_data:
            return pointer_data
        else:
            # Fallback: find most recent snapshot manually
            snapshots = get_available_snapshots()
            if snapshots:
                latest_date = snapshots[-1]  # Last in sorted list
                return {
                    "date": latest_date,
                    "key": snapshot_key(latest_date),
                    "source": "manual_lookup"
                }
        
        return None
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting latest snapshot info: {e}")
        return None


# Health check function
def health_check() -> Dict:
    """
    Check health of S3 storage system
    
    Returns:
        Health status dictionary
    """
    try:
        s3_store = get_s3_store()
        
        # Check S3 access
        try:
            client = s3_store.get_s3_client()
            client.head_bucket(Bucket=s3_store.bucket)
            s3_available = True
            s3_error = None
        except Exception as e:
            s3_available = False
            s3_error = str(e)
        
        # Check Redis availability
        redis_available = _get_redis_client() is not None
        
        # Count available snapshots
        available_snapshots = get_available_snapshots()
        latest_snapshot = get_latest_snapshot_info()
        
        return {
            'status': 'healthy' if s3_available else 'degraded',
            'storage': {
                's3_available': s3_available,
                's3_bucket': s3_store.bucket,
                's3_prefix': s3_store.prefix,
                's3_error': s3_error
            },
            'locking': {
                'redis_available': redis_available,
                'fallback': 's3_locks'
            },
            'data': {
                'snapshot_count': len(available_snapshots),
                'latest_snapshot': latest_snapshot,
                'oldest_snapshot': available_snapshots[0] if available_snapshots else None,
                'newest_snapshot': available_snapshots[-1] if available_snapshots else None
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


class LeaderboardStore:
    """
    Wrapper class for leaderboard store functions to maintain compatibility
    """
    
    def __init__(self):
        """Initialize the store"""
        pass
    
    def read_snapshot(self, date_str: str) -> Optional[List[Dict]]:
        """Read snapshot for the given date"""
        return read_snapshot(date_str)
    
    def write_snapshot(self, date_str: str, entries: List[Dict]) -> bool:
        """Write snapshot for the given date"""
        return write_snapshot(date_str, entries)
    
    def health_check(self) -> Dict:
        """Get health status"""
        return health_check()
    
    def cleanup_old_snapshots(self, keep_days: int = 90) -> int:
        """Clean up old snapshots"""
        return cleanup_old_snapshots(keep_days)
    
    def get_available_snapshots(self) -> List[str]:
        """Get list of available snapshots"""
        return get_available_snapshots()
    
    def set_posted_lock(self, date_str: str) -> bool:
        """Set posted lock for date"""
        return set_posted_lock(date_str)


if __name__ == "__main__":
    # Test S3 leaderboard store
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing S3 Leaderboard Store...")
    
    # Test data
    test_date = "2025-10-08"
    test_entries = [
        {"id": 1, "name": "Test User 1", "score": 1000.0, "rank": 1, "affiliation": "Test Team"},
        {"id": 2, "name": "Test User 2", "score": 950.0, "rank": 2, "affiliation": "Another Team"},
        {"id": 3, "name": "Test User 3", "score": 900.0, "rank": 3, "affiliation": "Third Team"}
    ]
    
    # Test write
    print(f"Writing test snapshot for {test_date}...")
    success = write_snapshot(test_date, test_entries)
    
    if success:
        print("✅ Write successful!")
        
        # Test read
        print(f"Reading test snapshot for {test_date}...")
        read_entries = read_snapshot(test_date)
        
        if read_entries and len(read_entries) == len(test_entries):
            print("✅ Read successful!")
            
            # Test health check
            print("Running health check...")
            health = health_check()
            print(f"Health status: {health['status']}")
            
            print("S3 Leaderboard Store test completed successfully!")
        else:
            print("❌ Read failed or data mismatch")
            sys.exit(1)
    else:
        print("❌ Write failed")
        sys.exit(1)