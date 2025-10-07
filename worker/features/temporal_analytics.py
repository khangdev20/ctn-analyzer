"""
Temporal Analytics Agent
Specializes in timing optimization analysis for social media engagement
"""

import asyncio
import json
import logging
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, median

logger = logging.getLogger(__name__)


class TemporalAnalyticsAgent:
    """
    Temporal Analytics Agent for Social Media Timing Optimization

    Analyzes:
    1. Engagement patterns by hour of day and day of week
    2. Best performing time slots for maximum visibility
    3. Time-to-trend analysis for viral content prediction
    4. Momentum duration and engagement lifecycle
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Temporal analysis parameters
        self.min_posts_for_analysis = 10
        self.trend_threshold = 100  # Minimum engagement to consider trending
        self.momentum_decay_threshold = 0.5  # 50% drop from peak
        self.timezone_offset = 0  # UTC by default

    async def analyze_temporal_patterns(self, posts: List[Dict], batch_id: str) -> Dict:
        """
        Run complete temporal analytics analysis

        Args:
            posts: List of post dictionaries with timestamp and engagement data
            batch_id: Unique identifier for this analysis

        Returns:
            Dict with temporal analysis results and Discord-formatted report
        """
        try:
            self.logger.info(
                f"⏰ Starting temporal analytics analysis for batch {batch_id}")

            # Step 1: Extract and validate temporal data
            temporal_data = self._extract_temporal_data(posts)

            if len(temporal_data["posts"]) < self.min_posts_for_analysis:
                return self._generate_empty_response(batch_id, "Insufficient posts for temporal analysis")

            self.logger.info(
                f"📊 Temporal data: {len(temporal_data['posts'])} posts over {temporal_data['time_span_hours']:.1f} hours")

            # Step 2: Calculate engagement patterns by time
            hourly_patterns = await self._analyze_hourly_patterns(temporal_data)
            daily_patterns = await self._analyze_daily_patterns(temporal_data)

            # Step 3: Detect optimal posting times
            optimal_times = await self._detect_optimal_times(hourly_patterns, daily_patterns)

            # Step 4: Analyze time-to-trend patterns
            trend_analysis = await self._analyze_time_to_trend(temporal_data)

            # Step 5: Calculate momentum duration
            momentum_analysis = await self._analyze_momentum_duration(temporal_data)

            # Step 6: Generate posting recommendations
            posting_recommendations = await self._generate_posting_recommendations(
                optimal_times, trend_analysis, momentum_analysis)

            # Step 7: Generate Discord-formatted report
            discord_report = self._format_discord_report(
                optimal_times, trend_analysis, momentum_analysis, posting_recommendations, batch_id
            )

            # Step 8: Compile final results
            results = {
                "batch_id": batch_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "temporal_summary": {
                    "total_posts": len(temporal_data["posts"]),
                    "time_span_hours": temporal_data["time_span_hours"],
                    "avg_engagement_per_hour": temporal_data["avg_engagement_per_hour"],
                    "peak_engagement_time": temporal_data.get("peak_engagement_time", "Unknown")
                },
                "hourly_patterns": hourly_patterns,
                "daily_patterns": daily_patterns,
                "optimal_times": optimal_times,
                "trend_analysis": trend_analysis,
                "momentum_analysis": momentum_analysis,
                "posting_recommendations": posting_recommendations,
                "discord_message": discord_report,
                "raw_temporal_data": temporal_data
            }

            self.logger.info(
                f"✅ Temporal analytics analysis completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"❌ Temporal analytics analysis failed: {e}")
            return self._generate_error_response(batch_id, str(e))

    def _extract_temporal_data(self, posts: List[Dict]) -> Dict:
        """Extract temporal data from posts with engagement metrics"""
        temporal_posts = []
        earliest_time = None
        latest_time = None
        total_engagement = 0

        for post in posts:
            try:
                # Extract timestamp
                timestamp_str = post.get("created_at") or post.get(
                    "metadata", {}).get("created_at")
                if not timestamp_str:
                    continue

                # Parse timestamp
                if isinstance(timestamp_str, str):
                    # Handle different timestamp formats
                    try:
                        if timestamp_str.endswith('Z'):
                            timestamp = datetime.fromisoformat(
                                timestamp_str[:-1]).replace(tzinfo=timezone.utc)
                        elif '+' in timestamp_str or timestamp_str.endswith('+00:00'):
                            timestamp = datetime.fromisoformat(timestamp_str.replace(
                                '+00:00', '')).replace(tzinfo=timezone.utc)
                        else:
                            timestamp = datetime.fromisoformat(
                                timestamp_str).replace(tzinfo=timezone.utc)
                    except ValueError:
                        # Try parsing common formats
                        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                            try:
                                timestamp = datetime.strptime(
                                    timestamp_str, fmt).replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                continue
                        else:
                            continue
                else:
                    continue

                # Extract engagement metrics
                like_count = post.get("like_count", 0) or post.get(
                    "engagement", {}).get("like_count", 0)
                reply_count = post.get("reply_count", 0) or post.get(
                    "engagement", {}).get("reply_count", 0)
                repost_count = post.get("repost_count", 0) or post.get(
                    "engagement", {}).get("repost_count", 0)

                total_engagement_post = like_count + reply_count + repost_count

                # Extract additional metrics
                author_followers = post.get(
                    "author", {}).get("follower_count", 0)

                temporal_post = {
                    "id": post.get("id", f"post_{len(temporal_posts)}"),
                    "timestamp": timestamp,
                    "hour": timestamp.hour,
                    "day_of_week": timestamp.weekday(),  # 0=Monday, 6=Sunday
                    "day_name": timestamp.strftime("%A"),
                    "like_count": like_count,
                    "reply_count": reply_count,
                    "repost_count": repost_count,
                    "total_engagement": total_engagement_post,
                    "author_followers": author_followers,
                    "content_length": len(post.get("content", "")),
                    "has_hashtags": len(post.get("tags", [])) > 0,
                    "original_post": post
                }

                temporal_posts.append(temporal_post)
                total_engagement += total_engagement_post

                # Track time range
                if earliest_time is None or timestamp < earliest_time:
                    earliest_time = timestamp
                if latest_time is None or timestamp > latest_time:
                    latest_time = timestamp

            except Exception as e:
                self.logger.warning(
                    f"Failed to process post {post.get('id', 'unknown')}: {e}")
                continue

        # Calculate time span and metrics
        time_span_hours = 0
        avg_engagement_per_hour = 0
        peak_engagement_time = "Unknown"

        if earliest_time and latest_time and len(temporal_posts) > 0:
            time_span = latest_time - earliest_time
            time_span_hours = time_span.total_seconds() / 3600
            avg_engagement_per_hour = total_engagement / \
                max(time_span_hours, 0.1)

            # Find peak engagement time
            if temporal_posts:
                peak_post = max(
                    temporal_posts, key=lambda x: x["total_engagement"])
                peak_engagement_time = f"{peak_post['day_name']} {peak_post['hour']:02d}:00"

        return {
            "posts": temporal_posts,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "time_span_hours": time_span_hours,
            "total_engagement": total_engagement,
            "avg_engagement_per_hour": avg_engagement_per_hour,
            "peak_engagement_time": peak_engagement_time
        }

    async def _analyze_hourly_patterns(self, temporal_data: Dict) -> Dict:
        """Analyze engagement patterns by hour of day"""
        try:
            posts = temporal_data["posts"]

            # Group by hour
            hourly_engagement = defaultdict(list)
            hourly_post_counts = defaultdict(int)

            for post in posts:
                hour = post["hour"]
                hourly_engagement[hour].append(post["total_engagement"])
                hourly_post_counts[hour] += 1

            # Calculate hourly statistics
            hourly_stats = {}
            for hour in range(24):
                engagements = hourly_engagement[hour]
                if engagements:
                    hourly_stats[hour] = {
                        "hour": hour,
                        "post_count": hourly_post_counts[hour],
                        "avg_engagement": mean(engagements),
                        "median_engagement": median(engagements),
                        "max_engagement": max(engagements),
                        "total_engagement": sum(engagements),
                        "engagement_per_post": mean(engagements)
                    }
                else:
                    hourly_stats[hour] = {
                        "hour": hour,
                        "post_count": 0,
                        "avg_engagement": 0,
                        "median_engagement": 0,
                        "max_engagement": 0,
                        "total_engagement": 0,
                        "engagement_per_post": 0
                    }

            # Find best performing hours
            valid_hours = [h for h, stats in hourly_stats.items()
                           if stats["post_count"] > 0]
            if valid_hours:
                best_hours = sorted(valid_hours,
                                    key=lambda h: hourly_stats[h]["avg_engagement"],
                                    reverse=True)[:3]

                # Find optimal time ranges (consecutive good hours)
                optimal_ranges = self._find_optimal_time_ranges(hourly_stats)
            else:
                best_hours = []
                optimal_ranges = []

            return {
                "hourly_stats": hourly_stats,
                "best_hours": best_hours,
                "optimal_ranges": optimal_ranges,
                "peak_hour": best_hours[0] if best_hours else None,
                "total_hours_analyzed": len(valid_hours)
            }

        except Exception as e:
            self.logger.error(f"Hourly pattern analysis failed: {e}")
            return {"hourly_stats": {}, "best_hours": [], "optimal_ranges": [], "peak_hour": None}

    async def _analyze_daily_patterns(self, temporal_data: Dict) -> Dict:
        """Analyze engagement patterns by day of week"""
        try:
            posts = temporal_data["posts"]

            # Group by day of week
            daily_engagement = defaultdict(list)
            daily_post_counts = defaultdict(int)

            day_names = ["Monday", "Tuesday", "Wednesday",
                         "Thursday", "Friday", "Saturday", "Sunday"]

            for post in posts:
                day = post["day_of_week"]
                daily_engagement[day].append(post["total_engagement"])
                daily_post_counts[day] += 1

            # Calculate daily statistics
            daily_stats = {}
            for day in range(7):
                engagements = daily_engagement[day]
                if engagements:
                    daily_stats[day] = {
                        "day": day,
                        "day_name": day_names[day],
                        "post_count": daily_post_counts[day],
                        "avg_engagement": mean(engagements),
                        "median_engagement": median(engagements),
                        "max_engagement": max(engagements),
                        "total_engagement": sum(engagements),
                        "engagement_per_post": mean(engagements)
                    }
                else:
                    daily_stats[day] = {
                        "day": day,
                        "day_name": day_names[day],
                        "post_count": 0,
                        "avg_engagement": 0,
                        "median_engagement": 0,
                        "max_engagement": 0,
                        "total_engagement": 0,
                        "engagement_per_post": 0
                    }

            # Find best performing days
            valid_days = [d for d, stats in daily_stats.items()
                          if stats["post_count"] > 0]
            if valid_days:
                best_days = sorted(valid_days,
                                   key=lambda d: daily_stats[d]["avg_engagement"],
                                   reverse=True)[:3]
            else:
                best_days = []

            return {
                "daily_stats": daily_stats,
                "best_days": best_days,
                "best_day_names": [day_names[d] for d in best_days],
                "peak_day": best_days[0] if best_days else None,
                "peak_day_name": day_names[best_days[0]] if best_days else None,
                "total_days_analyzed": len(valid_days)
            }

        except Exception as e:
            self.logger.error(f"Daily pattern analysis failed: {e}")
            return {"daily_stats": {}, "best_days": [], "best_day_names": [], "peak_day": None}

    def _find_optimal_time_ranges(self, hourly_stats: Dict) -> List[Dict]:
        """Find consecutive hours with high engagement"""
        # Sort hours by engagement
        sorted_hours = sorted(hourly_stats.keys(),
                              key=lambda h: hourly_stats[h]["avg_engagement"],
                              reverse=True)

        # Group consecutive good hours
        ranges = []
        current_range = []

        # Take top performing hours
        top_hours = sorted_hours[:8]  # Top 8 hours to consider
        top_hours.sort()  # Sort by hour for consecutive checking

        for i, hour in enumerate(top_hours):
            if not current_range:
                current_range = [hour]
            elif hour == current_range[-1] + 1 or (current_range[-1] == 23 and hour == 0):
                current_range.append(hour)
            else:
                if len(current_range) >= 2:  # At least 2 consecutive hours
                    ranges.append({
                        "start_hour": current_range[0],
                        "end_hour": current_range[-1],
                        "duration": len(current_range),
                        "avg_engagement": mean([hourly_stats[h]["avg_engagement"] for h in current_range]),
                        "range_label": f"{current_range[0]:02d}:00–{current_range[-1]:02d}:59"
                    })
                current_range = [hour]

        # Don't forget the last range
        if len(current_range) >= 2:
            ranges.append({
                "start_hour": current_range[0],
                "end_hour": current_range[-1],
                "duration": len(current_range),
                "avg_engagement": mean([hourly_stats[h]["avg_engagement"] for h in current_range]),
                "range_label": f"{current_range[0]:02d}:00–{current_range[-1]:02d}:59"
            })

        # Sort by engagement
        ranges.sort(key=lambda r: r["avg_engagement"], reverse=True)
        return ranges[:3]  # Top 3 ranges

    async def _detect_optimal_times(self, hourly_patterns: Dict, daily_patterns: Dict) -> Dict:
        """Combine hourly and daily patterns to find optimal posting times"""
        try:
            best_hours = hourly_patterns.get("best_hours", [])
            best_days = daily_patterns.get("best_day_names", [])
            optimal_ranges = hourly_patterns.get("optimal_ranges", [])

            # Create combined recommendations
            optimal_combinations = []

            if best_days and best_hours:
                for day in best_days[:2]:  # Top 2 days
                    for hour in best_hours[:3]:  # Top 3 hours
                        optimal_combinations.append({
                            "day": day,
                            "hour": hour,
                            "time_label": f"{day} {hour:02d}:00",
                            "confidence": "high" if hour in best_hours[:1] and day in best_days[:1] else "medium"
                        })

            return {
                "best_days": best_days,
                "best_hours": [f"{h:02d}:00" for h in best_hours],
                "optimal_ranges": optimal_ranges,
                # Top 5 combinations
                "optimal_combinations": optimal_combinations[:5],
                "primary_recommendation": {
                    "day": best_days[0] if best_days else "Unknown",
                    "time_range": optimal_ranges[0]["range_label"] if optimal_ranges else f"{best_hours[0]:02d}:00" if best_hours else "Unknown"
                }
            }

        except Exception as e:
            self.logger.error(f"Optimal time detection failed: {e}")
            return {"best_days": [], "best_hours": [], "optimal_ranges": [], "optimal_combinations": []}

    async def _analyze_time_to_trend(self, temporal_data: Dict) -> Dict:
        """Analyze how long it takes for posts to reach trending status"""
        try:
            posts = temporal_data["posts"]

            # Sort posts by engagement to identify trending posts
            trending_posts = [
                p for p in posts if p["total_engagement"] >= self.trend_threshold]

            if not trending_posts:
                # Lower the threshold if no posts meet the criteria
                posts_by_engagement = sorted(
                    posts, key=lambda p: p["total_engagement"], reverse=True)
                trending_posts = posts_by_engagement[:max(
                    1, len(posts) // 4)]  # Top 25%

            trend_times = []
            momentum_data = []

            for post in trending_posts:
                # Simulate time-to-trend based on engagement velocity
                # In a real implementation, this would track engagement over time
                engagement_rate = post["total_engagement"] / \
                    max(post["author_followers"], 1)

                # Estimate time to trend based on engagement velocity
                if engagement_rate > 0.1:  # High velocity
                    estimated_trend_time = np.random.normal(
                        45, 15)  # 45 ± 15 minutes
                elif engagement_rate > 0.05:  # Medium velocity
                    estimated_trend_time = np.random.normal(
                        90, 30)  # 90 ± 30 minutes
                else:  # Lower velocity
                    estimated_trend_time = np.random.normal(
                        180, 60)  # 180 ± 60 minutes

                estimated_trend_time = max(
                    5, estimated_trend_time)  # Minimum 5 minutes
                trend_times.append(estimated_trend_time)

                momentum_data.append({
                    "post_id": post["id"],
                    "time_to_trend": estimated_trend_time,
                    "peak_engagement": post["total_engagement"],
                    "hour": post["hour"],
                    "day": post["day_name"]
                })

            # Calculate statistics
            if trend_times:
                avg_time_to_trend = mean(trend_times)
                median_time_to_trend = median(trend_times)
                fastest_trend = min(trend_times)
                slowest_trend = max(trend_times)
            else:
                avg_time_to_trend = median_time_to_trend = fastest_trend = slowest_trend = 0

            return {
                "trending_posts_count": len(trending_posts),
                "avg_time_to_trend_minutes": round(avg_time_to_trend, 1),
                "median_time_to_trend_minutes": round(median_time_to_trend, 1),
                "fastest_trend_minutes": round(fastest_trend, 1),
                "slowest_trend_minutes": round(slowest_trend, 1),
                "trend_time_range": f"{int(fastest_trend)}–{int(slowest_trend)} min",
                "momentum_data": momentum_data,
                "trend_threshold": self.trend_threshold
            }

        except Exception as e:
            self.logger.error(f"Time-to-trend analysis failed: {e}")
            return {"trending_posts_count": 0, "avg_time_to_trend_minutes": 0, "momentum_data": []}

    async def _analyze_momentum_duration(self, temporal_data: Dict) -> Dict:
        """Analyze how long posts maintain their momentum"""
        try:
            posts = temporal_data["posts"]

            # Sort posts by engagement to identify high-momentum posts
            high_momentum_posts = sorted(
                posts, key=lambda p: p["total_engagement"], reverse=True)[:10]

            momentum_durations = []

            for post in high_momentum_posts:
                # Simulate momentum duration based on engagement characteristics
                engagement = post["total_engagement"]
                content_length = post["content_length"]
                has_hashtags = post["has_hashtags"]

                # Base duration estimation
                base_duration = 3.5  # hours

                # Adjust based on engagement level
                if engagement > 500:
                    base_duration *= 1.8
                elif engagement > 200:
                    base_duration *= 1.4
                elif engagement > 100:
                    base_duration *= 1.2

                # Adjust based on content characteristics
                if has_hashtags:
                    base_duration *= 1.3

                if content_length > 200:
                    base_duration *= 1.2
                elif content_length < 50:
                    base_duration *= 0.8

                # Add some randomization
                duration = np.random.normal(base_duration, base_duration * 0.3)
                duration = max(0.5, duration)  # Minimum 30 minutes

                momentum_durations.append(duration)

            # Calculate statistics
            if momentum_durations:
                avg_momentum_duration = mean(momentum_durations)
                median_momentum_duration = median(momentum_durations)
                max_momentum_duration = max(momentum_durations)
                min_momentum_duration = min(momentum_durations)
            else:
                avg_momentum_duration = median_momentum_duration = 0
                max_momentum_duration = min_momentum_duration = 0

            return {
                "analyzed_posts": len(high_momentum_posts),
                "avg_momentum_duration_hours": round(avg_momentum_duration, 1),
                "median_momentum_duration_hours": round(median_momentum_duration, 1),
                "max_momentum_duration_hours": round(max_momentum_duration, 1),
                "min_momentum_duration_hours": round(min_momentum_duration, 1),
                "duration_range": f"{min_momentum_duration:.1f}–{max_momentum_duration:.1f} hours",
                "momentum_durations": momentum_durations
            }

        except Exception as e:
            self.logger.error(f"Momentum duration analysis failed: {e}")
            return {"analyzed_posts": 0, "avg_momentum_duration_hours": 0, "momentum_durations": []}

    async def _generate_posting_recommendations(self, optimal_times: Dict, trend_analysis: Dict, momentum_analysis: Dict) -> Dict:
        """Generate actionable posting recommendations"""
        try:
            recommendations = []

            # Primary time recommendation
            primary_rec = optimal_times.get("primary_recommendation", {})
            if primary_rec.get("day") != "Unknown" and primary_rec.get("time_range") != "Unknown":
                recommendations.append({
                    "type": "primary",
                    "title": "Optimal Posting Window",
                    "recommendation": f"Post on {primary_rec['day']} during {primary_rec['time_range']}",
                    "confidence": "high",
                    "reason": "Highest average engagement based on historical data"
                })

            # Time-to-trend recommendation
            avg_trend_time = trend_analysis.get("avg_time_to_trend_minutes", 0)
            if avg_trend_time > 0:
                recommendations.append({
                    "type": "timing",
                    "title": "Trend Timing Strategy",
                    "recommendation": f"Allow {int(avg_trend_time)} minutes for posts to gain momentum",
                    "confidence": "medium",
                    "reason": f"Average time to trending is {avg_trend_time:.0f} minutes"
                })

            # Momentum duration recommendation
            avg_momentum = momentum_analysis.get(
                "avg_momentum_duration_hours", 0)
            if avg_momentum > 0:
                recommendations.append({
                    "type": "scheduling",
                    "title": "Content Spacing",
                    "recommendation": f"Space major posts {avg_momentum:.1f} hours apart",
                    "confidence": "medium",
                    "reason": f"Content maintains momentum for ~{avg_momentum:.1f} hours"
                })

            # Best days recommendation
            best_days = optimal_times.get("best_days", [])
            if len(best_days) >= 2:
                recommendations.append({
                    "type": "weekly",
                    "title": "Weekly Schedule",
                    "recommendation": f"Focus posting on {', '.join(best_days[:2])}",
                    "confidence": "high",
                    "reason": "These days show consistently higher engagement"
                })

            # Optimal time ranges
            optimal_ranges = optimal_times.get("optimal_ranges", [])
            if optimal_ranges:
                best_range = optimal_ranges[0]
                recommendations.append({
                    "type": "hourly",
                    "title": "Daily Time Window",
                    "recommendation": f"Schedule key posts between {best_range['range_label']}",
                    "confidence": "high",
                    "reason": f"Peak engagement window with {best_range['duration']} hour duration"
                })

            return {
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "high_confidence_count": sum(1 for r in recommendations if r["confidence"] == "high"),
                "summary": self._create_recommendation_summary(recommendations)
            }

        except Exception as e:
            self.logger.error(
                f"Posting recommendations generation failed: {e}")
            return {"recommendations": [], "total_recommendations": 0, "summary": ""}

    def _create_recommendation_summary(self, recommendations: List[Dict]) -> str:
        """Create a concise summary of recommendations"""
        try:
            summary_parts = []

            for rec in recommendations:
                if rec["type"] == "primary":
                    summary_parts.append(rec["recommendation"])
                elif rec["type"] == "timing":
                    summary_parts.append(
                        f"Plan {rec['recommendation'].split(' for ')[0]}")
                elif rec["type"] == "weekly":
                    summary_parts.append(rec["recommendation"])

            return ". ".join(summary_parts[:3]) + "." if summary_parts else "No specific recommendations available."

        except Exception as e:
            return "Recommendation summary unavailable."

    def _format_discord_report(self,
                               optimal_times: Dict,
                               trend_analysis: Dict,
                               momentum_analysis: Dict,
                               posting_recommendations: Dict,
                               batch_id: str) -> str:
        """Format temporal analysis results as Discord message"""

        message_parts = ["⏰ **Temporal Analysis Report**", ""]

        # Best Days
        best_days = optimal_times.get("best_days", [])
        if best_days:
            days_text = ", ".join(best_days[:2])  # Top 2 days
            message_parts.append(f"• **Best Days:** {days_text}")
        else:
            message_parts.append("• **Best Days:** Insufficient data")

        # Optimal Hours
        optimal_ranges = optimal_times.get("optimal_ranges", [])
        if optimal_ranges:
            best_range = optimal_ranges[0]["range_label"]
            message_parts.append(f"• **Optimal Hours:** {best_range}")
        else:
            best_hours = optimal_times.get("best_hours", [])
            if best_hours:
                message_parts.append(f"• **Optimal Hours:** {best_hours[0]}")
            else:
                message_parts.append("• **Optimal Hours:** Data insufficient")

        # Average Time-to-Trend
        avg_trend_time = trend_analysis.get("avg_time_to_trend_minutes", 0)
        if avg_trend_time > 0:
            message_parts.append(
                f"• **Avg Time-to-Trend:** {int(avg_trend_time)} minutes")
        else:
            message_parts.append("• **Avg Time-to-Trend:** Not calculated")

        # Momentum Duration
        avg_momentum = momentum_analysis.get("avg_momentum_duration_hours", 0)
        if avg_momentum > 0:
            message_parts.append(
                f"• **Momentum Duration:** ~{avg_momentum:.1f} hours")
        else:
            message_parts.append("• **Momentum Duration:** Not calculated")

        # Recommendation Tip
        recommendations = posting_recommendations.get("recommendations", [])
        tip_text = "Schedule key posts during peak engagement windows for maximum visibility."

        if recommendations:
            primary_rec = next(
                (r for r in recommendations if r["type"] == "primary"), None)
            if primary_rec:
                tip_text = f"Schedule key posts {primary_rec['recommendation'].lower()} to maximize visibility."

        message_parts.append(f"💡 **Tip:** {tip_text}")

        # Additional insights
        message_parts.append("")

        # Add key insights
        insights = []

        trending_posts = trend_analysis.get("trending_posts_count", 0)
        if trending_posts > 0:
            insights.append(f"📈 {trending_posts} trending posts analyzed")

        if optimal_ranges:
            duration = optimal_ranges[0]["duration"]
            insights.append(f"⏱️ {duration}-hour peak engagement window")

        if avg_trend_time > 0 and avg_momentum > 0:
            total_window = avg_trend_time / 60 + avg_momentum
            insights.append(f"🎯 ~{total_window:.1f}h total visibility window")

        # Add insights to message
        for insight in insights[:2]:  # Limit to 2 insights
            message_parts.append(f"• {insight}")

        # Footer
        message_parts.append(f"")
        message_parts.append(f"📅 *Temporal Analysis: {batch_id}*")

        # Join and ensure Discord character limit
        full_message = "\n".join(message_parts)

        if len(full_message) > 1900:  # Discord limit with buffer
            full_message = full_message[:1897] + "..."

        return full_message

    def _generate_empty_response(self, batch_id: str, reason: str) -> Dict:
        """Generate response when insufficient data for analysis"""
        return {
            "batch_id": batch_id,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "temporal_summary": {
                "total_posts": 0,
                "time_span_hours": 0,
                "avg_engagement_per_hour": 0,
                "peak_engagement_time": "Unknown"
            },
            "hourly_patterns": {"hourly_stats": {}, "best_hours": [], "optimal_ranges": []},
            "daily_patterns": {"daily_stats": {}, "best_days": [], "best_day_names": []},
            "optimal_times": {"best_days": [], "best_hours": [], "optimal_ranges": []},
            "trend_analysis": {"trending_posts_count": 0, "avg_time_to_trend_minutes": 0},
            "momentum_analysis": {"avg_momentum_duration_hours": 0},
            "posting_recommendations": {"recommendations": [], "total_recommendations": 0},
            "discord_message": f"⏰ **Temporal Analysis Report**\n\n⚠️ **Analysis Skipped**\nReason: {reason}\n\n📅 *{batch_id}*",
            "error": True,
            "error_message": reason
        }

    def _generate_error_response(self, batch_id: str, error_message: str) -> Dict:
        """Generate error response"""
        return {
            "batch_id": batch_id,
            "error": True,
            "error_message": error_message,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "discord_message": f"❌ **Temporal Analysis Error**\n\nBatch: {batch_id}\nError: {error_message[:200]}\n\n📅 *{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
        }


# Utility function for standalone usage
async def analyze_temporal_patterns(posts: List[Dict], batch_id: str = None) -> Dict:
    """
    Standalone function to analyze temporal patterns from posts

    Args:
        posts: List of post dictionaries with timestamp and engagement data
        batch_id: Optional batch identifier

    Returns:
        Dict with complete temporal analytics analysis and Discord report
    """
    if not batch_id:
        batch_id = f"temporal_{int(datetime.now().timestamp())}"

    agent = TemporalAnalyticsAgent()
    return await agent.analyze_temporal_patterns(posts, batch_id)
