"""
Strategic Intelligence Analysis Engine
Specializes in narrative and campaign strategy analysis for political/social content
"""

import asyncio
import json
import logging
import re
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from statistics import mean, median
import numpy as np

logger = logging.getLogger(__name__)


class StrategicIntelligenceAgent:
    """
    Strategic Intelligence Agent for Campaign and Narrative Analysis

    Analyzes:
    1. Content framing classification (attack/support/call-to-action/emotional-appeal)
    2. Coordinated posting behavior and campaign groups
    3. Dominant emotional strategies and consistency
    4. Shared themes and narrative patterns
    5. Strategic timing and messaging coordination
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Strategic analysis parameters
        self.min_posts_for_analysis = 5
        # Similarity threshold for coordination detection
        self.coordination_threshold = 0.7
        # Time window for detecting coordinated posting
        self.group_detection_window_hours = 6
        # Threshold for emotion shift detection
        self.emotion_consistency_threshold = 0.15

        # Framing keywords for classification
        self.framing_keywords = {
            "attack": [
                "corrupt", "failed", "dangerous", "incompetent", "lies", "fraud", "scandal",
                "betrayed", "disaster", "crisis", "failed", "broken", "destroying", "ruining",
                "exposed", "caught", "wrong", "terrible", "worst", "disaster", "catastrophe"
            ],
            "support": [
                "excellent", "successful", "great", "amazing", "proud", "achievement", "victory",
                "progress", "improvement", "positive", "strong", "effective", "working", "delivering",
                "champion", "leader", "hero", "dedicated", "committed", "fighting for"
            ],
            "call_to_action": [
                "vote", "support", "join", "donate", "volunteer", "share", "spread", "tell",
                "contact", "call", "write", "attend", "participate", "register", "sign up",
                "take action", "make a difference", "get involved", "stand up", "fight back"
            ],
            "emotional_appeal": [
                "future", "children", "family", "hope", "dream", "fear", "worried", "concerned",
                "heartbreaking", "inspiring", "amazing", "incredible", "together", "unity",
                "freedom", "justice", "fairness", "opportunity", "prosperity", "security"
            ]
        }

        # Common political themes
        self.political_themes = {
            "economy": ["economy", "jobs", "employment", "wages", "taxes", "business", "trade", "inflation"],
            "healthcare": ["healthcare", "health", "medical", "insurance", "doctors", "hospitals", "medicine"],
            "education": ["education", "schools", "teachers", "students", "college", "university", "learning"],
            "immigration": ["immigration", "border", "migrants", "refugees", "citizenship", "deportation"],
            "environment": ["climate", "environment", "green", "pollution", "energy", "renewable", "carbon"],
            "security": ["security", "defense", "military", "police", "crime", "safety", "terrorism"],
            "politics": ["politics", "government", "democracy", "election", "voting", "campaign", "policy"],
            "social": ["social", "equality", "rights", "justice", "discrimination", "community", "society"],
            "reform": ["reform", "change", "transformation", "revolution", "movement", "progress", "innovation"],
            "hope": ["hope", "future", "tomorrow", "better", "improvement", "optimism", "positive"]
        }

    async def analyze_strategic_patterns(self, posts: List[Dict], batch_id: str) -> Dict:
        """
        Run complete strategic intelligence analysis

        Args:
            posts: List of post dictionaries with content and engagement data
            batch_id: Unique identifier for this analysis

        Returns:
            Dict with strategic analysis results and Discord-formatted report
        """
        try:
            self.logger.info(
                f"🧭 Starting strategic intelligence analysis for batch {batch_id}")

            if len(posts) < self.min_posts_for_analysis:
                return self._generate_empty_response(batch_id, "Insufficient posts for strategic analysis")

            # Step 1: Classify posts by framing
            framing_analysis = await self._classify_content_framing(posts)

            # Step 2: Detect shared themes
            theme_analysis = await self._analyze_shared_themes(posts)

            # Step 3: Detect coordinated posting behavior
            coordination_analysis = await self._detect_coordinated_behavior(posts)

            # Step 4: Analyze emotional strategies
            emotional_analysis = await self._analyze_emotional_strategies(posts)

            # Step 5: Identify strategic patterns
            strategic_patterns = await self._identify_strategic_patterns(
                framing_analysis, theme_analysis, coordination_analysis, emotional_analysis
            )

            # Step 6: Generate Discord report
            discord_report = self._format_strategic_discord_report(
                framing_analysis, theme_analysis, coordination_analysis,
                emotional_analysis, strategic_patterns, batch_id
            )

            # Step 7: Compile results
            results = {
                "batch_id": batch_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "strategic_summary": {
                    "total_posts": len(posts),
                    "analyzed_posts": len([p for p in posts if p.get("content")]),
                    "dominant_framing": framing_analysis.get("dominant_framing", "Unknown"),
                    "main_themes": theme_analysis.get("top_themes", [])[:3],
                    "coordination_detected": coordination_analysis.get("groups_detected", 0) > 0
                },
                "framing_analysis": framing_analysis,
                "theme_analysis": theme_analysis,
                "coordination_analysis": coordination_analysis,
                "emotional_analysis": emotional_analysis,
                "strategic_patterns": strategic_patterns,
                "discord_message": discord_report
            }

            self.logger.info(
                f"✅ Strategic intelligence analysis completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"❌ Strategic intelligence analysis failed: {e}")
            return self._generate_error_response(batch_id, str(e))

    async def _classify_content_framing(self, posts: List[Dict]) -> Dict:
        """Classify posts by framing strategy"""
        try:
            framing_counts = {"attack": 0, "support": 0,
                              "call_to_action": 0, "emotional_appeal": 0, "neutral": 0}
            post_classifications = []

            for post in posts:
                content = post.get("content", "").lower()
                if not content:
                    continue

                # Score each framing type
                scores = {}
                for framing_type, keywords in self.framing_keywords.items():
                    score = sum(
                        1 for keyword in keywords if keyword in content)
                    scores[framing_type] = score

                # Determine dominant framing
                if sum(scores.values()) == 0:
                    classification = "neutral"
                else:
                    classification = max(
                        scores.keys(), key=lambda k: scores[k])

                framing_counts[classification] += 1

                post_classifications.append({
                    "post_id": post.get("id", "unknown"),
                    "framing": classification,
                    "scores": scores,
                    "content_preview": content[:100] + "..." if len(content) > 100 else content
                })

            # Calculate percentages
            total_posts = sum(framing_counts.values())
            framing_percentages = {}
            if total_posts > 0:
                for framing, count in framing_counts.items():
                    framing_percentages[framing] = round(
                        (count / total_posts) * 100, 1)

            # Find dominant framing
            dominant_framing = max(framing_counts.keys(),
                                   key=lambda k: framing_counts[k])

            return {
                "framing_counts": framing_counts,
                "framing_percentages": framing_percentages,
                "dominant_framing": dominant_framing,
                "post_classifications": post_classifications,
                "total_analyzed": total_posts
            }

        except Exception as e:
            self.logger.error(f"Content framing analysis failed: {e}")
            return {"framing_counts": {}, "dominant_framing": "Unknown", "post_classifications": []}

    async def _analyze_shared_themes(self, posts: List[Dict]) -> Dict:
        """Analyze shared themes across posts"""
        try:
            theme_counts = defaultdict(int)
            theme_posts = defaultdict(list)

            for post in posts:
                content = post.get("content", "").lower()
                if not content:
                    continue

                # Check for theme keywords
                for theme, keywords in self.political_themes.items():
                    theme_score = sum(
                        1 for keyword in keywords if keyword in content)
                    if theme_score > 0:
                        theme_counts[theme] += theme_score
                        theme_posts[theme].append({
                            "post_id": post.get("id", "unknown"),
                            "score": theme_score,
                            "content_preview": content[:80] + "..." if len(content) > 80 else content
                        })

            # Sort themes by frequency
            sorted_themes = sorted(theme_counts.items(),
                                   key=lambda x: x[1], reverse=True)
            top_themes = [theme for theme, count in sorted_themes[:5]]

            # Calculate theme percentages
            total_theme_mentions = sum(theme_counts.values())
            theme_percentages = {}
            if total_theme_mentions > 0:
                for theme, count in theme_counts.items():
                    theme_percentages[theme] = round(
                        (count / total_theme_mentions) * 100, 1)

            return {
                "theme_counts": dict(theme_counts),
                "theme_percentages": theme_percentages,
                "top_themes": top_themes,
                "theme_posts": dict(theme_posts),
                "total_theme_mentions": total_theme_mentions
            }

        except Exception as e:
            self.logger.error(f"Theme analysis failed: {e}")
            return {"theme_counts": {}, "top_themes": [], "theme_posts": {}}

    async def _detect_coordinated_behavior(self, posts: List[Dict]) -> Dict:
        """Detect coordinated posting behavior and campaign groups"""
        try:
            groups_detected = []
            author_posting_patterns = defaultdict(list)

            # Group posts by author and analyze timing
            for post in posts:
                author = post.get("author", {}).get("username", "unknown")
                timestamp_str = post.get("created_at") or post.get(
                    "metadata", {}).get("created_at")

                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, str):
                            if timestamp_str.endswith('Z'):
                                timestamp = datetime.fromisoformat(
                                    timestamp_str[:-1]).replace(tzinfo=timezone.utc)
                            else:
                                timestamp = datetime.fromisoformat(
                                    timestamp_str).replace(tzinfo=timezone.utc)
                        else:
                            continue

                        author_posting_patterns[author].append({
                            "post_id": post.get("id", "unknown"),
                            "timestamp": timestamp,
                            "content": post.get("content", ""),
                            "engagement": post.get("like_count", 0) + post.get("reply_count", 0) + post.get("repost_count", 0)
                        })
                    except:
                        continue

            # Detect potential coordination groups
            authors = list(author_posting_patterns.keys())

            for i, author1 in enumerate(authors):
                for author2 in authors[i+1:]:
                    coordination_score = self._calculate_coordination_score(
                        author_posting_patterns[author1],
                        author_posting_patterns[author2]
                    )

                    if coordination_score > self.coordination_threshold:
                        # Check if this is part of an existing group
                        group_found = False
                        for group in groups_detected:
                            if author1 in group["members"] or author2 in group["members"]:
                                if author1 not in group["members"]:
                                    group["members"].append(author1)
                                if author2 not in group["members"]:
                                    group["members"].append(author2)
                                group["coordination_score"] = max(
                                    group["coordination_score"], coordination_score)
                                group_found = True
                                break

                        if not group_found:
                            # Create new group
                            group_name = self._generate_group_name(
                                [author1, author2])
                            groups_detected.append({
                                "group_name": group_name,
                                "members": [author1, author2],
                                "coordination_score": coordination_score,
                                "synchronized_posts": self._find_synchronized_posts(
                                    author_posting_patterns[author1],
                                    author_posting_patterns[author2]
                                )
                            })

            # Analyze group characteristics
            group_analysis = []
            for group in groups_detected:
                total_posts = sum(
                    len(author_posting_patterns[member]) for member in group["members"])
                avg_engagement = 0
                if total_posts > 0:
                    total_engagement = sum(
                        sum(post["engagement"]
                            for post in author_posting_patterns[member])
                        for member in group["members"]
                    )
                    avg_engagement = total_engagement / total_posts

                group_analysis.append({
                    "group_name": group["group_name"],
                    "member_count": len(group["members"]),
                    "total_posts": total_posts,
                    "avg_engagement": round(avg_engagement, 1),
                    "coordination_level": "High" if group["coordination_score"] > 0.8 else "Medium"
                })

            return {
                "groups_detected": len(groups_detected),
                "coordination_groups": groups_detected,
                "group_analysis": group_analysis,
                "total_authors_analyzed": len(authors),
                "coordination_threshold": self.coordination_threshold
            }

        except Exception as e:
            self.logger.error(f"Coordination detection failed: {e}")
            return {"groups_detected": 0, "coordination_groups": [], "group_analysis": []}

    def _calculate_coordination_score(self, posts1: List[Dict], posts2: List[Dict]) -> float:
        """Calculate coordination score between two authors"""
        try:
            if not posts1 or not posts2:
                return 0.0

            # Check temporal coordination (posting within same time windows)
            temporal_score = 0.0
            for post1 in posts1:
                for post2 in posts2:
                    time_diff = abs(
                        (post1["timestamp"] - post2["timestamp"]).total_seconds())
                    if time_diff <= self.group_detection_window_hours * 3600:  # Within window
                        temporal_score += 1

            temporal_score = min(1.0, temporal_score /
                                 max(len(posts1), len(posts2)))

            # Check content similarity (simple keyword overlap)
            content_score = 0.0
            for post1 in posts1:
                content1_words = set(post1["content"].lower().split())
                for post2 in posts2:
                    content2_words = set(post2["content"].lower().split())
                    if content1_words and content2_words:
                        overlap = len(
                            content1_words.intersection(content2_words))
                        total_unique = len(
                            content1_words.union(content2_words))
                        if total_unique > 0:
                            content_score = max(
                                content_score, overlap / total_unique)

            # Combined coordination score
            return (temporal_score * 0.6 + content_score * 0.4)

        except Exception as e:
            return 0.0

    def _generate_group_name(self, members: List[str]) -> str:
        """Generate a group name based on member usernames"""
        try:
            # Extract common patterns or prefixes
            if len(members) >= 2:
                # Look for common prefixes or patterns
                common_chars = ""
                for i in range(min(len(members[0]), len(members[1]))):
                    if members[0][i].lower() == members[1][i].lower():
                        common_chars += members[0][i]
                    else:
                        break

                if len(common_chars) >= 3:
                    return f"{common_chars.capitalize()}Group"

                # Try extracting apparent team names
                for member in members:
                    if any(team_word in member.lower() for team_word in ["team", "squad", "group", "collective"]):
                        base_name = member.split(
                            "_")[0] if "_" in member else member[:6]
                        return f"{base_name.capitalize()}Team"

            # Default naming
            return f"Group_{members[0][:3]}{members[1][:3]}".replace("_", "")

        except:
            return "CoordinatedGroup"

    def _find_synchronized_posts(self, posts1: List[Dict], posts2: List[Dict]) -> int:
        """Find posts that were made in coordination"""
        synchronized = 0
        for post1 in posts1:
            for post2 in posts2:
                time_diff = abs(
                    (post1["timestamp"] - post2["timestamp"]).total_seconds())
                if time_diff <= 3600:  # Within 1 hour
                    synchronized += 1
                    break
        return synchronized

    async def _analyze_emotional_strategies(self, posts: List[Dict]) -> Dict:
        """Analyze emotional strategies and consistency"""
        try:
            emotion_scores = []
            emotional_patterns = {"positive": 0, "negative": 0, "neutral": 0}

            # Simple emotion keywords
            positive_words = ["great", "amazing", "excellent", "wonderful", "fantastic", "awesome",
                              "hope", "future", "progress", "success", "victory", "achievement"]
            negative_words = ["terrible", "awful", "disaster", "crisis", "failed", "broken",
                              "corrupt", "dangerous", "wrong", "worst", "catastrophe", "betrayed"]

            for post in posts:
                content = post.get("content", "").lower()
                if not content:
                    continue

                positive_score = sum(
                    1 for word in positive_words if word in content)
                negative_score = sum(
                    1 for word in negative_words if word in content)

                # Calculate emotion score (-1 to 1, negative to positive)
                total_emotional_words = positive_score + negative_score
                if total_emotional_words > 0:
                    emotion_score = (positive_score -
                                     negative_score) / total_emotional_words
                else:
                    emotion_score = 0  # neutral

                emotion_scores.append(emotion_score)

                # Categorize
                if emotion_score > 0.2:
                    emotional_patterns["positive"] += 1
                elif emotion_score < -0.2:
                    emotional_patterns["negative"] += 1
                else:
                    emotional_patterns["neutral"] += 1

            # Calculate consistency (lower standard deviation = more consistent)
            if len(emotion_scores) > 1:
                emotion_std = np.std(emotion_scores)
                avg_emotion = np.mean(emotion_scores)
                consistency_level = "High" if emotion_std < self.emotion_consistency_threshold else "Low"
            else:
                emotion_std = 0
                avg_emotion = emotion_scores[0] if emotion_scores else 0
                consistency_level = "Unknown"

            # Calculate percentages
            total_posts = sum(emotional_patterns.values())
            emotion_percentages = {}
            if total_posts > 0:
                for emotion, count in emotional_patterns.items():
                    emotion_percentages[emotion] = round(
                        (count / total_posts) * 100, 1)

            return {
                "emotion_scores": emotion_scores,
                "avg_emotion_score": round(avg_emotion, 3),
                "emotion_std_deviation": round(emotion_std, 3),
                "consistency_level": consistency_level,
                "emotional_patterns": emotional_patterns,
                "emotion_percentages": emotion_percentages,
                "dominant_emotion": max(emotional_patterns.keys(), key=lambda k: emotional_patterns[k])
            }

        except Exception as e:
            self.logger.error(f"Emotional analysis failed: {e}")
            return {"emotion_scores": [], "consistency_level": "Unknown", "emotional_patterns": {}}

    async def _identify_strategic_patterns(self, framing_analysis: Dict, theme_analysis: Dict,
                                           coordination_analysis: Dict, emotional_analysis: Dict) -> Dict:
        """Identify overall strategic patterns"""
        try:
            patterns = []

            # Pattern 1: Dominant messaging strategy
            dominant_framing = framing_analysis.get(
                "dominant_framing", "Unknown")
            framing_percentage = framing_analysis.get(
                "framing_percentages", {}).get(dominant_framing, 0)

            if framing_percentage > 50:
                patterns.append({
                    "pattern": "Dominant Messaging",
                    "description": f"Strong focus on {dominant_framing} messaging ({framing_percentage}%)",
                    "confidence": "High" if framing_percentage > 70 else "Medium"
                })

            # Pattern 2: Coordinated campaign activity
            groups_detected = coordination_analysis.get("groups_detected", 0)
            if groups_detected > 0:
                patterns.append({
                    "pattern": "Coordinated Activity",
                    "description": f"{groups_detected} coordinated group(s) detected",
                    "confidence": "High"
                })

            # Pattern 3: Emotional consistency
            consistency_level = emotional_analysis.get(
                "consistency_level", "Unknown")
            if consistency_level == "High":
                patterns.append({
                    "pattern": "Consistent Emotional Strategy",
                    "description": "Uniform emotional messaging across posts",
                    "confidence": "High"
                })

            # Pattern 4: Theme concentration
            top_themes = theme_analysis.get("top_themes", [])
            if len(top_themes) >= 2:
                patterns.append({
                    "pattern": "Focused Narrative",
                    "description": f"Concentrated on {', '.join(top_themes[:2])} themes",
                    "confidence": "Medium"
                })

            return {
                "patterns_detected": len(patterns),
                "strategic_patterns": patterns,
                "overall_strategy_assessment": self._assess_overall_strategy(patterns)
            }

        except Exception as e:
            self.logger.error(f"Strategic pattern identification failed: {e}")
            return {"patterns_detected": 0, "strategic_patterns": []}

    def _assess_overall_strategy(self, patterns: List[Dict]) -> str:
        """Assess overall strategic approach"""
        if len(patterns) >= 3:
            return "Highly Strategic - Multiple coordinated elements detected"
        elif len(patterns) >= 2:
            return "Strategic - Some coordination and planning evident"
        elif len(patterns) >= 1:
            return "Basic Strategy - Limited strategic elements"
        else:
            return "Organic - No clear strategic coordination detected"

    def _format_strategic_discord_report(self, framing_analysis: Dict, theme_analysis: Dict,
                                         coordination_analysis: Dict, emotional_analysis: Dict,
                                         strategic_patterns: Dict, batch_id: str) -> str:
        """Format strategic analysis results as Discord message"""

        message_parts = ["🧭 **Strategic Intelligence Summary**", ""]

        # Dominant Framing
        framing_percentages = framing_analysis.get("framing_percentages", {})
        if framing_percentages:
            # Get top 3 framings
            sorted_framings = sorted(
                framing_percentages.items(), key=lambda x: x[1], reverse=True)
            top_framings = []
            for framing, percentage in sorted_framings[:3]:
                if percentage > 0:
                    framing_display = framing.replace("_", " ").title()
                    top_framings.append(f"{framing_display} ({percentage}%)")

            if top_framings:
                message_parts.append(
                    f"• **Dominant Framing:** {', '.join(top_framings)}")
            else:
                message_parts.append("• **Dominant Framing:** Mixed messaging")
        else:
            message_parts.append("• **Dominant Framing:** Analysis incomplete")

        # Common Themes
        top_themes = theme_analysis.get("top_themes", [])
        if len(top_themes) >= 3:
            themes_display = ", ".join([theme.title()
                                       for theme in top_themes[:3]])
            message_parts.append(f"• **Common Themes:** {themes_display}")
        elif len(top_themes) >= 1:
            themes_display = ", ".join([theme.title() for theme in top_themes])
            message_parts.append(f"• **Common Themes:** {themes_display}")
        else:
            message_parts.append("• **Common Themes:** Diverse topics")

        # Detected Campaign Groups
        groups_detected = coordination_analysis.get("groups_detected", 0)
        if groups_detected > 0:
            coordination_groups = coordination_analysis.get(
                "coordination_groups", [])
            if coordination_groups:
                primary_group = coordination_groups[0]
                group_name = primary_group.get("group_name", "Unknown")
                synchronized_posts = primary_group.get("synchronized_posts", 0)
                message_parts.append(
                    f"• **Detected Campaign Group:** \"{group_name}\" — {synchronized_posts} synchronized posts")
            else:
                message_parts.append(
                    f"• **Detected Campaign Groups:** {groups_detected} group(s) identified")
        else:
            message_parts.append(
                "• **Detected Campaign Group:** No coordination detected")

        # Emotional Strategy
        consistency_level = emotional_analysis.get(
            "consistency_level", "Unknown")
        emotion_std = emotional_analysis.get("emotion_std_deviation", 0)
        if consistency_level != "Unknown":
            consistency_desc = "Consistent" if consistency_level == "High" else "Variable"
            message_parts.append(
                f"• **Emotional Strategy:** {consistency_desc} (avg emotion shift = {emotion_std:.2f})")
        else:
            message_parts.append("• **Emotional Strategy:** Pattern unclear")

        # Strategic Assessment
        strategic_assessment = strategic_patterns.get(
            "overall_strategy_assessment", "")
        if strategic_assessment:
            message_parts.append("")
            message_parts.append(f"📊 **Assessment:** {strategic_assessment}")

        # Footer
        message_parts.append("")
        message_parts.append(f"🎯 *Strategic Analysis: {batch_id}*")

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
            "strategic_summary": {
                "total_posts": 0,
                "analyzed_posts": 0,
                "dominant_framing": "Unknown",
                "main_themes": [],
                "coordination_detected": False
            },
            "framing_analysis": {"framing_counts": {}, "dominant_framing": "Unknown"},
            "theme_analysis": {"theme_counts": {}, "top_themes": []},
            "coordination_analysis": {"groups_detected": 0, "coordination_groups": []},
            "emotional_analysis": {"consistency_level": "Unknown", "emotional_patterns": {}},
            "strategic_patterns": {"patterns_detected": 0, "strategic_patterns": []},
            "discord_message": f"🧭 **Strategic Intelligence Summary**\n\n⚠️ **Analysis Skipped**\nReason: {reason}\n\n🎯 *{batch_id}*",
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
            "discord_message": f"❌ **Strategic Intelligence Error**\n\nBatch: {batch_id}\nError: {error_message[:200]}\n\n🎯 *{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"
        }


# Utility function for standalone usage
async def analyze_strategic_patterns(posts: List[Dict], batch_id: str = None) -> Dict:
    """
    Standalone function to analyze strategic patterns from posts

    Args:
        posts: List of post dictionaries with content and engagement data
        batch_id: Optional batch identifier

    Returns:
        Dict with complete strategic intelligence analysis and Discord report
    """
    if not batch_id:
        batch_id = f"strategic_{int(datetime.now().timestamp())}"

    agent = StrategicIntelligenceAgent()
    return await agent.analyze_strategic_patterns(posts, batch_id)
