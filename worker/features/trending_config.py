"""
Trending Intelligence Configuration
Cấu hình chi tiết cho pipeline phân tích trending
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


@dataclass
class TrendingIntelligenceConfig:
    """Configuration for trending intelligence pipeline"""

    # Pipeline scheduling
    collection_interval_minutes: int = 15  # Every 15 minutes
    batch_size: int = 3  # Number of pages to collect per batch

    # Data storage paths
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"
    reports_path: str = "data/reports"

    # Analysis parameters
    min_post_length: int = 10  # Minimum content length
    engagement_threshold_percentile: float = 0.75  # Top 25% for high engagement
    viral_threshold_score: float = 80.0  # Viral potential threshold

    # Feature extraction settings
    max_hashtags_to_analyze: int = 20
    min_hashtag_frequency: int = 2
    emotion_analysis_enabled: bool = True
    viral_pattern_analysis_enabled: bool = True

    # LLM settings
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.7
    llm_analysis_enabled: bool = True

    # Notification settings
    discord_notifications_enabled: bool = True
    # Only notify for high-quality insights
    notification_threshold_score: float = 70.0
    max_insights_per_notification: int = 3

    # Performance monitoring
    max_processing_time_minutes: int = 10  # Max time per pipeline run
    retry_attempts: int = 3
    retry_delay_seconds: int = 30

    # Data retention
    raw_data_retention_days: int = 30
    processed_data_retention_days: int = 90
    reports_retention_days: int = 365

    # Quality filters
    min_engagement_for_analysis: int = 5  # Minimum total engagement
    exclude_retweets: bool = False
    exclude_short_posts: bool = True
    verified_author_bonus: float = 1.2


class PipelineMetrics:
    """Track pipeline performance metrics"""

    def __init__(self):
        self.reset_metrics()

    def reset_metrics(self):
        """Reset all metrics to initial state"""
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.average_processing_time = 0.0
        self.total_posts_processed = 0
        self.last_run_timestamp = None
        self.last_error = None
        self.stage_performance = {
            'collect': {'success': 0, 'failure': 0, 'avg_time': 0.0},
            'clean': {'success': 0, 'failure': 0, 'avg_time': 0.0},
            'score': {'success': 0, 'failure': 0, 'avg_time': 0.0},
            'analyze': {'success': 0, 'failure': 0, 'avg_time': 0.0},
            'notify': {'success': 0, 'failure': 0, 'avg_time': 0.0}
        }

    def record_run(self, success: bool, processing_time: float, posts_count: int, error: str = None):
        """Record metrics for a pipeline run"""
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
            self.last_error = error

        # Update average processing time
        self.average_processing_time = (
            (self.average_processing_time * (self.total_runs - 1) +
             processing_time) / self.total_runs
        )

        self.total_posts_processed += posts_count
        self.last_run_timestamp = datetime.now(timezone.utc).isoformat()

    def record_stage_performance(self, stage: str, success: bool, processing_time: float):
        """Record performance for individual stage"""
        if stage not in self.stage_performance:
            return

        if success:
            self.stage_performance[stage]['success'] += 1
        else:
            self.stage_performance[stage]['failure'] += 1

        # Update average time
        total_attempts = (
            self.stage_performance[stage]['success'] +
            self.stage_performance[stage]['failure']
        )
        current_avg = self.stage_performance[stage]['avg_time']
        self.stage_performance[stage]['avg_time'] = (
            (current_avg * (total_attempts - 1) + processing_time) / total_attempts
        )

    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    def get_stage_success_rate(self, stage: str) -> float:
        """Calculate success rate for specific stage"""
        if stage not in self.stage_performance:
            return 0.0

        stage_data = self.stage_performance[stage]
        total = stage_data['success'] + stage_data['failure']
        if total == 0:
            return 0.0
        return stage_data['success'] / total

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary"""
        return {
            'total_runs': self.total_runs,
            'successful_runs': self.successful_runs,
            'failed_runs': self.failed_runs,
            'success_rate': self.get_success_rate(),
            'average_processing_time': self.average_processing_time,
            'total_posts_processed': self.total_posts_processed,
            'last_run_timestamp': self.last_run_timestamp,
            'last_error': self.last_error,
            'stage_performance': {
                stage: {
                    **data,
                    'success_rate': self.get_stage_success_rate(stage)
                }
                for stage, data in self.stage_performance.items()
            }
        }


class TrendingTopicsTracker:
    """Track trending topics over time"""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.topic_history = []  # List of (timestamp, topics) tuples
        self.topic_trends = {}  # topic -> list of scores over time

    def update_topics(self, topics: List[Dict], timestamp: str = None):
        """Update topics with new data"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        # Add to history
        self.topic_history.append((timestamp, topics))

        # Maintain max history size
        if len(self.topic_history) > self.max_history:
            self.topic_history.pop(0)

        # Update trends
        for topic_data in topics:
            topic_name = topic_data.get(
                'name', topic_data.get('topic', 'unknown'))
            score = topic_data.get(
                'score', topic_data.get('engagement_score', 0))

            if topic_name not in self.topic_trends:
                self.topic_trends[topic_name] = []

            self.topic_trends[topic_name].append((timestamp, score))

            # Maintain trend history
            if len(self.topic_trends[topic_name]) > self.max_history:
                self.topic_trends[topic_name].pop(0)

    def get_trending_topics(self, lookback_periods: int = 5) -> List[Dict]:
        """Get currently trending topics based on recent data"""
        if not self.topic_history:
            return []

        recent_periods = self.topic_history[-lookback_periods:]
        topic_scores = {}

        for timestamp, topics in recent_periods:
            for topic_data in topics:
                topic_name = topic_data.get(
                    'name', topic_data.get('topic', 'unknown'))
                score = topic_data.get(
                    'score', topic_data.get('engagement_score', 0))

                if topic_name not in topic_scores:
                    topic_scores[topic_name] = []
                topic_scores[topic_name].append(score)

        # Calculate trending score (recent average with momentum)
        trending_topics = []
        for topic, scores in topic_scores.items():
            if len(scores) >= 2:  # Need at least 2 data points
                recent_avg = sum(scores) / len(scores)
                momentum = scores[-1] - scores[0] if len(scores) > 1 else 0
                trending_score = recent_avg + momentum * 0.1  # 10% weight for momentum

                trending_topics.append({
                    'topic': topic,
                    'trending_score': trending_score,
                    'recent_average': recent_avg,
                    'momentum': momentum,
                    'appearances': len(scores)
                })

        # Sort by trending score
        trending_topics.sort(key=lambda x: x['trending_score'], reverse=True)
        return trending_topics

    def get_topic_trend(self, topic: str) -> List[Tuple[str, float]]:
        """Get historical trend for specific topic"""
        return self.topic_trends.get(topic, [])


# Global configuration instance
config = TrendingIntelligenceConfig()

# Global metrics instance
metrics = PipelineMetrics()

# Global topics tracker
topics_tracker = TrendingTopicsTracker()


def get_config() -> TrendingIntelligenceConfig:
    """Get current configuration"""
    return config


def update_config(**kwargs) -> TrendingIntelligenceConfig:
    """Update configuration with new values"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def get_metrics() -> PipelineMetrics:
    """Get current metrics"""
    return metrics


def get_topics_tracker() -> TrendingTopicsTracker:
    """Get current topics tracker"""
    return topics_tracker


def load_config_from_env():
    """Load configuration from environment variables"""
    env_mapping = {
        'TRENDING_COLLECTION_INTERVAL': ('collection_interval_minutes', int),
        'TRENDING_BATCH_SIZE': ('batch_size', int),
        'TRENDING_LLM_MODEL': ('llm_model', str),
        'TRENDING_DISCORD_ENABLED': ('discord_notifications_enabled', lambda x: x.lower() == 'true'),
        'TRENDING_VIRAL_THRESHOLD': ('viral_threshold_score', float),
        'TRENDING_MAX_PROCESSING_TIME': ('max_processing_time_minutes', int),
    }

    for env_var, (config_attr, converter) in env_mapping.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                converted_value = converter(env_value)
                setattr(config, config_attr, converted_value)
            except (ValueError, TypeError) as e:
                print(f"Warning: Failed to convert {env_var}={env_value}: {e}")


def save_metrics_to_file(filepath: str = "trending_metrics.json"):
    """Save current metrics to file"""
    import json
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)
    except Exception as e:
        print(f"Failed to save metrics: {e}")


def load_metrics_from_file(filepath: str = "trending_metrics.json"):
    """Load metrics from file"""
    import json
    global metrics
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)

            metrics.total_runs = data.get('total_runs', 0)
            metrics.successful_runs = data.get('successful_runs', 0)
            metrics.failed_runs = data.get('failed_runs', 0)
            metrics.average_processing_time = data.get(
                'average_processing_time', 0.0)
            metrics.total_posts_processed = data.get(
                'total_posts_processed', 0)
            metrics.last_run_timestamp = data.get('last_run_timestamp')
            metrics.last_error = data.get('last_error')

            if 'stage_performance' in data:
                for stage, stage_data in data['stage_performance'].items():
                    if stage in metrics.stage_performance:
                        metrics.stage_performance[stage].update({
                            'success': stage_data.get('success', 0),
                            'failure': stage_data.get('failure', 0),
                            'avg_time': stage_data.get('avg_time', 0.0)
                        })
    except Exception as e:
        print(f"Failed to load metrics: {e}")


# Load configuration from environment on import
load_config_from_env()
load_metrics_from_file()
