"""
Dynamic Scheduler Configuration Manager
Allows runtime configuration of job intervals via API

Author: AI Assistant
Date: October 9, 2025
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SchedulerConfig:
    """Dynamic scheduler configuration manager"""

    def __init__(self, config_file: str = "config/scheduler_intervals.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        self._intervals = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or return defaults"""
        defaults = {
            "content_analysis_minutes": 12,
            "trending_prediction_minutes": 10,
            "leaderboard_hours": 1,  # Changed from bi-daily to hourly
            "main_flow_hours": 2,
            "debate_strategy_hours": 2,
            "cleanup_minutes": 30,
            "disk_cleanup_hours": 6,
            "last_updated": datetime.now().isoformat(),
            "updated_by": "system_default"
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    stored_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    defaults.update(stored_config)
                    logger.info(
                        f"[CONFIG] Loaded scheduler intervals from {self.config_file}")
            except Exception as e:
                logger.warning(
                    f"[CONFIG] Failed to load config file: {e}, using defaults")
        else:
            logger.info(
                "[CONFIG] No scheduler config file found, using defaults")

        return defaults

    def _save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            self._intervals["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(self._intervals, f, indent=2)
            logger.info(
                f"[CONFIG] Saved scheduler intervals to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"[CONFIG] Failed to save config: {e}")
            return False

    def get_interval(self, job_name: str) -> Optional[int]:
        """Get interval for a specific job"""
        return self._intervals.get(f"{job_name}_minutes") or self._intervals.get(f"{job_name}_hours")

    def get_all_intervals(self) -> Dict:
        """Get all current intervals"""
        return self._intervals.copy()

    def update_interval(self, job_name: str, value: int, unit: str = "minutes", updated_by: str = "api") -> bool:
        """
        Update interval for a job

        Args:
            job_name: Job name (e.g., 'content_analysis', 'leaderboard')
            value: New interval value
            unit: 'minutes' or 'hours'
            updated_by: Who made the change
        """
        if unit not in ["minutes", "hours"]:
            logger.error(
                f"[CONFIG] Invalid unit: {unit}. Must be 'minutes' or 'hours'")
            return False

        if value <= 0:
            logger.error(
                f"[CONFIG] Invalid interval value: {value}. Must be positive")
            return False

        key = f"{job_name}_{unit}"
        old_value = self._intervals.get(key)

        self._intervals[key] = value
        self._intervals["updated_by"] = updated_by

        if self._save_config():
            logger.info(
                f"[CONFIG] Updated {job_name} interval: {old_value} -> {value} {unit} (by {updated_by})")
            return True
        else:
            # Rollback on save failure
            if old_value is not None:
                self._intervals[key] = old_value
            return False

    def reset_to_defaults(self, updated_by: str = "api") -> bool:
        """Reset all intervals to defaults"""
        defaults = {
            "content_analysis_minutes": 12,
            "trending_prediction_minutes": 10,
            "leaderboard_hours": 1,
            "main_flow_hours": 2,
            "debate_strategy_hours": 2,
            "cleanup_minutes": 30,
            "disk_cleanup_hours": 6,
            "updated_by": updated_by
        }

        old_config = self._intervals.copy()
        self._intervals.update(defaults)

        if self._save_config():
            logger.info(
                f"[CONFIG] Reset all intervals to defaults (by {updated_by})")
            return True
        else:
            # Rollback
            self._intervals = old_config
            return False


# Global instance
_scheduler_config = None


def get_scheduler_config() -> SchedulerConfig:
    """Get global scheduler configuration instance"""
    global _scheduler_config
    if _scheduler_config is None:
        _scheduler_config = SchedulerConfig()
    return _scheduler_config


def get_job_interval(job_name: str) -> int:
    """Get interval for a job (convenience function)"""
    config = get_scheduler_config()
    return config.get_interval(job_name) or 10  # Default fallback
