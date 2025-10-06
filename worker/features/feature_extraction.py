"""
Feature extraction utilities for social media posts analysis
Advanced feature engineering for trending intelligence pipeline
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import re
import string
import logging
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PostFeatureExtractor:
    """Extract advanced features from social media posts"""

    def __init__(self):
        self.emotion_keywords = {
            'positive': ['amazing', 'great', 'excellent', 'awesome', 'fantastic', 'perfect', 'love', 'best', 'wonderful', 'brilliant'],
            'negative': ['terrible', 'awful', 'hate', 'worst', 'horrible', 'bad', 'disappointing', 'failed', 'disaster', 'wrong'],
            'urgency': ['now', 'urgent', 'immediate', 'quickly', 'asap', 'breaking', 'alert', 'emergency', 'critical', 'hurry'],
            'engagement': ['please', 'help', 'share', 'comment', 'like', 'follow', 'subscribe', 'join', 'participate', 'vote']
        }

        self.viral_patterns = [
            r'\b(breaking|urgent|alert)\b',
            r'\b(must see|don\'t miss|incredible)\b',
            r'\b(shocking|unbelievable|amazing)\b',
            r'\?+',  # Multiple question marks
            r'!+',   # Multiple exclamation marks
        ]

    def extract_all_features(self, post: Dict) -> Dict:
        """Extract comprehensive feature set from a post"""
        content = post.get('content', '')

        features = {}

        # Basic content features
        features.update(self._extract_content_features(content))

        # Linguistic features
        features.update(self._extract_linguistic_features(content))

        # Emotional features
        features.update(self._extract_emotional_features(content))

        # Viral potential features
        features.update(self._extract_viral_features(content))

        # Temporal features
        features.update(self._extract_temporal_features(
            post.get('created_at', '')))

        # Author influence features
        features.update(self._extract_author_features(post.get('author', {})))

        # Engagement prediction features
        features.update(self._extract_engagement_features(post))

        return features

    def _extract_content_features(self, content: str) -> Dict:
        """Extract basic content characteristics"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)

        return {
            'char_count': len(content),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
            'punctuation_ratio': sum(1 for c in content if c in string.punctuation) / len(content) if content else 0,
            'uppercase_ratio': sum(1 for c in content if c.isupper()) / len(content) if content else 0,
            'digit_count': sum(1 for c in content if c.isdigit()),
            'url_count': len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)),
            'mention_count': len(re.findall(r'@\w+', content)),
            'hashtag_count': len(re.findall(r'#\w+', content))
        }

    def _extract_linguistic_features(self, content: str) -> Dict:
        """Extract linguistic patterns and complexity"""
        # Question and exclamation patterns
        question_marks = content.count('?')
        exclamation_marks = content.count('!')

        # Repetitive patterns
        # Characters repeated 3+ times
        repeated_chars = len(re.findall(r'(.)\1{2,}', content))
        repeated_words = len(re.findall(
            r'\b(\w+)\s+\1\b', content.lower()))  # Repeated words

        # Capitalization patterns
        all_caps_words = len(re.findall(r'\b[A-Z]{2,}\b', content))

        return {
            'question_marks': question_marks,
            'exclamation_marks': exclamation_marks,
            'total_emphasis_marks': question_marks + exclamation_marks,
            'repeated_chars': repeated_chars,
            'repeated_words': repeated_words,
            'all_caps_words': all_caps_words,
            'has_ellipsis': '...' in content,
            'has_quotes': '"' in content or "'" in content,
            'parentheses_count': content.count('(') + content.count(')')
        }

    def _extract_emotional_features(self, content: str) -> Dict:
        """Extract emotional indicators"""
        content_lower = content.lower()
        words = content_lower.split()

        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for word in words if any(
                keyword in word for keyword in keywords))
            emotion_scores[f'{emotion}_words'] = score
            emotion_scores[f'{emotion}_score'] = score / \
                len(words) if words else 0

        # Emotional intensity
        total_emotional_words = sum(
            emotion_scores[f'{emotion}_words'] for emotion in self.emotion_keywords.keys())

        return {
            **emotion_scores,
            'total_emotional_words': total_emotional_words,
            'emotional_intensity': total_emotional_words / len(words) if words else 0,
            'sentiment_polarity': emotion_scores['positive_words'] - emotion_scores['negative_words']
        }

    def _extract_viral_features(self, content: str) -> Dict:
        """Extract features that indicate viral potential"""
        viral_indicators = 0

        for pattern in self.viral_patterns:
            viral_indicators += len(re.findall(pattern,
                                    content, re.IGNORECASE))

        # Call-to-action phrases
        cta_patterns = ['share if', 'comment below',
                        'tag a friend', 'what do you think', 'agree or disagree']
        cta_count = sum(
            1 for pattern in cta_patterns if pattern in content.lower())

        # Controversial indicators
        controversial_words = ['debate', 'controversial',
                               'opinion', 'thoughts', 'disagree', 'argue', 'discuss']
        controversy_score = sum(
            1 for word in controversial_words if word in content.lower())

        return {
            'viral_indicators': viral_indicators,
            'cta_count': cta_count,
            'controversy_score': controversy_score,
            'viral_potential_score': viral_indicators + cta_count * 2 + controversy_score,
            'has_call_to_action': cta_count > 0,
            'has_viral_keywords': viral_indicators > 0
        }

    def _extract_temporal_features(self, created_at: str) -> Dict:
        """Extract temporal posting patterns"""
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

            return {
                'hour_of_day': dt.hour,
                'day_of_week': dt.weekday(),  # 0=Monday, 6=Sunday
                'is_weekend': dt.weekday() >= 5,
                'is_prime_time': 18 <= dt.hour <= 22,  # 6-10 PM
                'is_morning': 6 <= dt.hour <= 11,
                'is_afternoon': 12 <= dt.hour <= 17,
                'is_evening': 18 <= dt.hour <= 23,
                'is_night': dt.hour < 6 or dt.hour > 23,
                'time_since_hour_start': dt.minute,
                'quarter_of_hour': dt.minute // 15
            }
        except Exception as e:
            logger.debug(f"Failed to parse timestamp {created_at}: {e}")
            return {
                'hour_of_day': 12,  # Default to noon
                'day_of_week': 1,   # Default to Tuesday
                'is_weekend': False,
                'is_prime_time': False,
                'is_morning': False,
                'is_afternoon': True,
                'is_evening': False,
                'is_night': False,
                'time_since_hour_start': 0,
                'quarter_of_hour': 0
            }

    def _extract_author_features(self, author: Dict) -> Dict:
        """Extract author influence indicators"""
        follower_count = author.get('follower_count', 0)

        # Influence tiers
        influence_tier = 'micro'  # < 1K
        if follower_count >= 1000000:
            influence_tier = 'mega'
        elif follower_count >= 100000:
            influence_tier = 'macro'
        elif follower_count >= 10000:
            influence_tier = 'mid'
        elif follower_count >= 1000:
            influence_tier = 'small'

        return {
            'follower_count': follower_count,
            'is_verified': author.get('verified', False),
            'influence_tier': influence_tier,
            # Log scale for modeling
            'follower_log': np.log10(max(1, follower_count)),
            'username_length': len(author.get('username', '')),
            'display_name_length': len(author.get('display_name', '')),
            'has_display_name': bool(author.get('display_name', '').strip()),
            'verified_bonus': 1.5 if author.get('verified', False) else 1.0
        }

    def _extract_engagement_features(self, post: Dict) -> Dict:
        """Extract features for engagement prediction"""
        engagement = post.get('engagement', {})
        author = post.get('author', {})

        likes = engagement.get('like_count', 0)
        replies = engagement.get('reply_count', 0)
        reposts = engagement.get('repost_count', 0)

        total_engagement = likes + replies + reposts
        follower_count = max(1, author.get('follower_count', 1))

        return {
            'engagement_total': total_engagement,
            'engagement_rate': total_engagement / follower_count,
            'reply_to_like_ratio': replies / max(1, likes),
            'repost_to_like_ratio': reposts / max(1, likes),
            'interaction_diversity': len([x for x in [likes, replies, reposts] if x > 0]),
            # Could be time-normalized in real scenario
            'engagement_velocity': total_engagement,
            'viral_coefficient': reposts / max(1, total_engagement)
        }


class BatchFeatureExtractor:
    """Extract features across a batch of posts"""

    def __init__(self):
        self.post_extractor = PostFeatureExtractor()

    def extract_batch_features(self, posts: List[Dict]) -> pd.DataFrame:
        """Extract features for all posts and return as DataFrame"""
        if not posts:
            return pd.DataFrame()

        features_list = []

        for post in posts:
            try:
                post_features = self.post_extractor.extract_all_features(post)
                post_features['post_id'] = post.get('id')
                features_list.append(post_features)
            except Exception as e:
                logger.warning(
                    f"Failed to extract features for post {post.get('id', 'unknown')}: {e}")
                continue

        if not features_list:
            return pd.DataFrame()

        df = pd.DataFrame(features_list)

        # Add batch-level features
        df = self._add_batch_features(df)

        return df

    def _add_batch_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features that depend on the entire batch"""
        if df.empty:
            return df

        # Relative engagement metrics
        if 'engagement_total' in df.columns:
            df['engagement_percentile'] = df['engagement_total'].rank(pct=True)
            df['is_top_engagement'] = df['engagement_percentile'] >= 0.9
            df['is_bottom_engagement'] = df['engagement_percentile'] <= 0.1

        # Relative follower metrics
        if 'follower_count' in df.columns:
            df['follower_percentile'] = df['follower_count'].rank(pct=True)
            df['is_top_influencer'] = df['follower_percentile'] >= 0.9

        # Content length relative to batch
        if 'char_count' in df.columns:
            df['length_percentile'] = df['char_count'].rank(pct=True)
            df['is_long_content'] = df['length_percentile'] >= 0.75
            df['is_short_content'] = df['length_percentile'] <= 0.25

        # Viral potential relative to batch
        if 'viral_potential_score' in df.columns:
            df['viral_percentile'] = df['viral_potential_score'].rank(pct=True)
            df['high_viral_potential'] = df['viral_percentile'] >= 0.8

        return df

    def get_feature_summary(self, df: pd.DataFrame) -> Dict:
        """Get summary statistics of extracted features"""
        if df.empty:
            return {}

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        summary = {
            'total_posts': len(df),
            'feature_count': len(df.columns),
            'numeric_features': len(numeric_cols),
            'feature_stats': {}
        }

        # Key feature statistics
        key_features = [
            'engagement_total', 'follower_count', 'viral_potential_score',
            'emotional_intensity', 'char_count', 'hashtag_count'
        ]

        for feature in key_features:
            if feature in df.columns:
                summary['feature_stats'][feature] = {
                    'mean': df[feature].mean(),
                    'std': df[feature].std(),
                    'min': df[feature].min(),
                    'max': df[feature].max(),
                    'median': df[feature].median()
                }

        return summary


# Utility functions for feature engineering
def create_engagement_tiers(engagement_score: float) -> str:
    """Categorize engagement into tiers"""
    if engagement_score >= 90:
        return 'viral'
    elif engagement_score >= 75:
        return 'high'
    elif engagement_score >= 50:
        return 'medium'
    elif engagement_score >= 25:
        return 'low'
    else:
        return 'minimal'


def calculate_influence_multiplier(follower_count: int, verified: bool) -> float:
    """Calculate influence multiplier based on follower count and verification"""
    base_multiplier = min(3.0, 1.0 + np.log10(max(1, follower_count)) / 10)
    verification_bonus = 0.5 if verified else 0.0
    return base_multiplier + verification_bonus


def extract_trending_topics(posts: List[Dict], min_frequency: int = 2) -> List[Tuple[str, int, float]]:
    """Extract trending topics with their frequency and average engagement"""
    topic_stats = defaultdict(lambda: {'count': 0, 'total_engagement': 0})

    for post in posts:
        engagement = post.get('scores', {}).get('engagement_score', 0)

        # Extract hashtags
        for tag in post.get('tags', []):
            topic_stats[f"#{tag}"]['count'] += 1
            topic_stats[f"#{tag}"]['total_engagement'] += engagement

        # Extract hashtags from content
        hashtags = re.findall(r'#\w+', post.get('content', ''))
        for hashtag in hashtags:
            if hashtag.lower() not in [f"#{tag}".lower() for tag in post.get('tags', [])]:
                topic_stats[hashtag.lower()]['count'] += 1
                topic_stats[hashtag.lower()]['total_engagement'] += engagement

    # Filter and calculate averages
    trending_topics = []
    for topic, stats in topic_stats.items():
        if stats['count'] >= min_frequency:
            avg_engagement = stats['total_engagement'] / stats['count']
            trending_topics.append((topic, stats['count'], avg_engagement))

    # Sort by engagement score
    trending_topics.sort(key=lambda x: x[2], reverse=True)

    return trending_topics


# Legacy functions for backward compatibility with existing code

def _safe_get(obj: Dict, key: str, default=None):
    """Legacy function for safe dict access"""
    return obj.get(key, default) if obj.get(key) is not None else default


def _safe_int(value, default: int = 0) -> int:
    """Legacy function for safe int conversion"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def compute_post_feature(post: Dict) -> Dict:
    """Legacy function - compute basic features for a single post"""
    extractor = PostFeatureExtractor()
    return extractor.extract_all_features(post)


def compute_dataset(posts: List[Dict]) -> Dict:
    """Legacy function - compute features for dataset"""
    batch_extractor = BatchFeatureExtractor()
    df = batch_extractor.extract_batch_features(posts)

    if df.empty:
        return {
            'post_features': [],
            'summary_statistics': {
                'total_posts': 0,
                'error': 'No posts to analyze'
            }
        }

    post_features = df.to_dict('records')
    summary = batch_extractor.get_feature_summary(df)

    return {
        'post_features': post_features,
        'summary_statistics': summary
    }


def _safe_get(obj: Dict, key: str, default: Any = None) -> Any:
    """
    Lấy giá trị từ dict một cách an toàn.
    Trả về default nếu key không tồn tại hoặc value là None.
    """
    return obj.get(key, default) if obj.get(key) is not None else default


def _safe_int(value: Any, default: int = 0) -> int:
    """Chuyển đổi giá trị sang int một cách an toàn."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Chuyển đổi giá trị sang float một cách an toàn."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO-8601 datetime string một cách an toàn.
    Trả về None nếu không parse được.
    """
    if not dt_string:
        return None

    try:
        # Xử lý các format datetime phổ biến
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # 2025-10-04T16:30:10.123Z
            "%Y-%m-%dT%H:%M:%SZ",     # 2025-10-04T16:30:10Z
            "%Y-%m-%dT%H:%M:%S",      # 2025-10-04T16:30:10
            "%Y-%m-%d %H:%M:%S"       # 2025-10-04 16:30:10
        ]:
            try:
                return datetime.strptime(dt_string.replace('+00:00', 'Z'), fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def compute_post_feature(post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính toán các chỉ số feature cho một bài post.

    Args:
        post: Dict chứa thông tin bài post

    Returns:
        Dict chứa các feature đã tính toán + thông tin tác giả
    """
    # Lấy thông tin cơ bản với xử lý dữ liệu thiếu
    author = _safe_get(post, 'author', {})
    content = _safe_get(post, 'content', '')
    created_at_str = _safe_get(post, 'created_at', '')
    tags = _safe_get(post, 'tags', [])

    # Thông tin tác giả
    display_name = _safe_get(author, 'display_name', 'Unknown')
    username = _safe_get(author, 'username', 'unknown')
    follower_count = _safe_int(
        _safe_get(author, 'follower_count'), 1)  # Min 1 để tránh chia 0
    verified = bool(_safe_get(author, 'verified', False))

    # Engagement metrics
    like_count = _safe_int(_safe_get(post, 'like_count'))
    reply_count = _safe_int(_safe_get(post, 'reply_count'))
    repost_count = _safe_int(_safe_get(post, 'repost_count'))

    # Tính các chỉ số engagement
    engagement_score_raw = like_count + reply_count + repost_count
    engagement_rate = engagement_score_raw / max(follower_count, 1)
    reply_ratio = reply_count / max(like_count, 1)
    repost_ratio = repost_count / max(like_count, 1)

    # Content features
    content_length = len(str(content)) if content else 0

    # Tag features
    hashtag_count = len(tags) if isinstance(tags, list) else 0
    has_trending_tag = 0

    # Kiểm tra trending tag
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict) and tag.get('trending', False):
                has_trending_tag = 1
                break

    # Time features
    post_hour = 0
    created_dt = _parse_datetime(created_at_str)
    if created_dt:
        post_hour = created_dt.hour

    # Tạo feature dict
    features = {
        # Author info
        'display_name': display_name,
        'username': username,
        'follower_count': follower_count,
        'verified': verified,

        # Basic engagement
        'like_count': like_count,
        'reply_count': reply_count,
        'repost_count': repost_count,

        # Computed features
        'engagement_score_raw': engagement_score_raw,
        'engagement_rate': round(engagement_rate, 6),
        'reply_ratio': round(reply_ratio, 4),
        'repost_ratio': round(repost_ratio, 4),
        'content_length': content_length,
        'hashtag_count': hashtag_count,
        'has_trending_tag': has_trending_tag,
        'post_hour': post_hour,

        # Original data
        'content': content,
        'created_at': created_at_str,
        'tags': tags,
        'embed': _safe_get(post, 'embed')
    }

    return features


def compute_dataset(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tính toán features cho toàn bộ dataset và tạo thống kê mô tả.

    Args:
        posts: List các bài post

    Returns:
        Dict chứa post_features và summary_statistics
    """
    if not posts:
        return {
            'post_features': [],
            'summary_statistics': {
                'total_posts': 0,
                'error': 'No posts to analyze'
            }
        }

    # Tính features cho từng post
    post_features = []
    engagement_rates = []

    for i, post in enumerate(posts):
        try:
            features = compute_post_feature(post)
            post_features.append(features)
            engagement_rates.append(features['engagement_rate'])
        except Exception as e:
            print(f"Warning: Failed to process post {i}: {e}")
            continue

    if not post_features:
        return {
            'post_features': [],
            'summary_statistics': {
                'total_posts': 0,
                'error': 'No posts could be processed'
            }
        }

    # Tính quantile 90% cho engagement_rate
    engagement_rates_sorted = sorted(engagement_rates)
    q90_index = int(len(engagement_rates_sorted) * 0.9)
    engagement_threshold = engagement_rates_sorted[q90_index] if engagement_rates_sorted else 0

    # Thêm cờ is_trending
    for feature in post_features:
        feature['is_trending'] = 1 if feature['engagement_rate'] >= engagement_threshold else 0

    # Tính thống kê mô tả
    total_posts = len(post_features)

    # Basic stats
    engagement_rates_valid = [f['engagement_rate'] for f in post_features]
    engagement_stats = {
        'mean': round(sum(engagement_rates_valid) / len(engagement_rates_valid), 6),
        'min': round(min(engagement_rates_valid), 6),
        'max': round(max(engagement_rates_valid), 6),
        'threshold_top10': round(engagement_threshold, 6)
    }

    # Top hashtags
    all_hashtags = []
    for feature in post_features:
        tags = feature.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get('name')
                    if tag_name:
                        all_hashtags.append(tag_name)
                elif isinstance(tag, str):
                    all_hashtags.append(tag)

    hashtag_counter = Counter(all_hashtags)
    top_hashtags = [item[0] for item in hashtag_counter.most_common(10)]

    # Trending tag ratio
    trending_tag_count = sum(
        1 for f in post_features if f['has_trending_tag'] == 1)
    trending_tag_ratio = round(trending_tag_count / total_posts, 4)

    # Verified ratio
    verified_count = sum(1 for f in post_features if f['verified'])
    verified_ratio = round(verified_count / total_posts, 4)

    # Engagement by hour
    hour_engagement = defaultdict(list)
    for feature in post_features:
        hour = feature['post_hour']
        hour_engagement[hour].append(feature['engagement_rate'])

    # Tính trung bình engagement theo giờ
    hourly_stats = {}
    for hour, rates in hour_engagement.items():
        hourly_stats[hour] = {
            'avg_engagement': round(sum(rates) / len(rates), 6),
            'post_count': len(rates)
        }

    # Content length stats
    content_lengths = [f['content_length'] for f in post_features]
    content_stats = {
        'mean': round(sum(content_lengths) / len(content_lengths), 2),
        'min': min(content_lengths),
        'max': max(content_lengths)
    }

    summary_statistics = {
        'total_posts': total_posts,
        'engagement_stats': engagement_stats,
        'top_hashtags': top_hashtags,
        'trending_tag_ratio': trending_tag_ratio,
        'verified_ratio': verified_ratio,
        'hourly_engagement': dict(sorted(hourly_stats.items())),
        'content_length_stats': content_stats,
        'analysis_timestamp': datetime.now().isoformat()
    }

    return {
        'post_features': post_features,
        'summary_statistics': summary_statistics
    }


def _generate_schema_report(post_features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tạo báo cáo schema cho dataset.

    Args:
        post_features: List các post features

    Returns:
        Dict chứa thông tin schema
    """
    if not post_features:
        return {'error': 'No data for schema analysis'}

    total_rows = len(post_features)
    schema_info = {}

    # Lấy tất cả các keys từ tất cả records
    all_keys = set()
    for feature in post_features:
        all_keys.update(feature.keys())

    # Phân tích từng column
    for key in sorted(all_keys):
        values = []
        null_count = 0

        for feature in post_features:
            value = feature.get(key)
            if value is None or value == '' or value == []:
                null_count += 1
            else:
                values.append(value)

        # Xác định data type
        if not values:
            dtype = 'null'
        else:
            sample_value = values[0]
            if isinstance(sample_value, bool):
                dtype = 'boolean'
            elif isinstance(sample_value, int):
                dtype = 'integer'
            elif isinstance(sample_value, float):
                dtype = 'float'
            elif isinstance(sample_value, str):
                dtype = 'string'
            elif isinstance(sample_value, list):
                dtype = 'array'
            elif isinstance(sample_value, dict):
                dtype = 'object'
            else:
                dtype = 'unknown'

        # Tính null ratio
        null_ratio = round(null_count / total_rows, 4)

        schema_info[key] = {
            'dtype': dtype,
            'null_count': null_count,
            'null_ratio': null_ratio,
            'non_null_count': total_rows - null_count
        }

    return {
        'total_rows': total_rows,
        'total_columns': len(all_keys),
        'columns': schema_info,
        'generated_at': datetime.now().isoformat()
    }


def save_json(obj: Any, path: str) -> bool:
    """
    Ghi dữ liệu ra file JSON với UTF-8 encoding.

    Args:
        obj: Object cần ghi
        path: Đường dẫn file

    Returns:
        bool: True nếu thành công, False nếu lỗi
    """
    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved: {path}")
        return True

    except Exception as e:
        print(f"❌ Failed to save {path}: {e}")
        return False


def analyze_posts_to_json(
    posts: List[Dict[str, Any]],
    features_path: str = "post_features.json",
    summary_path: str = "summary_statistics.json",
    schema_path: str = "schema_report.json"
) -> Dict[str, Any]:
    """
    Pipeline hoàn chỉnh: phân tích posts và ghi ra 3 file JSON.

    Args:
        posts: List các bài post cần phân tích
        features_path: Đường dẫn file post features
        summary_path: Đường dẫn file summary statistics  
        schema_path: Đường dẫn file schema report

    Returns:
        Dict tóm tắt kết quả phân tích
    """
    print("🚀 Starting social media post analysis...")

    # Bước 1: Tính toán features và thống kê
    print("📊 Computing features and statistics...")
    result = compute_dataset(posts)

    post_features = result['post_features']
    summary_statistics = result['summary_statistics']

    if not post_features:
        return {
            'error': 'No posts could be processed',
            'rows': 0,
            'files': {}
        }

    # Bước 2: Tạo schema report
    print("📋 Generating schema report...")
    schema_report = _generate_schema_report(post_features)

    # Bước 3: Ghi files
    print("💾 Saving analysis results...")
    files_saved = {}

    # Ghi post features
    if save_json(post_features, features_path):
        files_saved['post_features'] = features_path

    # Ghi summary statistics
    if save_json(summary_statistics, summary_path):
        files_saved['summary_statistics'] = summary_path

    # Ghi schema report
    if save_json(schema_report, schema_path):
        files_saved['schema_report'] = schema_path

    # Tạo kết quả tóm tắt
    avg_engagement_rate = summary_statistics.get(
        'engagement_stats', {}).get('mean', 0)
    top_hashtags = summary_statistics.get('top_hashtags', [])

    result_summary = {
        'rows': len(post_features),
        'avg_engagement_rate': avg_engagement_rate,
        'top_hashtags': top_hashtags[:5],  # Top 5 hashtags
        'files': files_saved,
        'analysis_completed_at': datetime.now().isoformat()
    }

    print(f"✅ Analysis completed!")
    print(f"   - Processed: {len(post_features)} posts")
    print(f"   - Avg engagement rate: {avg_engagement_rate:.6f}")
    print(f"   - Top hashtags: {', '.join(top_hashtags[:3])}")
    print(f"   - Files saved: {len(files_saved)}")

    return result_summary


if __name__ == "__main__":
    """
    Test script - đọc posts.json và chạy thử phân tích.
    """
    print("🧪 Running feature extraction test...")

    # Thử đọc file posts.json
    test_file = "posts.json"

    if os.path.exists(test_file):
        try:
            print(f"📖 Loading {test_file}...")
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Xử lý cấu trúc dữ liệu
            if isinstance(data, dict) and 'data' in data:
                posts = data['data']
            elif isinstance(data, list):
                posts = data
            else:
                posts = [data]

            print(f"📊 Found {len(posts)} posts to analyze")

            # Chạy phân tích
            result = analyze_posts_to_json(
                posts,
                features_path="output/post_features.json",
                summary_path="output/summary_statistics.json",
                schema_path="output/schema_report.json"
            )

            print("\n📋 Analysis Summary:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"❌ Error processing {test_file}: {e}")

    else:
        print(f"⚠️  {test_file} not found. Creating sample data for testing...")

        # Tạo dữ liệu mẫu để test
        sample_posts = [
            {
                "author": {
                    "display_name": "John Doe",
                    "username": "johndoe",
                    "follower_count": 1500,
                    "verified": True
                },
                "content": "This is a sample post about #technology #ai",
                "created_at": "2025-10-04T14:30:00Z",
                "like_count": 25,
                "reply_count": 5,
                "repost_count": 3,
                "tags": [
                    {"name": "technology", "trending": True},
                    {"name": "ai", "trending": False}
                ],
                "embed": None
            },
            {
                "author": {
                    "display_name": "Jane Smith",
                    "username": "janesmith",
                    "follower_count": 2500,
                    "verified": False
                },
                "content": "Another test post with different metrics",
                "created_at": "2025-10-04T16:45:00Z",
                "like_count": 100,
                "reply_count": 15,
                "repost_count": 8,
                "tags": [],
                "embed": "sample_embed_data"
            }
        ]

        print("🧪 Testing with sample data...")
        result = analyze_posts_to_json(
            sample_posts,
            features_path="test_output/post_features.json",
            summary_path="test_output/summary_statistics.json",
            schema_path="test_output/schema_report.json"
        )

        print("\n📋 Test Results:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
