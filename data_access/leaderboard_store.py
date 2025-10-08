"""
Leaderboard Data Store - Snapshot persistence and idempotency management
Handles reading/writing daily snapshots and lock management

Author: AI Assistant
Date: October 8, 2025
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import redis

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


def read_snapshot(date_str: str) -> Optional[List[Dict]]:
    """
    Read snapshot for given date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        List of leaderboard entries or None if not found
    """
    snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
    snapshot_path = snapshot_dir / f"{date_str}.json"
    
    try:
        if not snapshot_path.exists():
            logger.info(f"[OPEN_FOLDER] Snapshot not found: {snapshot_path}")
            return None
            
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Validate structure
        if not isinstance(data, dict) or 'entries' not in data:
            logger.error(f"[ERROR] Invalid snapshot format in {snapshot_path}")
            return None
            
        entries = data['entries']
        if not isinstance(entries, list):
            logger.error(f"[ERROR] Invalid entries format in {snapshot_path}")
            return None
            
        logger.info(f"[OK] Loaded snapshot {date_str}: {len(entries)} entries")
        return entries
        
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] JSON decode error reading {snapshot_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Error reading snapshot {snapshot_path}: {e}")
        return None


def write_snapshot(date_str: str, entries: List[Dict]) -> bool:
    """
    Write snapshot for given date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        entries: List of leaderboard entries
        
    Returns:
        True if successful, False otherwise
    """
    snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_path = snapshot_dir / f"{date_str}.json"
    
    try:
        # Prepare data structure
        snapshot_data = {
            'date': date_str,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_entries': len(entries),
            'entries': entries,
            'metadata': {
                'generated_by': 'leaderboard_worker',
                'version': '1.0'
            }
        }
        
        # Write atomically (write to temp file, then rename)
        temp_path = snapshot_path.with_suffix('.tmp')
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_path.rename(snapshot_path)
        
        # Also write a compact CSV for historical analysis (optional)
        _write_csv_append(date_str, entries)
        
        logger.info(f"[SAVE] Saved snapshot {date_str}: {len(entries)} entries to {snapshot_path}")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error writing snapshot {snapshot_path}: {e}")
        return False


def _write_csv_append(date_str: str, entries: List[Dict]) -> None:
    """Write compact CSV for historical analysis"""
    try:
        snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
        csv_path = snapshot_dir / "historical.csv"
        
        # Check if CSV exists and needs header
        write_header = not csv_path.exists()
        
        with open(csv_path, 'a', encoding='utf-8') as f:
            if write_header:
                f.write("date,id,name,score,rank,affiliation\n")
            
            # Write top 50 entries to keep file manageable
            for entry in entries[:50]:
                name = entry['name'].replace(',', ' ').replace('\n', ' ')
                affiliation = entry.get('affiliation', '').replace(',', ' ').replace('\n', ' ')
                f.write(f"{date_str},{entry['id']},{name},{entry['score']},{entry['rank']},{affiliation}\n")
        
        logger.debug(f"[ANALYTICS] Updated historical CSV: {csv_path}")
        
    except Exception as e:
        logger.warning(f"[WARNING] Failed to write CSV: {e}")


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
        return _set_file_lock(date_str)


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
        logger.warning(f"[WARNING] Redis lock failed, falling back to file lock: {e}")
        return _set_file_lock(date_str)


def _set_file_lock(date_str: str) -> bool:
    """Set file-based lock as fallback"""
    try:
        snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        lock_path = snapshot_dir / f"{date_str}.lock"
        
        if lock_path.exists():
            logger.info(f"[LOCKED] File lock already exists for {date_str}")
            return False
        
        # Create lock file
        with open(lock_path, 'w', encoding='utf-8') as f:
            f.write(f"Locked at {datetime.utcnow().isoformat()}Z\n")
        
        logger.info(f"[LOCKED] File lock set for {date_str}")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to set file lock for {date_str}: {e}")
        return False  # Assume already locked to be safe


def cleanup_old_snapshots(keep_days: int = 90) -> int:
    """
    Remove snapshots older than keep_days
    
    Args:
        keep_days: Number of days to keep
        
    Returns:
        Number of files removed
    """
    try:
        from datetime import timedelta
        
        snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
        if not snapshot_dir.exists():
            return 0
            
        cutoff_date = datetime.now().date() - timedelta(days=keep_days)
        removed_count = 0
        
        # Clean up JSON snapshots
        for file_path in snapshot_dir.glob("*.json"):
            try:
                # Parse date from filename
                date_str = file_path.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if file_date < cutoff_date:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"[DELETE] Removed old snapshot: {date_str}")
                    
            except ValueError:
                # Skip files that don't match date format
                continue
        
        # Clean up lock files
        for lock_path in snapshot_dir.glob("*.lock"):
            try:
                date_str = lock_path.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if file_date < cutoff_date:
                    lock_path.unlink()
                    logger.debug(f"[DELETE] Removed old lock: {date_str}")
                    
            except ValueError:
                continue
        
        if removed_count > 0:
            logger.info(f"[CLEANUP] Cleaned up {removed_count} old snapshots")
        
        return removed_count
        
    except Exception as e:
        logger.error(f"[ERROR] Error during cleanup: {e}")
        return 0


def get_available_snapshots() -> List[str]:
    """
    Get list of available snapshot dates
    
    Returns:
        List of date strings (YYYY-MM-DD) sorted chronologically
    """
    try:
        snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
        if not snapshot_dir.exists():
            return []
        
        snapshots = []
        for file_path in snapshot_dir.glob("*.json"):
            if file_path.stem.count('-') == 2:  # YYYY-MM-DD format
                snapshots.append(file_path.stem)
        
        return sorted(snapshots)
        
    except Exception as e:
        logger.error(f"[ERROR] Error listing snapshots: {e}")
        return []


# Health check function
def health_check() -> Dict:
    """
    Check health of storage system
    
    Returns:
        Health status dictionary
    """
    try:
        snapshot_dir = Path(os.getenv('SNAPSHOT_DIR', 'data/leaderboard'))
        
        # Check directory access
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Check Redis availability
        redis_available = _get_redis_client() is not None
        
        # Count available snapshots
        available_snapshots = get_available_snapshots()
        
        return {
            'status': 'healthy',
            'snapshot_dir': str(snapshot_dir),
            'snapshot_dir_exists': snapshot_dir.exists(),
            'snapshot_dir_writable': os.access(snapshot_dir, os.W_OK),
            'redis_available': redis_available,
            'total_snapshots': len(available_snapshots),
            'latest_snapshot': available_snapshots[-1] if available_snapshots else None
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }