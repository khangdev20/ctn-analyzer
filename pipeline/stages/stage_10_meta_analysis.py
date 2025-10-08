# 🟪 Stage 10: Meta Analysis — Weekly Strategic Insights

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import statistics
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class MetaAnalysisStage:
    """
    Task: Generate weekly strategic insights and content calendar recommendations
    - Input: 7 days of processed intelligence data
    - Output: weekly report with strategic insights and content calendar
    - Steps:
      1. Aggregate week's trending data
      2. Identify patterns across multiple days
      3. Generate strategic insights and recommendations
      4. Create content calendar suggestions
    - Return: comprehensive weekly analysis with actionable recommendations
    """

    def __init__(self, config):
        self.config = config
        self.analysis_window_days = 7  # Look back 7 days for analysis

    async def execute(self, batch_id: str, learning_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute meta analysis stage"""
        logger.info("[ANALYTICS] Stage 10: Generating weekly strategic insights and content calendar...")
        
        try:
            # Collect weekly data from multiple pipeline stages
            weekly_data = await self._collect_weekly_data(batch_id)
            
            if not weekly_data:
                logger.warning("[ANALYTICS] No weekly data found - generating baseline analysis")
                return await self._create_baseline_analysis(batch_id)
            
            # Generate comprehensive weekly analysis
            trend_patterns = await self._analyze_trend_patterns(weekly_data)
            content_insights = await self._analyze_content_patterns(weekly_data)
            strategic_recommendations = await self._generate_strategic_recommendations(trend_patterns, content_insights)
            content_calendar = await self._create_content_calendar(strategic_recommendations, weekly_data)
            competitive_analysis = await self._analyze_competitive_landscape(weekly_data)
            performance_metrics = await self._calculate_weekly_performance(weekly_data)
            
            # Create comprehensive meta analysis
            meta_analysis = {
                "batch_id": batch_id,
                "analysis_period": {
                    "start_date": (datetime.now(timezone.utc) - timedelta(days=self.analysis_window_days)).isoformat(),
                    "end_date": datetime.now(timezone.utc).isoformat(),
                    "total_days": self.analysis_window_days
                },
                "trend_patterns": trend_patterns,
                "content_insights": content_insights,
                "strategic_recommendations": strategic_recommendations,
                "content_calendar": content_calendar,
                "competitive_analysis": competitive_analysis,
                "performance_metrics": performance_metrics,
                "metadata": {
                    "total_posts_analyzed": len(weekly_data.get("all_posts", [])),
                    "trending_posts_count": len(weekly_data.get("trending_posts", [])),
                    "analysis_version": "meta_1.0",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Save meta analysis
            output_path = await self._save_meta_analysis(meta_analysis, batch_id)
            
            # Generate executive summary
            summary = self._generate_summary(meta_analysis, batch_id)
            
            logger.info(f"[OK] Stage 10 completed: Weekly meta analysis generated")
            logger.info(f"[TRENDING_UP] Analyzed {len(weekly_data.get('all_posts', []))} posts across {self.analysis_window_days} days")
            
            return {
                **summary,
                "meta_analysis": meta_analysis,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"[ERROR] Stage 10 error: {e}")
            return None

    async def _collect_weekly_data(self, current_batch_id: str) -> Dict:
        """Collect data from the past week across all pipeline stages"""
        weekly_data = {
            "all_posts": [],
            "trending_posts": [],
            "daily_summaries": [],
            "pattern_data": [],
            "prediction_data": []
        }
        
        try:
            now = datetime.now(timezone.utc)
            
            for days_back in range(self.analysis_window_days):
                search_date = now - timedelta(days=days_back)
                date_str = f"{search_date.year:04d}/{search_date.month:02d}/{search_date.day:02d}"
                
                # Collect from different pipeline stages
                await self._collect_from_stage(weekly_data, "clean", date_str)
                await self._collect_from_stage(weekly_data, "score", date_str)
                await self._collect_from_stage(weekly_data, "rubric", date_str)
                await self._collect_from_stage(weekly_data, "network", date_str)
                await self._collect_from_stage(weekly_data, "predict", date_str)
                await self._collect_from_stage(weekly_data, "report", date_str)
            
            # Deduplicate posts by URL
            seen_urls = set()
            unique_posts = []
            for post in weekly_data["all_posts"]:
                url = post.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_posts.append(post)
            
            weekly_data["all_posts"] = unique_posts
            
            # Identify trending posts (high scores and predictions)
            trending_posts = [
                post for post in unique_posts
                if post.get("final_score", 0) >= 70 or post.get("trending_probability", 0) >= 0.7
            ]
            weekly_data["trending_posts"] = trending_posts
            
            logger.info(f"[ANALYTICS] Collected {len(unique_posts)} unique posts ({len(trending_posts)} trending)")
            return weekly_data
            
        except Exception as e:
            logger.error(f"Failed to collect weekly data: {e}")
            return {}

    async def _collect_from_stage(self, weekly_data: Dict, stage: str, date_str: str):
        """Collect data from a specific pipeline stage"""
        stage_dir = f"data/{stage}/{date_str}"
        
        if not os.path.exists(stage_dir):
            return
        
        try:
            stage_files = [f for f in os.listdir(stage_dir) if f.endswith(f'.{stage}.json')]
            
            for file in stage_files:
                file_path = os.path.join(stage_dir, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    posts = data.get("posts", [])
                    for post in posts:
                        post["stage"] = stage
                        post["analysis_date"] = date_str
                        weekly_data["all_posts"].append(post)
                    
                    # Collect stage-specific summaries
                    if "summary" in data:
                        weekly_data["daily_summaries"].append({
                            "date": date_str,
                            "stage": stage,
                            "summary": data["summary"]
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to scan {stage_dir}: {e}")

    async def _analyze_trend_patterns(self, weekly_data: Dict) -> Dict:
        """Analyze trending patterns across the week"""
        all_posts = weekly_data.get("all_posts", [])
        trending_posts = weekly_data.get("trending_posts", [])
        
        # Time-based patterns
        hourly_distribution = self._analyze_hourly_patterns(all_posts)
        daily_trends = self._analyze_daily_trends(all_posts)
        
        # Content type patterns
        content_type_performance = self._analyze_content_types(trending_posts)
        
        # Topic clustering
        topic_trends = self._analyze_topic_trends(trending_posts)
        
        # Engagement velocity patterns
        velocity_patterns = self._analyze_velocity_patterns(trending_posts)
        
        return {
            "temporal_patterns": {
                "peak_hours": hourly_distribution,
                "daily_trends": daily_trends,
                "optimal_posting_windows": self._identify_optimal_windows(hourly_distribution)
            },
            "content_patterns": {
                "high_performing_types": content_type_performance,
                "trending_topics": topic_trends,
                "length_optimization": self._analyze_content_length(trending_posts)
            },
            "engagement_patterns": {
                "velocity_insights": velocity_patterns,
                "viral_characteristics": self._identify_viral_characteristics(trending_posts)
            }
        }

    def _analyze_hourly_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze when posts perform best by hour"""
        hourly_performance = defaultdict(list)
        
        for post in posts:
            created_at = post.get("created_at")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hour = dt.hour
                    score = post.get("final_score", 0)
                    hourly_performance[hour].append(score)
                except:
                    continue
        
        # Calculate average performance by hour
        hourly_averages = {}
        for hour, scores in hourly_performance.items():
            if scores:
                hourly_averages[hour] = {
                    "average_score": statistics.mean(scores),
                    "post_count": len(scores),
                    "max_score": max(scores)
                }
        
        # Find peak performance hours
        sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1]["average_score"], reverse=True)
        
        return {
            "hourly_averages": hourly_averages,
            "peak_hours": [hour for hour, data in sorted_hours[:3]],
            "performance_ranking": sorted_hours
        }

    def _analyze_daily_trends(self, posts: List[Dict]) -> Dict:
        """Analyze performance trends across days of the week"""
        daily_performance = defaultdict(list)
        
        for post in posts:
            created_at = post.get("created_at")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    day_name = dt.strftime('%A')
                    score = post.get("final_score", 0)
                    daily_performance[day_name].append(score)
                except:
                    continue
        
        daily_averages = {}
        for day, scores in daily_performance.items():
            if scores:
                daily_averages[day] = {
                    "average_score": statistics.mean(scores),
                    "post_count": len(scores),
                    "trending_rate": len([s for s in scores if s >= 70]) / len(scores)
                }
        
        return daily_averages

    def _analyze_content_types(self, trending_posts: List[Dict]) -> Dict:
        """Analyze which content types perform best"""
        type_performance = defaultdict(list)
        
        for post in trending_posts:
            # Determine content type based on characteristics
            content_type = self._classify_content_type(post)
            score = post.get("final_score", 0)
            type_performance[content_type].append(score)
        
        type_averages = {}
        for content_type, scores in type_performance.items():
            if scores:
                type_averages[content_type] = {
                    "average_score": statistics.mean(scores),
                    "count": len(scores),
                    "success_rate": len([s for s in scores if s >= 70]) / len(scores)
                }
        
        return type_averages

    def _classify_content_type(self, post: Dict) -> str:
        """Classify post content type"""
        text = (post.get("text", "") or "").lower()
        
        if any(word in text for word in ["how to", "tutorial", "guide", "step"]):
            return "Educational"
        elif any(word in text for word in ["breaking", "news", "update", "announced"]):
            return "News"
        elif any(word in text for word in ["opinion", "think", "believe", "should"]):
            return "Opinion"
        elif any(word in text for word in ["funny", "lol", "😂", "joke"]):
            return "Humor"
        elif post.get("tag_count", 0) > 3:
            return "Promotional"
        else:
            return "General"

    def _analyze_topic_trends(self, trending_posts: List[Dict]) -> Dict:
        """Analyze trending topics and hashtags"""
        all_tags = []
        topic_performance = defaultdict(list)
        
        for post in trending_posts:
            tags = post.get("tags", [])
            score = post.get("final_score", 0)
            
            for tag in tags:
                all_tags.append(tag.lower())
                topic_performance[tag.lower()].append(score)
        
        # Most common tags
        tag_counts = Counter(all_tags)
        
        # Best performing tags
        tag_performance = {}
        for tag, scores in topic_performance.items():
            if len(scores) >= 2:  # Minimum 2 posts to be considered
                tag_performance[tag] = {
                    "average_score": statistics.mean(scores),
                    "frequency": len(scores),
                    "total_mentions": tag_counts[tag]
                }
        
        return {
            "trending_hashtags": dict(tag_counts.most_common(10)),
            "high_performance_tags": dict(sorted(tag_performance.items(), 
                                                key=lambda x: x[1]["average_score"], reverse=True)[:10])
        }

    def _analyze_velocity_patterns(self, trending_posts: List[Dict]) -> Dict:
        """Analyze engagement velocity patterns"""
        velocities = [post.get("velocity_per_min", 0) for post in trending_posts if post.get("velocity_per_min")]
        
        if not velocities:
            return {"note": "No velocity data available"}
        
        return {
            "average_velocity": statistics.mean(velocities),
            "median_velocity": statistics.median(velocities),
            "velocity_range": {
                "min": min(velocities),
                "max": max(velocities)
            },
            "high_velocity_threshold": statistics.quantile(velocities, 0.8) if len(velocities) >= 5 else max(velocities)
        }

    def _identify_optimal_windows(self, hourly_distribution: Dict) -> List[Dict]:
        """Identify optimal posting time windows"""
        peak_hours = hourly_distribution.get("peak_hours", [])
        
        windows = []
        if peak_hours:
            for hour in peak_hours:
                windows.append({
                    "start_hour": hour,
                    "end_hour": (hour + 2) % 24,
                    "description": f"{hour:02d}:00 - {(hour + 2) % 24:02d}:00",
                    "performance_level": "High"
                })
        
        return windows

    async def _analyze_content_patterns(self, weekly_data: Dict) -> Dict:
        """Analyze content patterns and preferences"""
        trending_posts = weekly_data.get("trending_posts", [])
        
        # Content length analysis
        length_analysis = self._analyze_content_length(trending_posts)
        
        # Sentiment patterns
        sentiment_patterns = self._analyze_sentiment_patterns(trending_posts)
        
        # Linguistic features
        linguistic_features = self._analyze_linguistic_features(trending_posts)
        
        return {
            "content_optimization": {
                "optimal_length": length_analysis,
                "sentiment_preferences": sentiment_patterns,
                "effective_language": linguistic_features
            },
            "format_insights": self._analyze_content_formats(trending_posts),
            "engagement_drivers": self._identify_engagement_drivers(trending_posts)
        }

    def _analyze_content_length(self, posts: List[Dict]) -> Dict:
        """Analyze optimal content length"""
        length_performance = []
        
        for post in posts:
            content_length = post.get("content_length", 0)
            score = post.get("final_score", 0)
            if content_length > 0:
                length_performance.append((content_length, score))
        
        if not length_performance:
            return {"note": "No content length data available"}
        
        # Group by length ranges
        length_ranges = {
            "Short (1-50)": [],
            "Medium (51-150)": [],
            "Long (151-300)": [],
            "Very Long (300+)": []
        }
        
        for length, score in length_performance:
            if length <= 50:
                length_ranges["Short (1-50)"].append(score)
            elif length <= 150:
                length_ranges["Medium (51-150)"].append(score)
            elif length <= 300:
                length_ranges["Long (151-300)"].append(score)
            else:
                length_ranges["Very Long (300+)"].append(score)
        
        # Calculate averages
        range_performance = {}
        for range_name, scores in length_ranges.items():
            if scores:
                range_performance[range_name] = {
                    "average_score": statistics.mean(scores),
                    "count": len(scores),
                    "success_rate": len([s for s in scores if s >= 70]) / len(scores)
                }
        
        # Find optimal range
        best_range = max(range_performance.items(), key=lambda x: x[1]["average_score"]) if range_performance else None
        
        return {
            "range_performance": range_performance,
            "optimal_range": best_range[0] if best_range else "Medium (51-150)",
            "recommendation": f"Content performs best in {best_range[0]} character range" if best_range else "Aim for medium length content"
        }

    def _analyze_sentiment_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze sentiment patterns in trending content"""
        # Simple sentiment analysis based on keywords
        positive_words = ["great", "amazing", "love", "best", "awesome", "excellent", "fantastic"]
        negative_words = ["bad", "hate", "worst", "terrible", "awful", "horrible"]
        question_words = ["what", "how", "why", "when", "where", "which"]
        
        sentiment_performance = {"positive": [], "negative": [], "neutral": [], "question": []}
        
        for post in posts:
            text = (post.get("text", "") or "").lower()
            score = post.get("final_score", 0)
            
            if any(word in text for word in question_words):
                sentiment_performance["question"].append(score)
            elif any(word in text for word in positive_words):
                sentiment_performance["positive"].append(score)
            elif any(word in text for word in negative_words):
                sentiment_performance["negative"].append(score)
            else:
                sentiment_performance["neutral"].append(score)
        
        # Calculate averages
        sentiment_averages = {}
        for sentiment, scores in sentiment_performance.items():
            if scores:
                sentiment_averages[sentiment] = {
                    "average_score": statistics.mean(scores),
                    "count": len(scores)
                }
        
        return sentiment_averages

    def _analyze_linguistic_features(self, posts: List[Dict]) -> Dict:
        """Analyze effective linguistic features"""
        feature_performance = {
            "uses_numbers": [],
            "uses_caps": [],
            "uses_emojis": [],
            "asks_questions": []
        }
        
        for post in posts:
            text = post.get("text", "") or ""
            score = post.get("final_score", 0)
            
            if any(char.isdigit() for char in text):
                feature_performance["uses_numbers"].append(score)
            
            if any(char.isupper() for char in text):
                feature_performance["uses_caps"].append(score)
            
            if any(ord(char) > 127 for char in text):  # Simple emoji detection
                feature_performance["uses_emojis"].append(score)
            
            if "?" in text:
                feature_performance["asks_questions"].append(score)
        
        # Calculate feature effectiveness
        feature_effectiveness = {}
        for feature, scores in feature_performance.items():
            if scores:
                feature_effectiveness[feature] = {
                    "average_score": statistics.mean(scores),
                    "usage_count": len(scores)
                }
        
        return feature_effectiveness

    async def _generate_strategic_recommendations(self, trend_patterns: Dict, content_insights: Dict) -> List[Dict]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        # Timing recommendations
        optimal_windows = trend_patterns.get("temporal_patterns", {}).get("optimal_posting_windows", [])
        if optimal_windows:
            recommendations.append({
                "category": "Timing Strategy",
                "priority": "High",
                "recommendation": f"Post during peak engagement windows: {', '.join([w['description'] for w in optimal_windows[:2]])}",
                "rationale": "Analysis shows significantly higher engagement during these time periods",
                "implementation": "Schedule content releases during identified peak windows"
            })
        
        # Content type recommendations
        content_types = trend_patterns.get("content_patterns", {}).get("high_performing_types", {})
        if content_types:
            best_type = max(content_types.items(), key=lambda x: x[1]["average_score"]) if content_types else None
            if best_type:
                recommendations.append({
                    "category": "Content Strategy",
                    "priority": "High",
                    "recommendation": f"Focus on {best_type[0]} content - shows {best_type[1]['success_rate']:.1%} success rate",
                    "rationale": f"Average score of {best_type[1]['average_score']:.1f} outperforms other content types",
                    "implementation": f"Increase {best_type[0]} content production by 30%"
                })
        
        # Topic recommendations
        trending_topics = trend_patterns.get("content_patterns", {}).get("trending_topics", {})
        top_hashtags = trending_topics.get("trending_hashtags", {})
        if top_hashtags:
            top_tags = list(top_hashtags.keys())[:3]
            recommendations.append({
                "category": "Topic Strategy",
                "priority": "Medium",
                "recommendation": f"Leverage trending hashtags: {', '.join([f'#{tag}' for tag in top_tags])}",
                "rationale": "These hashtags show consistent high engagement across the analysis period",
                "implementation": "Incorporate these tags into upcoming content strategy"
            })
        
        # Content length recommendations
        optimal_length = content_insights.get("content_optimization", {}).get("optimal_length", {})
        if optimal_length.get("optimal_range"):
            recommendations.append({
                "category": "Content Optimization",
                "priority": "Medium",
                "recommendation": f"Optimize content length to {optimal_length['optimal_range']} characters",
                "rationale": optimal_length.get("recommendation", "Analysis shows this range performs best"),
                "implementation": "Review and adjust content length targets for upcoming posts"
            })
        
        # Engagement velocity recommendations
        velocity_insights = trend_patterns.get("engagement_patterns", {}).get("velocity_insights", {})
        if velocity_insights.get("high_velocity_threshold"):
            threshold = velocity_insights["high_velocity_threshold"]
            recommendations.append({
                "category": "Engagement Strategy",
                "priority": "Medium",
                "recommendation": f"Target content that can achieve {threshold:.1f}+ engagement per minute",
                "rationale": "High velocity content shows significantly better trending potential",
                "implementation": "Focus on timely, reactive content and immediate engagement tactics"
            })
        
        return recommendations

    async def _create_content_calendar(self, recommendations: List[Dict], weekly_data: Dict) -> Dict:
        """Create content calendar based on strategic insights"""
        
        # Get optimal posting windows
        calendar_suggestions = []
        
        # Daily content suggestions for the next week
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days_of_week:
            day_suggestions = {
                "day": day,
                "recommended_posts": [],
                "optimal_times": [],
                "content_themes": []
            }
            
            # Add 2-3 content suggestions per day
            day_suggestions["recommended_posts"] = [
                {
                    "time": "09:00",
                    "content_type": "Educational",
                    "theme": "Industry insights or how-to content",
                    "priority": "High"
                },
                {
                    "time": "15:00", 
                    "content_type": "Engagement",
                    "theme": "Question or discussion starter",
                    "priority": "Medium"
                },
                {
                    "time": "19:00",
                    "content_type": "Community",
                    "theme": "Behind-the-scenes or personal insight",
                    "priority": "Low"
                }
            ]
            
            calendar_suggestions.append(day_suggestions)
        
        # Weekly themes based on trending topics
        trending_topics = weekly_data.get("trending_posts", [])
        weekly_themes = self._extract_weekly_themes(trending_topics)
        
        return {
            "next_week_calendar": calendar_suggestions,
            "weekly_themes": weekly_themes,
            "content_quotas": {
                "educational_posts": 3,
                "engagement_posts": 2,
                "promotional_posts": 1,
                "community_posts": 1
            },
            "strategic_focus": [rec["recommendation"] for rec in recommendations if rec["priority"] == "High"]
        }

    def _extract_weekly_themes(self, trending_posts: List[Dict]) -> List[str]:
        """Extract themes for upcoming week based on trending content"""
        all_tags = []
        for post in trending_posts:
            all_tags.extend(post.get("tags", []))
        
        tag_counts = Counter(all_tags)
        top_themes = [tag for tag, count in tag_counts.most_common(5)]
        
        return top_themes

    async def _analyze_competitive_landscape(self, weekly_data: Dict) -> Dict:
        """Analyze competitive landscape insights"""
        all_posts = weekly_data.get("all_posts", [])
        
        # Author performance analysis
        author_performance = defaultdict(list)
        for post in all_posts:
            author = post.get("author_username", "unknown")
            score = post.get("final_score", 0)
            author_performance[author].append(score)
        
        # Top performers
        top_authors = {}
        for author, scores in author_performance.items():
            if len(scores) >= 2:  # At least 2 posts
                top_authors[author] = {
                    "average_score": statistics.mean(scores),
                    "post_count": len(scores),
                    "consistency": statistics.stdev(scores) if len(scores) > 1 else 0,
                    "peak_score": max(scores)
                }
        
        # Sort by performance
        sorted_authors = sorted(top_authors.items(), key=lambda x: x[1]["average_score"], reverse=True)
        
        return {
            "top_performers": dict(sorted_authors[:10]),
            "performance_benchmarks": {
                "average_top_score": statistics.mean([data["average_score"] for _, data in sorted_authors[:5]]) if sorted_authors else 0,
                "consistency_leaders": sorted(top_authors.items(), key=lambda x: x[1]["consistency"])[:5],
                "volume_leaders": sorted(top_authors.items(), key=lambda x: x[1]["post_count"], reverse=True)[:5]
            }
        }

    async def _calculate_weekly_performance(self, weekly_data: Dict) -> Dict:
        """Calculate overall weekly performance metrics"""
        all_posts = weekly_data.get("all_posts", [])
        trending_posts = weekly_data.get("trending_posts", [])
        
        if not all_posts:
            return {"note": "No posts to analyze"}
        
        # Overall metrics
        total_posts = len(all_posts)
        trending_count = len(trending_posts)
        trending_rate = trending_count / total_posts if total_posts > 0 else 0
        
        # Score distribution
        all_scores = [post.get("final_score", 0) for post in all_posts]
        
        # Engagement metrics
        total_engagement = sum(post.get("total_engagement", 0) for post in all_posts)
        avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
        
        # Velocity metrics
        velocities = [post.get("velocity_per_min", 0) for post in all_posts if post.get("velocity_per_min")]
        avg_velocity = statistics.mean(velocities) if velocities else 0
        
        return {
            "overview": {
                "total_posts_analyzed": total_posts,
                "trending_posts": trending_count,
                "trending_rate": trending_rate,
                "analysis_period_days": self.analysis_window_days
            },
            "content_performance": {
                "average_score": statistics.mean(all_scores) if all_scores else 0,
                "median_score": statistics.median(all_scores) if all_scores else 0,
                "score_distribution": {
                    "excellent_85+": len([s for s in all_scores if s >= 85]),
                    "good_70_84": len([s for s in all_scores if 70 <= s < 85]),
                    "average_50_69": len([s for s in all_scores if 50 <= s < 70]),
                    "below_average_50": len([s for s in all_scores if s < 50])
                }
            },
            "engagement_metrics": {
                "total_engagement": total_engagement,
                "average_engagement_per_post": avg_engagement,
                "average_velocity_per_minute": avg_velocity
            },
            "weekly_trends": {
                "improvement_areas": self._identify_improvement_areas(all_posts),
                "success_patterns": self._identify_success_patterns(trending_posts)
            }
        }

    def _identify_improvement_areas(self, posts: List[Dict]) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        low_score_posts = [p for p in posts if p.get("final_score", 0) < 50]
        if len(low_score_posts) > len(posts) * 0.3:  # More than 30% low scoring
            improvements.append("Content quality - 30%+ of posts scoring below 50")
        
        low_engagement_posts = [p for p in posts if p.get("total_engagement", 0) < 10]
        if len(low_engagement_posts) > len(posts) * 0.4:  # More than 40% low engagement
            improvements.append("Engagement rates - 40%+ of posts with minimal engagement")
        
        return improvements

    def _identify_success_patterns(self, trending_posts: List[Dict]) -> List[str]:
        """Identify patterns in successful content"""
        patterns = []
        
        if not trending_posts:
            return ["No trending posts found in analysis period"]
        
        # Common characteristics of trending posts
        avg_length = statistics.mean([p.get("content_length", 0) for p in trending_posts if p.get("content_length")])
        if avg_length:
            patterns.append(f"Successful content averages {avg_length:.0f} characters")
        
        common_tags = Counter()
        for post in trending_posts:
            common_tags.update(post.get("tags", []))
        
        if common_tags:
            top_tag = common_tags.most_common(1)[0]
            patterns.append(f"Most successful hashtag: #{top_tag[0]} (used in {top_tag[1]} trending posts)")
        
        return patterns

    async def _create_baseline_analysis(self, batch_id: str) -> Dict:
        """Create baseline analysis when no weekly data is available"""
        
        baseline_analysis = {
            "batch_id": batch_id,
            "analysis_period": {
                "start_date": (datetime.now(timezone.utc) - timedelta(days=self.analysis_window_days)).isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat(),
                "total_days": self.analysis_window_days
            },
            "status": "baseline_analysis",
            "strategic_recommendations": [
                {
                    "category": "Data Collection",
                    "priority": "High",
                    "recommendation": "Continue collecting data for meaningful weekly analysis",
                    "rationale": "Insufficient historical data for pattern analysis",
                    "implementation": "Run system consistently for 7+ days to enable meta analysis"
                }
            ],
            "content_calendar": {
                "note": "Content calendar will be available after sufficient data collection",
                "recommended_schedule": "2-3 posts per day during peak hours (9-11 AM, 2-4 PM, 7-9 PM)"
            },
            "metadata": {
                "total_posts_analyzed": 0,
                "trending_posts_count": 0,
                "analysis_version": "baseline_1.0",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Save baseline analysis
        output_path = await self._save_meta_analysis(baseline_analysis, batch_id)
        
        return {
            "batch_id": batch_id,
            "weekly_insights": ["Baseline analysis - collecting data for future insights"],
            "content_calendar": baseline_analysis["content_calendar"],
            "strategic_focus": ["Data collection and system consistency"],
            "performance_summary": "Baseline period - no performance data available",
            "meta_analysis": baseline_analysis,
            "output_path": output_path
        }

    async def _save_meta_analysis(self, analysis: Dict, batch_id: str) -> str:
        """Save meta analysis to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/meta/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = f"{dir_path}/meta_analysis_{batch_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return filepath

    def _generate_summary(self, meta_analysis: Dict, batch_id: str) -> Dict:
        """Generate summary as specified in AI Agent Prompts"""
        
        strategic_recommendations = meta_analysis.get("strategic_recommendations", [])
        performance_metrics = meta_analysis.get("performance_metrics", {})
        
        # Extract key insights
        weekly_insights = []
        for rec in strategic_recommendations:
            if rec.get("priority") == "High":
                weekly_insights.append(rec.get("recommendation", ""))
        
        # Performance summary
        overview = performance_metrics.get("overview", {})
        performance_summary = f"Analyzed {overview.get('total_posts_analyzed', 0)} posts with {overview.get('trending_rate', 0):.1%} trending rate"
        
        return {
            "batch_id": batch_id,
            "weekly_insights": weekly_insights[:5],  # Top 5 insights
            "content_calendar": meta_analysis.get("content_calendar", {}),
            "strategic_focus": [rec["category"] for rec in strategic_recommendations if rec.get("priority") == "High"],
            "performance_summary": performance_summary,
            "competitive_insights": meta_analysis.get("competitive_analysis", {}).get("performance_benchmarks", {}),
            "trend_forecast": {
                "emerging_topics": meta_analysis.get("trend_patterns", {}).get("content_patterns", {}).get("trending_topics", {}),
                "optimal_timing": meta_analysis.get("trend_patterns", {}).get("temporal_patterns", {}).get("optimal_posting_windows", [])
            }
        }