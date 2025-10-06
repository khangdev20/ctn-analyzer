"""
Flask Background Worker Bot Application
Main application file for the background worker bot.
"""
import os
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from config.config import Config
from worker.base import BackgroundWorker
from worker.features.trending_config import get_metrics, get_topics_tracker, get_config

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global worker instance
_worker = None


def create_app():
    """Create and configure the Flask application."""
    global _worker

    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize background worker
    _worker = BackgroundWorker()

    # Add API routes
    register_api_routes(app)

    # Start the background worker automatically
    _worker.start()
    return app


def register_api_routes(app):
    """Register API routes for monitoring and control"""

    @app.route('/')
    def index():
        """Main dashboard endpoint"""
        from datetime import datetime, timezone

        # Calculate uptime if worker has start timestamp
        uptime_info = "Not available"
        if _worker and hasattr(_worker, 'start_timestamp'):
            uptime_delta = datetime.now(timezone.utc) - _worker.start_timestamp
            uptime_info = str(uptime_delta).split('.')[
                0]  # Remove microseconds

        return jsonify({
            "service": "Trending Intelligence Analyzer",
            "status": "running",
            "worker_status": "active" if _worker and _worker.is_running else "inactive",
            "active_tasks": len(_worker.active_tasks) if _worker else 0,
            "total_tasks": _worker.task_count if _worker else 0,
            "worker_uptime": uptime_info,
            "current_time": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            "endpoints": [
                "/metrics",
                "/topics",
                "/config",
                "/status",
                "/health",
                "/heartbeat"
            ]
        })

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        metrics = get_metrics()
        success_rate = metrics.get_success_rate()

        status = "healthy"
        if success_rate < 0.8 and metrics.total_runs > 5:
            status = "degraded"
        elif not _worker or not _worker.is_running:
            status = "unhealthy"

        return jsonify({
            "status": status,
            "worker_running": _worker.is_running if _worker else False,
            "success_rate": success_rate,
            "last_error": metrics.last_error,
            "uptime_check": "ok"
        })

    @app.route('/metrics')
    def get_pipeline_metrics():
        """Get detailed pipeline metrics"""
        metrics = get_metrics()
        return jsonify({
            "pipeline_metrics": metrics.to_dict(),
            "worker_status": {
                "is_running": _worker.is_running if _worker else False,
                "active_tasks": _worker.active_tasks if _worker else [],
                "task_count": _worker.task_count if _worker else 0
            }
        })

    @app.route('/heartbeat')
    def get_heartbeat():
        """Get worker heartbeat status - live activity monitoring"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        heartbeat_status = {
            "timestamp": now.isoformat(),
            "worker_alive": _worker.is_running if _worker else False,
            "worker_status": "active" if (_worker and _worker.is_running) else "inactive",
            "active_tasks": _worker.active_tasks if _worker else [],
            "total_tasks_run": _worker.task_count if _worker else 0,
            "heartbeat_count": _worker.heartbeat_count if _worker else 0,
            "last_heartbeat": _worker.last_heartbeat.isoformat() if (_worker and _worker.last_heartbeat) else None,
            "heartbeat_message": f"🔴 Worker heartbeat at {now.strftime('%H:%M:%S UTC')}"
        }

        # Add uptime if worker is running
        if _worker and _worker.start_timestamp:
            uptime_seconds = int(
                (now - _worker.start_timestamp).total_seconds())
            heartbeat_status["uptime_seconds"] = uptime_seconds
            heartbeat_status["uptime_display"] = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"

        return jsonify(heartbeat_status)

    @app.route('/topics')
    def get_trending_topics():
        """Get current trending topics"""
        topics_tracker = get_topics_tracker()
        lookback = request.args.get('lookback', 5, type=int)

        trending_topics = topics_tracker.get_trending_topics(
            lookback_periods=lookback)

        return jsonify({
            "trending_topics": trending_topics[:20],  # Top 20
            "total_topics_tracked": len(topics_tracker.topic_trends),
            "history_length": len(topics_tracker.topic_history),
            "lookback_periods": lookback
        })

    @app.route('/topics/<topic_name>')
    def get_topic_trend(topic_name):
        """Get trend data for specific topic"""
        topics_tracker = get_topics_tracker()
        trend_data = topics_tracker.get_topic_trend(topic_name)

        if not trend_data:
            return jsonify({"error": f"Topic '{topic_name}' not found"}), 404

        return jsonify({
            "topic": topic_name,
            "trend_data": trend_data,
            "data_points": len(trend_data)
        })

    @app.route('/config')
    def get_pipeline_config():
        """Get current pipeline configuration"""
        config = get_config()
        return jsonify({
            "collection_interval_minutes": config.collection_interval_minutes,
            "batch_size": config.batch_size,
            "llm_model": config.llm_model,
            "discord_notifications_enabled": config.discord_notifications_enabled,
            "viral_threshold_score": config.viral_threshold_score,
            "max_processing_time_minutes": config.max_processing_time_minutes,
            "data_paths": {
                "raw_data": config.raw_data_path,
                "processed_data": config.processed_data_path,
                "reports": config.reports_path
            }
        })

    @app.route('/status')
    def get_system_status():
        """Get comprehensive system status"""
        metrics = get_metrics()
        config = get_config()
        topics_tracker = get_topics_tracker()

        return jsonify({
            "system_status": {
                "worker_running": _worker.is_running if _worker else False,
                "active_tasks": len(_worker.active_tasks) if _worker else 0,
                "last_run": metrics.last_run_timestamp,
                "total_runs": metrics.total_runs,
                "success_rate": metrics.get_success_rate()
            },
            "pipeline_config": {
                "interval_minutes": config.collection_interval_minutes,
                "batch_size": config.batch_size,
                "llm_enabled": config.llm_analysis_enabled,
                "notifications_enabled": config.discord_notifications_enabled
            },
            "data_status": {
                "topics_tracked": len(topics_tracker.topic_trends),
                "history_length": len(topics_tracker.topic_history),
                "posts_processed": metrics.total_posts_processed
            },
            "performance": {
                "avg_processing_time": metrics.average_processing_time,
                "stage_success_rates": {
                    stage: metrics.get_stage_success_rate(stage)
                    for stage in metrics.stage_performance.keys()
                }
            }
        })

    @app.route('/trigger-intelligence', methods=['POST'])
    def trigger_intelligence_task():
        """Manually trigger trending intelligence task for testing"""
        if not _worker or not _worker.is_running:
            return jsonify({
                "error": "Worker not running",
                "worker_status": "inactive",
                "help": "Make sure the worker service is started"
            }), 503

        try:
            import asyncio
            from datetime import datetime, timezone

            # Get the current event loop
            if hasattr(_worker, '_loop') and _worker._loop:
                trigger_time = datetime.now(timezone.utc)

                # Schedule the task in the worker's event loop
                future = asyncio.run_coroutine_threadsafe(
                    _worker._run_trending_intelligence_task_with_cleanup(),
                    _worker._loop
                )

                return jsonify({
                    "status": "success",
                    "message": "Trending intelligence task triggered successfully",
                    "triggered_at": trigger_time.isoformat(),
                    "task_id": f"manual_trigger_{trigger_time.strftime('%Y%m%dT%H%M%SZ')}",
                    "task_scheduled": True,
                    "worker_status": {
                        "active_tasks": len(_worker.active_tasks),
                        "total_tasks": _worker.task_count,
                        "worker_running": _worker.is_running
                    },
                    "expected_completion": "Check /metrics endpoint for progress",
                    "monitoring": {
                        "logs": "Monitor bot.log for detailed execution progress",
                        "status_endpoint": "/status",
                        "metrics_endpoint": "/metrics"
                    }
                })
            else:
                return jsonify({
                    "error": "Worker event loop not available",
                    "worker_status": "loop_unavailable",
                    "help": "Worker may be starting up or crashed"
                }), 500

        except Exception as e:
            logger.error(f"Failed to trigger intelligence task: {e}")
            return jsonify({
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500

    @app.route('/trigger-intelligence', methods=['GET'])
    def get_trigger_info():
        """Get information about the manual trigger endpoint"""
        from datetime import datetime, timezone

        return jsonify({
            "endpoint": "/trigger-intelligence",
            "method": "POST",
            "description": "Manually trigger the trending intelligence task",
            "current_status": {
                "worker_running": _worker.is_running if _worker else False,
                "active_tasks": len(_worker.active_tasks) if _worker else 0,
                "can_trigger": (_worker and _worker.is_running) if _worker else False
            },
            "usage": {
                "curl_example": "curl -X POST http://localhost:5000/trigger-intelligence",
                "expected_response": "JSON with trigger confirmation and task details"
            },
            "monitoring": {
                "progress": "Check /status and /metrics endpoints",
                "logs": "Monitor bot.log for detailed execution progress",
                "completion": "Task typically takes 5-15 minutes depending on data volume"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    @app.route('/trigger', methods=['POST'])
    def trigger_alias():
        """Alias for /trigger-intelligence for easier access"""
        return trigger_intelligence_task()


# if __name__ == '__main__':
#     app = create_app()
#     port = int(os.environ.get('PORT', 5000))
#     debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
#     print(f"Starting Background Worker Bot on port {port}")
#     app.run(host='0.0.0.0', port=port, debug=debug)
