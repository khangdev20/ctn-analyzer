"""
Disk Cleanup Worker - Manages storage space and data retention
Automatically cleans old data files and manages disk usage

Author: AI Assistant
Date: October 7, 2025
"""

import asyncio
import logging
import os
import shutil
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List
import glob

logger = logging.getLogger(__name__)


class DiskCleanupWorker:
    """
    Worker to manage disk space and clean up old data files
    """

    def __init__(self, config: Dict = None):
        """Initialize disk cleanup worker with configuration"""
        self.config = config or self._get_default_config()
        self.base_path = Path(".")
        self.data_paths = [
            "data/raw",
            "data/processed",
            "data/reports",
            "logs",
            "cleanup_deprecated"
        ]

    def _get_default_config(self) -> Dict:
        """Get default cleanup configuration"""
        return {
            # Disk usage thresholds
            "max_disk_usage_percent": 85,
            "target_disk_usage_percent": 70,

            # Data retention periods (days)
            "retention_periods": {
                "raw_data": 30,      # Keep raw data for 30 days
                "processed_data": 60,  # Keep processed data for 60 days
                "reports": 90,       # Keep reports for 90 days
                "logs": 14,          # Keep logs for 14 days
                "deprecated": 7      # Clean deprecated files after 7 days
            },

            # File size limits (MB)
            "max_file_sizes": {
                "log_file": 100,     # Max 100MB per log file
                "data_file": 500,    # Max 500MB per data file
                "total_directory": 5000  # Max 5GB per directory
            },

            # Cleanup patterns
            "cleanup_patterns": [
                "*.tmp",
                "*.log.old*",
                "*_backup_*",
                "trending_data_*.json"  # Old trending data files
            ]
        }

    async def run_cleanup_cycle(self) -> Dict:
        """
        Run a complete cleanup cycle

        Returns:
            Dict with cleanup results
        """
        start_time = datetime.now(timezone.utc)
        logger.info("[CLEANUP] Starting disk cleanup cycle...")

        results = {
            "start_time": start_time.isoformat(),
            "cleaned_files": [],
            "freed_space_mb": 0,
            "errors": [],
            "disk_usage_before": {},
            "disk_usage_after": {}
        }

        try:
            # Check disk usage before cleanup
            results["disk_usage_before"] = await self._get_disk_usage()

            # Phase 1: Clean by age
            age_results = await self._cleanup_by_age()
            results["cleaned_files"].extend(age_results["files"])
            results["freed_space_mb"] += age_results["freed_mb"]

            # Phase 2: Clean by size
            size_results = await self._cleanup_by_size()
            results["cleaned_files"].extend(size_results["files"])
            results["freed_space_mb"] += size_results["freed_mb"]

            # Phase 3: Clean by patterns
            pattern_results = await self._cleanup_by_patterns()
            results["cleaned_files"].extend(pattern_results["files"])
            results["freed_space_mb"] += pattern_results["freed_mb"]

            # Phase 4: Compress old files
            compress_results = await self._compress_old_files()
            results["freed_space_mb"] += compress_results["freed_mb"]

            # Check disk usage after cleanup
            results["disk_usage_after"] = await self._get_disk_usage()

            # Generate summary
            execution_time = (datetime.now(timezone.utc) -
                              start_time).total_seconds()
            results["execution_time_seconds"] = execution_time
            results["files_cleaned"] = len(results["cleaned_files"])

            logger.info(
                f"[OK] Cleanup completed: {results['files_cleaned']} files, {results['freed_space_mb']:.1f}MB freed")

            return results

        except Exception as e:
            logger.error(f"[ERROR] Cleanup cycle failed: {str(e)}")
            results["errors"].append(str(e))
            return results

    async def _get_disk_usage(self) -> Dict:
        """Get current disk usage statistics"""
        try:
            usage = {}

            for path_name in self.data_paths:
                path = Path(path_name)
                if path.exists():
                    size = await self._get_directory_size(path)
                    usage[path_name] = {
                        "size_mb": size / (1024 * 1024),
                        "files": len(list(path.rglob("*"))) if path.is_dir() else 1
                    }

            # Get total disk usage
            if os.name == 'nt':  # Windows
                import psutil
                disk = psutil.disk_usage('.')
                usage["total_disk"] = {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent_used": (disk.used / disk.total) * 100
                }
            else:  # Unix-like
                statvfs = os.statvfs('.')
                usage["total_disk"] = {
                    "total_gb": (statvfs.f_frsize * statvfs.f_blocks) / (1024**3),
                    "used_gb": (statvfs.f_frsize * (statvfs.f_blocks - statvfs.f_available)) / (1024**3),
                    "free_gb": (statvfs.f_frsize * statvfs.f_available) / (1024**3),
                    "percent_used": ((statvfs.f_blocks - statvfs.f_available) / statvfs.f_blocks) * 100
                }

            return usage

        except Exception as e:
            logger.error(f"Error getting disk usage: {str(e)}")
            return {}

    async def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            if path.is_file():
                return path.stat().st_size

            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Error calculating size for {path}: {str(e)}")

        return total_size

    async def _cleanup_by_age(self) -> Dict:
        """Clean files based on age retention policies"""
        results = {"files": [], "freed_mb": 0}

        try:
            now = datetime.now(timezone.utc)

            for path_name, retention_days in self.config["retention_periods"].items():
                # Map path names to actual paths
                if path_name == "raw_data":
                    search_path = Path("data/raw")
                elif path_name == "processed_data":
                    search_path = Path("data/processed")
                elif path_name == "reports":
                    search_path = Path("data/reports")
                elif path_name == "logs":
                    search_path = Path("logs")
                elif path_name == "deprecated":
                    search_path = Path("cleanup_deprecated")
                else:
                    continue

                if not search_path.exists():
                    continue

                cutoff_time = now - timedelta(days=retention_days)

                # Find old files
                for file_path in search_path.rglob("*"):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(
                            file_path.stat().st_mtime, tz=timezone.utc)

                        if file_time < cutoff_time:
                            try:
                                file_size = file_path.stat().st_size
                                file_path.unlink()

                                results["files"].append({
                                    "path": str(file_path),
                                    "size_mb": file_size / (1024 * 1024),
                                    "reason": f"Age > {retention_days} days"
                                })
                                results["freed_mb"] += file_size / \
                                    (1024 * 1024)

                            except Exception as e:
                                logger.warning(
                                    f"Failed to delete {file_path}: {str(e)}")

            logger.info(
                f"🗓️ Age-based cleanup: {len(results['files'])} files, {results['freed_mb']:.1f}MB")

        except Exception as e:
            logger.error(f"Age-based cleanup failed: {str(e)}")

        return results

    async def _cleanup_by_size(self) -> Dict:
        """Clean files that exceed size limits"""
        results = {"files": [], "freed_mb": 0}

        try:
            # Clean oversized individual files
            for path_name in self.data_paths:
                path = Path(path_name)
                if not path.exists():
                    continue

                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)

                        # Check if file exceeds size limit
                        max_size = self.config["max_file_sizes"]["data_file"]
                        if file_path.suffix == ".log":
                            max_size = self.config["max_file_sizes"]["log_file"]

                        if file_size_mb > max_size:
                            try:
                                file_path.unlink()
                                results["files"].append({
                                    "path": str(file_path),
                                    "size_mb": file_size_mb,
                                    "reason": f"Size > {max_size}MB"
                                })
                                results["freed_mb"] += file_size_mb

                            except Exception as e:
                                logger.warning(
                                    f"Failed to delete oversized file {file_path}: {str(e)}")

            # Clean directories that exceed total size
            await self._cleanup_oversized_directories(results)

            logger.info(
                f"📏 Size-based cleanup: {len(results['files'])} files, {results['freed_mb']:.1f}MB")

        except Exception as e:
            logger.error(f"Size-based cleanup failed: {str(e)}")

        return results

    async def _cleanup_oversized_directories(self, results: Dict):
        """Clean directories that exceed total size limits"""
        max_dir_size_mb = self.config["max_file_sizes"]["total_directory"]

        for path_name in self.data_paths:
            path = Path(path_name)
            if not path.exists():
                continue

            dir_size = await self._get_directory_size(path)
            dir_size_mb = dir_size / (1024 * 1024)

            if dir_size_mb > max_dir_size_mb:
                # Get files sorted by age (oldest first)
                files = []
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        files.append((file_path, file_path.stat().st_mtime))

                files.sort(key=lambda x: x[1])  # Sort by modification time

                # Delete oldest files until under limit
                current_size_mb = dir_size_mb
                for file_path, _ in files:
                    if current_size_mb <= max_dir_size_mb:
                        break

                    try:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        file_path.unlink()

                        results["files"].append({
                            "path": str(file_path),
                            "size_mb": file_size_mb,
                            "reason": f"Directory > {max_dir_size_mb}MB"
                        })
                        results["freed_mb"] += file_size_mb
                        current_size_mb -= file_size_mb

                    except Exception as e:
                        logger.warning(
                            f"Failed to delete {file_path}: {str(e)}")

    async def _cleanup_by_patterns(self) -> Dict:
        """Clean files matching cleanup patterns"""
        results = {"files": [], "freed_mb": 0}

        try:
            for pattern in self.config["cleanup_patterns"]:
                # Search in all data paths
                for path_name in self.data_paths:
                    path = Path(path_name)
                    if not path.exists():
                        continue

                    # Find files matching pattern
                    for file_path in path.rglob(pattern):
                        if file_path.is_file():
                            try:
                                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                                file_path.unlink()

                                results["files"].append({
                                    "path": str(file_path),
                                    "size_mb": file_size_mb,
                                    "reason": f"Pattern: {pattern}"
                                })
                                results["freed_mb"] += file_size_mb

                            except Exception as e:
                                logger.warning(
                                    f"Failed to delete {file_path}: {str(e)}")

            logger.info(
                f"[TARGET] Pattern-based cleanup: {len(results['files'])} files, {results['freed_mb']:.1f}MB")

        except Exception as e:
            logger.error(f"Pattern-based cleanup failed: {str(e)}")

        return results

    async def _compress_old_files(self) -> Dict:
        """Compress old files to save space"""
        results = {"freed_mb": 0}

        try:
            import gzip

            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)

            for path_name in ["logs", "data/reports"]:
                path = Path(path_name)
                if not path.exists():
                    continue

                for file_path in path.rglob("*.log"):
                    if file_path.is_file() and not file_path.name.endswith('.gz'):
                        file_time = datetime.fromtimestamp(
                            file_path.stat().st_mtime, tz=timezone.utc)

                        if file_time < cutoff_time:
                            try:
                                original_size = file_path.stat().st_size
                                compressed_path = file_path.with_suffix(
                                    file_path.suffix + '.gz')

                                # Compress file
                                with open(file_path, 'rb') as f_in:
                                    with gzip.open(compressed_path, 'wb') as f_out:
                                        shutil.copyfileobj(f_in, f_out)

                                # Remove original file
                                file_path.unlink()

                                compressed_size = compressed_path.stat().st_size
                                space_saved = (original_size -
                                               compressed_size) / (1024 * 1024)
                                results["freed_mb"] += space_saved

                                logger.debug(
                                    f"Compressed {file_path.name}: {space_saved:.1f}MB saved")

                            except Exception as e:
                                logger.warning(
                                    f"Failed to compress {file_path}: {str(e)}")

            if results["freed_mb"] > 0:
                logger.info(
                    f"🗜️ Compression: {results['freed_mb']:.1f}MB saved")

        except ImportError:
            logger.warning("gzip module not available, skipping compression")
        except Exception as e:
            logger.error(f"Compression failed: {str(e)}")

        return results

    async def check_disk_health(self) -> Dict:
        """Check current disk health and usage"""
        try:
            usage = await self._get_disk_usage()

            # Calculate health status
            total_disk = usage.get("total_disk", {})
            percent_used = total_disk.get("percent_used", 0)

            health_status = "healthy"
            if percent_used > self.config["max_disk_usage_percent"]:
                health_status = "critical"
            elif percent_used > self.config["target_disk_usage_percent"]:
                health_status = "warning"

            return {
                "status": health_status,
                "disk_usage_percent": percent_used,
                "disk_usage": usage,
                "needs_cleanup": percent_used > self.config["target_disk_usage_percent"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def emergency_cleanup(self) -> Dict:
        """Perform emergency cleanup when disk space is critically low"""
        logger.warning("[WARNING] Performing emergency disk cleanup...")

        # More aggressive cleanup
        original_config = self.config.copy()

        # Reduce retention periods for emergency
        self.config["retention_periods"] = {
            "raw_data": 7,       # Keep only 7 days
            "processed_data": 14,  # Keep only 14 days
            "reports": 30,       # Keep only 30 days
            "logs": 3,           # Keep only 3 days
            "deprecated": 1      # Clean immediately
        }

        # Reduce file size limits
        self.config["max_file_sizes"]["total_directory"] = 1000  # 1GB limit

        try:
            results = await self.run_cleanup_cycle()
            results["emergency_mode"] = True

            logger.info(
                f"[ALERT] Emergency cleanup completed: {results['freed_space_mb']:.1f}MB freed")

            return results

        finally:
            # Restore original config
            self.config = original_config


# Async task function for scheduler integration
async def run_disk_cleanup_task(worker) -> Dict:
    """Task function for the worker scheduler"""
    task_id = f"disk_cleanup_{worker.task_count}"
    worker.task_count += 1
    worker.active_tasks.append(task_id)

    try:
        logger.info(f"[CLEANUP] Starting disk cleanup task: {task_id}")

        cleanup_worker = DiskCleanupWorker()

        # Check if cleanup is needed
        health = await cleanup_worker.check_disk_health()

        if health["needs_cleanup"]:
            if health["status"] == "critical":
                results = await cleanup_worker.emergency_cleanup()
            else:
                results = await cleanup_worker.run_cleanup_cycle()

            logger.info(
                f"[OK] Disk cleanup completed: {results['files_cleaned']} files cleaned")
        else:
            logger.info("[OK] Disk cleanup skipped: disk usage is healthy")
            results = {"status": "skipped", "reason": "disk usage is healthy"}

        return results

    except Exception as e:
        logger.error(f"[ERROR] Disk cleanup task failed: {str(e)}")
        return {"status": "error", "error": str(e)}

    finally:
        if task_id in worker.active_tasks:
            worker.active_tasks.remove(task_id)


if __name__ == "__main__":
    # Test the disk cleanup worker
    async def test_cleanup():
        cleanup_worker = DiskCleanupWorker()

        # Check disk health
        health = await cleanup_worker.check_disk_health()
        print(f"Disk Health: {health}")

        # Run cleanup if needed
        if health["needs_cleanup"]:
            results = await cleanup_worker.run_cleanup_cycle()
            print(f"Cleanup Results: {results}")

    asyncio.run(test_cleanup())
