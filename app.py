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
                "/heartbeat",
                "/trigger-intelligence",
                "/trigger-content-analysis",
                "/trigger-engagement-analysis",
                "/engagement-quick-check"
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
            "heartbeat_message": f"[RED] Worker heartbeat at {now.strftime('%H:%M:%S UTC')}"
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

    @app.route('/trigger-content-analysis', methods=['POST'])
    def trigger_content_analysis():
        """Manually trigger content analysis task"""
        from datetime import datetime, timezone
        import asyncio

        logger.info("[TRIGGER] Manual content analysis trigger requested")

        try:
            if _worker and _worker.is_running and _worker.loop:
                # Import the content analysis task
                from worker.tasks.content_analysis_task import ContentAnalysisTask

                # Get parameters from request
                data_source = request.json.get('data_source', 'api') if request.json else 'api'
                num_posts = request.json.get('num_posts', 20) if request.json else 20

                logger.info(f"[TRIGGER] Starting content analysis - Source: {data_source}, Posts: {num_posts}")

                # Schedule content analysis task
                task = ContentAnalysisTask()
                future = asyncio.run_coroutine_threadsafe(
                    task.run_content_analysis_workflow(data_source=data_source, num_posts=num_posts),
                    _worker.loop
                )

                logger.info("[TRIGGER] Content analysis task scheduled successfully")

                return jsonify({
                    "status": "triggered",
                    "message": "Content analysis task started",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "parameters": {
                        "data_source": data_source,
                        "num_posts": num_posts
                    },
                    "task_info": {
                        "estimated_duration": f"{num_posts * 2} seconds",
                        "worker_running": _worker.is_running
                    },
                    "monitoring": {
                        "logs": "Monitor bot.log for detailed execution progress",
                        "status_endpoint": "/status"
                    }
                })
            else:
                return jsonify({
                    "error": "Worker event loop not available",
                    "worker_status": "loop_unavailable"
                }), 500

        except Exception as e:
            logger.error(f"Failed to trigger content analysis task: {e}")
            return jsonify({
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500

    @app.route('/trigger-content-analysis', methods=['GET'])
    def get_content_analysis_info():
        """Get information about the content analysis endpoint"""
        from datetime import datetime, timezone

        return jsonify({
            "endpoint": "/trigger-content-analysis",
            "method": "POST",
            "description": "AI-powered social media content analysis",
            "parameters": {
                "data_source": "api (real) or mock (test) - default: api",
                "num_posts": "Number of posts (1-50) - default: 20"
            },
            "features": [
                "Content quality analysis",
                "Sentiment and emotion detection", 
                "Hashtag effectiveness scoring",
                "AI-generated Discord reports",
                "Readability assessment"
            ],
            "usage": {
                "curl_example": 'curl -X POST http://localhost:5000/trigger-content-analysis -H "Content-Type: application/json" -d \'{"data_source": "api", "num_posts": 15}\''
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    @app.route('/trigger-engagement-analysis', methods=['POST'])
    def trigger_engagement_analysis():
        """Manually trigger engagement intelligence analysis"""
        from datetime import datetime, timezone
        import asyncio

        logger.info("[TRIGGER] Manual engagement analysis trigger requested")

        try:
            if _worker and _worker.is_running and _worker.loop:
                # Import the engagement intelligence task
                from worker.tasks.engagement_intelligence_task import EngagementIntelligenceTask

                # Get parameters from request
                send_discord = request.json.get('send_discord', True) if request.json else True
                save_results = request.json.get('save_results', True) if request.json else True

                logger.info(f"[TRIGGER] Starting engagement analysis - Discord: {send_discord}, Save: {save_results}")

                # Schedule engagement analysis task
                task = EngagementIntelligenceTask()
                future = asyncio.run_coroutine_threadsafe(
                    task.run_engagement_analysis_workflow(
                        send_discord=send_discord,
                        save_results=save_results
                    ),
                    _worker.loop
                )

                logger.info("[TRIGGER] Engagement analysis task scheduled successfully")

                return jsonify({
                    "status": "triggered",
                    "message": "Engagement intelligence analysis started",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "parameters": {
                        "send_discord": send_discord,
                        "save_results": save_results
                    },
                    "task_info": {
                        "estimated_duration": "30-60 seconds",
                        "worker_running": _worker.is_running,
                        "description": "Analyzes engagement growth between current and previous data snapshots"
                    },
                    "analysis_features": [
                        "Engagement deltas (Δlikes, Δreplies, Δreposts)",
                        "Engagement velocity calculation",
                        "Engagement acceleration analysis", 
                        "Top 5 fastest growing posts identification",
                        "Discord-formatted growth reports"
                    ],
                    "monitoring": {
                        "logs": "Monitor bot.log for detailed execution progress",
                        "status_endpoint": "/status",
                        "results_path": "data/reports/engagement/"
                    }
                })
            else:
                return jsonify({
                    "error": "Worker event loop not available",
                    "worker_status": "loop_unavailable"
                }), 500

        except Exception as e:
            logger.error(f"Failed to trigger engagement analysis task: {e}")
            return jsonify({
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500

    @app.route('/trigger-engagement-analysis', methods=['GET'])
    def get_engagement_analysis_info():
        """Get information about the engagement analysis endpoint"""
        from datetime import datetime, timezone

        return jsonify({
            "endpoint": "/trigger-engagement-analysis",
            "method": "POST",
            "description": "Social engagement intelligence analysis with growth tracking",
            "parameters": {
                "send_discord": "Send Discord notification (true/false) - default: true",
                "save_results": "Save results to disk (true/false) - default: true"
            },
            "features": [
                "Engagement velocity computation (Δtotal_engagement / Δtime)",
                "Engagement acceleration analysis (velocity change rate)",
                "Top 5 fastest growing posts identification",
                "Engagement composition analysis (likes/replies/reposts %)",
                "Discord-formatted growth reports with emojis"
            ],
            "analysis_outputs": {
                "velocity_metrics": "Average growth velocity per minute",
                "top_performers": "Ranked list of fastest growing posts",
                "composition_breakdown": "Percentage distribution of engagement types",
                "discord_message": "Emoji-rich Discord report format"
            },
            "sample_discord_output": [
                "[ANALYTICS] **Engagement Growth Report**",
                "• Avg Growth Velocity: +0.73 /min",
                "[LAUNCH] **Top 5 Fastest Posts:**",
                "   [1] @user1 — +1.2/min (+45 likes, +20 replies)",
                "[TRENDING_UP] **Engagement Composition:**",
                "   [HEART] Likes 62% | [CHAT] Replies 25% | [REPOST] Reposts 13%"
            ],
            "usage": {
                "curl_example": 'curl -X POST http://localhost:5000/trigger-engagement-analysis -H "Content-Type: application/json" -d \'{"send_discord": true, "save_results": true}\''
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    @app.route('/engagement-quick-check', methods=['GET'])
    def engagement_quick_check():
        """Quick engagement metrics check for real-time monitoring"""
        from datetime import datetime, timezone
        import asyncio

        try:
            if _worker and _worker.is_running and _worker.loop:
                from worker.tasks.engagement_intelligence_task import EngagementIntelligenceTask

                # Run quick check
                task = EngagementIntelligenceTask()
                future = asyncio.run_coroutine_threadsafe(
                    task.quick_engagement_check(),
                    _worker.loop
                )

                # Wait for result with timeout
                try:
                    quick_result = future.result(timeout=30)
                    
                    return jsonify({
                        "status": "success",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "quick_check_result": quick_result,
                        "description": "Real-time engagement metrics snapshot"
                    })
                    
                except asyncio.TimeoutError:
                    return jsonify({
                        "status": "timeout",
                        "message": "Quick check timed out after 30 seconds",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }), 408
                    
            else:
                return jsonify({
                    "error": "Worker not available",
                    "status": "unavailable"
                }), 503

        except Exception as e:
            logger.error(f"Quick engagement check failed: {e}")
            return jsonify({
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500


# if __name__ == '__main__':
#     app = create_app()
#     port = int(os.environ.get('PORT', 5000))
#     debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
#     print(f"Starting Background Worker Bot on port {port}")
#     app.run(host='0.0.0.0', port=port, debug=debug)
