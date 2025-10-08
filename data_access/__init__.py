"""
Data Access Layer for Trending Intelligence System

Provides data persistence and management utilities for:
- Leaderboard snapshots and locks
- Historical data tracking
- Cache management

Author: AI Assistant
Date: October 8, 2025
"""

from .leaderboard_store import (
    read_snapshot,
    write_snapshot,
    set_posted_lock,
    cleanup_old_snapshots,
    get_available_snapshots,
    health_check
)

__all__ = [
    'read_snapshot',
    'write_snapshot',
    'set_posted_lock',
    'cleanup_old_snapshots',
    'get_available_snapshots',
    'health_check'
]