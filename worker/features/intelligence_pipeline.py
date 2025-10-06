"""
Trending Intelligence Pipeline - Core Processing Engine
Xử lý dữ liệu qua các giai đoạn: Clean -> Score -> Analyze -> Format
"""
import asyncio
import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

from llms.llm_models import LLMModels
from .prompt_suggestions import PromptSuggestionEngine, ContentCalendarGenerator
from .discord_formatter import DiscordMessageFormatter

logger = logging.getLogger(__name__)


class TrendingIntelligencePipeline:
    """Core pipeline for processing trending data through intelligence stages"""

    def __init__(self):
        self.llm = LLMModels()
        self.prompt_engine = PromptSuggestionEngine()
        self.calendar_generator = ContentCalendarGenerator(self.prompt_engine)
        self.discord_formatter = DiscordMessageFormatter(self.llm)

    async def clean_data(self, raw_data: Dict, batch_id: str) -> Dict:
        """Stage 2: Clean and preprocess data"""
        logger.info("🧹 Cleaning and preprocessing data...")

        raw_posts = raw_data.get("data", [])
        cleaned_posts = []

        for post in raw_posts:
            try:
                cleaned_post = self._clean_single_post(post)
                if cleaned_post:
                    cleaned_posts.append(cleaned_post)
            except Exception as e:
                logger.warning(
                    f"Failed to clean post {post.get('id', 'unknown')}: {e}")
                continue

        # Additional preprocessing
        cleaned_posts = self._preprocess_content(cleaned_posts)

        # Save cleaned data
        await self._save_processed_data(cleaned_posts, batch_id, "cleaned")

        return {
            "batch_id": batch_id,
            "stage": "cleaned",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "posts": cleaned_posts,
            "metadata": {
                "original_count": len(raw_posts),
                "cleaned_count": len(cleaned_posts),
                "cleaning_rate": len(cleaned_posts) / len(raw_posts) if raw_posts else 0
            }
        }

    def _clean_single_post(self, post: Dict) -> Optional[Dict]:
        """Clean individual post data"""
        try:
            # Required fields check
            if not all(key in post for key in ['id', 'content', 'author', 'created_at']):
                return None

            # Content validation
            content = post.get('content', '').strip()
            if len(content) < 10:  # Skip very short posts
                return None

            cleaned = {
                "id": post["id"],
                "content": content,
                "author": {
                    "id": post["author"].get("id"),
                    "username": post["author"].get("username", "").lower(),
                    "display_name": post["author"].get("display_name", ""),
                    "follower_count": max(0, post["author"].get("follower_count", 0)),
                    "verified": bool(post["author"].get("verified", False))
                },
                "engagement": {
                    "like_count": max(0, post.get("like_count", 0)),
                    "reply_count": max(0, post.get("reply_count", 0)),
                    "repost_count": max(0, post.get("repost_count", 0))
                },
                "tags": [tag.lower().strip() for tag in post.get("tags", []) if tag.strip()],
                "created_at": post["created_at"],
                "embed": post.get("embed"),

                # Derived fields
                "content_length": len(content),
                "word_count": len(content.split()),
                "has_embed": bool(post.get("embed")),
                "tag_count": len(post.get("tags", []))
            }

            return cleaned

        except Exception as e:
            logger.debug(f"Error cleaning post: {e}")
            return None

    def _preprocess_content(self, posts: List[Dict]) -> List[Dict]:
        """Additional content preprocessing"""
        for post in posts:
            content = post["content"]

            # Extract mentions and hashtags
            words = content.split()
            mentions = [word for word in words if word.startswith('@')]
            hashtags = [word for word in words if word.startswith('#')]

            post.update({
                "mentions": mentions,
                "hashtags": hashtags,
                "mention_count": len(mentions),
                "hashtag_count": len(hashtags),
                "has_question": '?' in content,
                "has_exclamation": '!' in content,
                "is_retweet": content.lower().startswith(('rt @', 'retweet')),
            })

        return posts

    async def calculate_scores(self, cleaned_data: Dict, batch_id: str) -> Dict:
        """Stage 3: Calculate performance scores and metrics"""
        logger.info("📈 Calculating performance scores...")

        posts = cleaned_data.get("posts", [])
        scored_posts = []

        # Calculate scores for each post
        for post in posts:
            scores = self._calculate_post_scores(post, posts)
            post.update(scores)
            scored_posts.append(post)

        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(scored_posts)

        # Save scored data
        await self._save_processed_data(scored_posts, batch_id, "scored")

        return {
            "batch_id": batch_id,
            "stage": "scored",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "posts": scored_posts,
            "aggregate_metrics": aggregate_metrics
        }

    def _calculate_post_scores(self, post: Dict, all_posts: List[Dict]) -> Dict:
        """Calculate various scores for a single post"""
        engagement = post["engagement"]
        author = post["author"]

        # Basic engagement metrics
        total_engagement = (
            engagement["like_count"] +
            engagement["reply_count"] * 2 +  # Replies weighted higher
            engagement["repost_count"] * 3   # Reposts weighted highest
        )

        # Normalized scores (0-100)
        max_engagement = max([
            p["engagement"]["like_count"] +
            p["engagement"]["reply_count"] * 2 +
            p["engagement"]["repost_count"] * 3
            for p in all_posts
        ]) or 1

        engagement_score = min(100, (total_engagement / max_engagement) * 100)

        # Author influence score
        follower_score = min(100, (author["follower_count"] / 10000) * 100)
        verified_bonus = 20 if author["verified"] else 0

        # Content quality indicators
        optimal_length = 100  # characters
        length_score = 100 - \
            abs(post["content_length"] - optimal_length) / optimal_length * 100
        length_score = max(0, min(100, length_score))

        # Virality indicators
        reply_ratio = engagement["reply_count"] / \
            max(1, engagement["like_count"])
        repost_ratio = engagement["repost_count"] / \
            max(1, engagement["like_count"])

        virality_score = min(100, (reply_ratio + repost_ratio * 2) * 50)

        # Tag effectiveness
        tag_score = min(100, post["tag_count"] * 25)  # Up to 4 tags optimal

        # Overall performance score
        performance_score = (
            engagement_score * 0.4 +
            follower_score * 0.2 +
            length_score * 0.15 +
            virality_score * 0.15 +
            tag_score * 0.1
        )

        return {
            "scores": {
                "engagement_score": round(engagement_score, 2),
                "follower_score": round(follower_score, 2),
                "length_score": round(length_score, 2),
                "virality_score": round(virality_score, 2),
                "tag_score": round(tag_score, 2),
                "performance_score": round(performance_score, 2),
                "verified_bonus": verified_bonus
            },
            "metrics": {
                "total_engagement": total_engagement,
                "reply_ratio": round(reply_ratio, 3),
                "repost_ratio": round(repost_ratio, 3),
                "engagement_rate": round(total_engagement / max(1, author["follower_count"]) * 100, 3)
            }
        }

    def _calculate_aggregate_metrics(self, posts: List[Dict]) -> Dict:
        """Calculate aggregate metrics across all posts"""
        if not posts:
            return {}

        # Performance score statistics
        performance_scores = [p["scores"]["performance_score"] for p in posts]
        engagement_scores = [p["scores"]["engagement_score"] for p in posts]

        # Tag analysis
        all_tags = []
        for post in posts:
            all_tags.extend(post["tags"])
        tag_counts = Counter(all_tags)

        # Author analysis
        author_performance = defaultdict(list)
        for post in posts:
            username = post["author"]["username"]
            author_performance[username].append(
                post["scores"]["performance_score"])

        top_authors = sorted(
            [(author, np.mean(scores))
             for author, scores in author_performance.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "performance_stats": {
                "mean_score": round(np.mean(performance_scores), 2),
                "median_score": round(np.median(performance_scores), 2),
                "std_score": round(np.std(performance_scores), 2),
                "top_10_percent": round(np.percentile(performance_scores, 90), 2)
            },
            "engagement_stats": {
                "mean_engagement": round(np.mean(engagement_scores), 2),
                "high_engagement_count": len([s for s in engagement_scores if s > 75])
            },
            "trending_tags": [tag for tag, count in tag_counts.most_common(10)],
            "tag_performance": {
                tag: round(np.mean([
                    p["scores"]["performance_score"] for p in posts if tag in p["tags"]
                ]), 2)
                for tag, count in tag_counts.most_common(5)
            },
            "top_authors": top_authors,
            "total_posts": len(posts)
        }

    async def analyze_strategies(self, scored_data: Dict, batch_id: str) -> Dict:
        """Stage 4: Analyze content strategies and patterns"""
        logger.info("🧠 Analyzing content strategies...")

        posts = scored_data.get("posts", [])
        aggregate_metrics = scored_data.get("aggregate_metrics", {})

        # Strategic analysis using LLM
        strategic_insights = await self._generate_strategic_insights(posts, aggregate_metrics)

        # Pattern analysis
        patterns = self._analyze_success_patterns(posts)

        # Competitive analysis
        competitive_insights = self._analyze_competitive_landscape(posts)

        # Save analysis results
        analysis_results = {
            "batch_id": batch_id,
            "stage": "analyzed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "strategic_insights": strategic_insights,
            "success_patterns": patterns,
            "competitive_insights": competitive_insights,
            "aggregate_metrics": aggregate_metrics,
            "posts": posts
        }

        await self._save_processed_data(analysis_results, batch_id, "analyzed")

        return analysis_results

    async def _generate_strategic_insights(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Generate comprehensive strategic insights using multiple LLM analyses"""
        try:
            logger.info("🤖 Running comprehensive LLM analysis...")

            # Multiple LLM analysis approaches
            all_insights = []

            # 1. Strategic Content Analysis
            content_insights = await self._analyze_content_strategies(posts, metrics)
            all_insights.extend(content_insights)

            # 2. Engagement Optimization Analysis
            engagement_insights = await self._analyze_engagement_strategies(posts, metrics)
            all_insights.extend(engagement_insights)

            # 3. Competitive Intelligence Analysis
            competitive_insights = await self._analyze_competitive_strategies(posts, metrics)
            all_insights.extend(competitive_insights)

            # 4. Trend Prediction Analysis
            trend_insights = await self._analyze_trend_predictions(posts, metrics)
            all_insights.extend(trend_insights)

            # 5. Content Suggestion Generation (Enhanced)
            content_suggestions = await self._generate_enhanced_content_suggestions(posts, metrics)
            all_insights.extend(content_suggestions)

            # 6. Advanced Prompt Suggestions
            prompt_suggestions = await self._generate_advanced_prompt_suggestions(posts, metrics)
            all_insights.extend(prompt_suggestions)

            # Rank and filter insights by quality
            ranked_insights = self._rank_insights_by_quality(all_insights)

            logger.info(
                f"✅ Generated {len(ranked_insights)} high-quality insights")
            return ranked_insights[:10]  # Top 10 insights

        except Exception as e:
            logger.error(f"Failed to generate strategic insights: {e}")
            return []

    async def _analyze_content_strategies(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Analyze content strategies using LLM"""
        try:
            top_performers = sorted(
                posts, key=lambda x: x["scores"]["performance_score"], reverse=True)[:10]

            prompt = self._build_content_strategy_prompt(
                top_performers, metrics)
            response = await self._get_llm_insights(prompt)

            return self._parse_structured_insights(response, "content_strategy")
        except Exception as e:
            logger.warning(f"Content strategy analysis failed: {e}")
            return []

    async def _analyze_engagement_strategies(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Analyze engagement optimization strategies using LLM"""
        try:
            high_engagement_posts = [
                p for p in posts if p["scores"]["engagement_score"] > 70]

            prompt = self._build_engagement_strategy_prompt(
                high_engagement_posts, metrics)
            response = await self._get_llm_insights(prompt)

            return self._parse_structured_insights(response, "engagement_optimization")
        except Exception as e:
            logger.warning(f"Engagement strategy analysis failed: {e}")
            return []

    async def _analyze_competitive_strategies(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Analyze competitive strategies using LLM"""
        try:
            author_performance = self._get_author_performance_data(posts)

            prompt = self._build_competitive_analysis_prompt(
                author_performance, metrics)
            response = await self._get_llm_insights(prompt)

            return self._parse_structured_insights(response, "competitive_intelligence")
        except Exception as e:
            logger.warning(f"Competitive strategy analysis failed: {e}")
            return []

    async def _analyze_trend_predictions(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Generate trend predictions using LLM"""
        try:
            trending_patterns = self._extract_trending_patterns(posts, metrics)

            prompt = self._build_trend_prediction_prompt(trending_patterns)
            response = await self._get_llm_insights(prompt)

            return self._parse_structured_insights(response, "trend_prediction")
        except Exception as e:
            logger.warning(f"Trend prediction analysis failed: {e}")
            return []

    async def _generate_content_suggestions(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Generate specific content suggestions using LLM"""
        try:
            success_patterns = self._extract_success_patterns_for_suggestions(
                posts)

            prompt = self._build_content_suggestion_prompt(
                success_patterns, metrics)
            response = await self._get_llm_insights(prompt)

            return self._parse_structured_insights(response, "content_suggestions")
        except Exception as e:
            logger.warning(f"Content suggestion generation failed: {e}")
            return []

    def _build_content_strategy_prompt(self, top_posts: List[Dict], metrics: Dict) -> str:
        """Build specialized prompt for content strategy analysis"""
        prompt = """🎯 CONTENT STRATEGY ANALYSIS

            You are an expert social media strategist. Analyze these high-performing posts to identify winning content patterns:

            TOP PERFORMING POSTS:
        """
        for i, post in enumerate(top_posts, 1):
            prompt += f"""
                {i}. Performance Score: {post['scores']['performance_score']:.1f}/100
                Content: "{post['content']}"
                Length: {post['content_length']} chars, {post['word_count']} words
                Engagement: {post['engagement']['like_count']}👍 {post['engagement']['reply_count']}💬 {post['engagement']['repost_count']}🔄
                Tags: {', '.join(post['tags'])} 
                Features: Questions={post.get('has_question', False)}, Exclamation={post.get('has_exclamation', False)}
                Author: {post['author']['display_name']} ({post['author']['follower_count']} followers, Verified={post['author']['verified']})
            """

        prompt += f"""
            KEY METRICS:
            - Average Performance: {metrics.get('performance_stats', {}).get('mean_score', 0):.1f}/100
            - Top Tags: {', '.join(metrics.get('trending_tags', [])[:5])}
            - High Engagement Posts: {metrics.get('engagement_stats', {}).get('high_engagement_count', 0)}

            ANALYZE AND PROVIDE:
            1. CONTENT_LENGTH_STRATEGY: Optimal character/word count patterns
            2. NARRATIVE_TECHNIQUES: Storytelling patterns that work
            3. EMOTIONAL_TRIGGERS: What emotions drive engagement
            4. HASHTAG_STRATEGY: Effective tag usage patterns
            5. CALL_TO_ACTION: Best practices for driving responses

            Format each insight as:
            STRATEGY_NAME: [Specific actionable recommendation with data support]

            Focus on concrete, implementable strategies with clear reasoning.
        """
        return prompt

    def _build_engagement_strategy_prompt(self, high_engagement_posts: List[Dict], metrics: Dict) -> str:
        """Build prompt for engagement optimization analysis"""
        if not high_engagement_posts:
            return "No high engagement posts available for analysis."

        prompt = """📈 ENGAGEMENT OPTIMIZATION ANALYSIS

            You are a social media engagement expert. Analyze these high-engagement posts to identify tactics that maximize user interaction:

            HIGH ENGAGEMENT POSTS:
        """
        for i, post in enumerate(high_engagement_posts[:8], 1):
            engagement_rate = post['metrics']['engagement_rate']
            reply_ratio = post['metrics']['reply_ratio']
            repost_ratio = post['metrics']['repost_ratio']

            prompt += f"""
                {i}. Engagement Score: {post['scores']['engagement_score']:.1f}/100
                Content: "{post['content'][:150]}..."
                Metrics: Rate={engagement_rate:.3f}%, Reply Ratio={reply_ratio:.2f}, Repost Ratio={repost_ratio:.2f}
                Interactive Elements: Mentions={post.get('mention_count', 0)}, Hashtags={post.get('hashtag_count', 0)}
                Timing: Posted at hour {datetime.fromisoformat(post['created_at'].replace('Z', '+00:00')).hour}
            """

        prompt += f"""
            ENGAGEMENT PATTERNS TO ANALYZE:
            - What content formats drive the most replies?
            - Which posting times generate peak engagement?
            - How do questions vs statements perform?
            - What role do mentions and hashtags play?
            - Which emotional tones create viral momentum?

            PROVIDE STRATEGIC RECOMMENDATIONS:
            1. REPLY_GENERATION_TACTICS: How to spark conversations
            2. REPOST_AMPLIFICATION: Content that gets shared
            3. OPTIMAL_TIMING: Best posting schedules
            4. INTERACTIVE_ELEMENTS: Use of questions, polls, CTAs
            5. COMMUNITY_BUILDING: Fostering ongoing engagement

            Each recommendation must include specific examples and success metrics.
        """
        return prompt

    def _build_competitive_analysis_prompt(self, author_performance: Dict, metrics: Dict) -> str:
        """Build prompt for competitive intelligence analysis"""
        prompt = """🏆 COMPETITIVE INTELLIGENCE ANALYSIS

            You are a competitive intelligence analyst. Analyze the performance patterns of different content creators:

            TOP PERFORMING AUTHORS:
        """
        top_authors = author_performance.get('top_performers', [])[:7]
        for i, author in enumerate(top_authors, 1):
            prompt += f"""
                {i}. @{author['username']}: Avg Score {author['avg_score']:.1f}/100
                Posts: {author['post_count']}, Best Score: {author['best_score']:.1f}
                Performance Consistency: {author['avg_score']/author['best_score']:.2f}
            """

        prompt += f"""
            MARKET ANALYSIS:
            - Total Active Creators: {author_performance.get('market_concentration', 0)}
            - Competitive Intensity: {author_performance.get('competitive_intensity', 0):.2f}
            - Market Leaders vs Followers gap analysis needed

            ANALYZE COMPETITIVE ADVANTAGES:
            1. CONTENT_DIFFERENTIATION: What makes top performers unique?
            2. CONSISTENCY_PATTERNS: How often do leaders post?
            3. ENGAGEMENT_MOATS: Sustainable competitive advantages
            4. MARKET_GAPS: Underserved content opportunities
            5. DISRUPTION_THREATS: Emerging competitor patterns

            Provide actionable competitive strategies for gaining market share.
        """
        return prompt

    def _build_trend_prediction_prompt(self, trending_patterns: Dict) -> str:
        """Build prompt for trend prediction analysis"""
        prompt = """🔮 TREND PREDICTION ANALYSIS

            You are a social media trend forecaster. Analyze current patterns to predict future opportunities:

            CURRENT TRENDING PATTERNS:
        """
        for category, data in trending_patterns.items():
            prompt += f"""
                {category.upper()}: {data}
            """

        prompt += f"""
            PREDICT EMERGING TRENDS:
            1. CONTENT_EVOLUTION: What content types will trend next?
            2. HASHTAG_MOMENTUM: Which tags are gaining traction?
            3. ENGAGEMENT_SHIFTS: How will user behavior change?
            4. PLATFORM_CHANGES: Algorithmic trends to leverage
            5. SEASONAL_PATTERNS: Upcoming cyclical opportunities

            For each prediction, provide:
            - Confidence level (High/Medium/Low)
            - Timeline (Next week/month/quarter)
            - Actionable preparation steps
            - Risk factors to monitor

            Focus on trends that can be capitalized on immediately.
        """
        return prompt

    def _build_content_suggestion_prompt(self, success_patterns: Dict, metrics: Dict) -> str:
        """Build prompt for generating specific content suggestions"""
        prompt = """✨ CONTENT SUGGESTION GENERATOR

            You are a creative content strategist. Based on successful patterns, generate specific content ideas:
            
            SUCCESS PATTERNS IDENTIFIED:
        """
        for pattern_name, pattern_data in success_patterns.items():
            prompt += f"""
                {pattern_name}: {pattern_data}
            """

        trending_tags = metrics.get('trending_tags', [])[:5]
        prompt += f"""
            TRENDING CONTEXT:
            - Hot Tags: {', '.join(trending_tags)}
            - Average Performance Target: {metrics.get('performance_stats', {}).get('mean_score', 0):.1f}/100
            - High-Engagement Threshold: {metrics.get('engagement_stats', {}).get('high_engagement_count', 0)} posts

            GENERATE SPECIFIC CONTENT IDEAS:
            1. POST_TEMPLATES: 5 high-potential post formats with examples
            2. HASHTAG_COMBINATIONS: Optimal tag strategies for each template
            3. TIMING_RECOMMENDATIONS: Best posting schedules
            4. ENGAGEMENT_HOOKS: Specific opening lines that grab attention
            5. CALL_TO_ACTION_VARIANTS: Different ways to encourage responses

            For each suggestion provide:
            - Expected performance score range
            - Target audience segment
            - Optimal posting time
            - Success metrics to track

            Make suggestions specific, actionable, and immediately implementable.
        """
        return prompt

    def _get_author_performance_data(self, posts: List[Dict]) -> Dict:
        """Extract author performance data for competitive analysis"""
        author_stats = defaultdict(
            lambda: {"posts": 0, "total_score": 0, "best_score": 0, "consistency": []})

        for post in posts:
            username = post["author"]["username"]
            score = post["scores"]["performance_score"]

            author_stats[username]["posts"] += 1
            author_stats[username]["total_score"] += score
            author_stats[username]["best_score"] = max(
                author_stats[username]["best_score"], score)
            author_stats[username]["consistency"].append(score)

        # Calculate competitive metrics
        top_performers = []
        for username, stats in author_stats.items():
            avg_score = stats["total_score"] / stats["posts"]
            consistency = np.std(stats["consistency"]) if len(
                stats["consistency"]) > 1 else 0

            top_performers.append({
                "username": username,
                "post_count": stats["posts"],
                "avg_score": round(avg_score, 2),
                "best_score": round(stats["best_score"], 2),
                # Lower std = higher consistency
                "consistency_score": round(100 - consistency, 2)
            })

        top_performers.sort(key=lambda x: x["avg_score"], reverse=True)

        return {
            "top_performers": top_performers[:10],
            "market_concentration": len(top_performers),
            "competitive_intensity": round(np.std([a["avg_score"] for a in top_performers]), 2)
        }

    def _extract_trending_patterns(self, posts: List[Dict], metrics: Dict) -> Dict:
        """Extract trending patterns for prediction analysis"""
        patterns = {}

        # Tag momentum analysis
        tag_performance = metrics.get('tag_performance', {})
        patterns['tag_trends'] = [(tag, score) for tag, score in sorted(
            tag_performance.items(), key=lambda x: x[1], reverse=True)[:5]]

        # Content length trends
        lengths = [p['content_length'] for p in posts]
        patterns['length_trends'] = {
            'avg': round(np.mean(lengths), 1),
            'trending_range': f"{int(np.percentile(lengths, 25))}-{int(np.percentile(lengths, 75))} chars"
        }

        # Timing patterns
        hours = []
        for post in posts:
            try:
                dt = datetime.fromisoformat(
                    post["created_at"].replace('Z', '+00:00'))
                hours.append(dt.hour)
            except:
                continue

        if hours:
            peak_hours = Counter(hours).most_common(3)
            patterns['timing_trends'] = [
                f"{hour}:00 ({count} posts)" for hour, count in peak_hours]

        # Engagement type trends
        reply_heavy = len(
            [p for p in posts if p['metrics']['reply_ratio'] > 0.5])
        repost_heavy = len(
            [p for p in posts if p['metrics']['repost_ratio'] > 0.3])
        patterns['engagement_trends'] = {
            'discussion_focused': f"{reply_heavy}/{len(posts)} posts",
            'viral_focused': f"{repost_heavy}/{len(posts)} posts"
        }

        return patterns

    def _extract_success_patterns_for_suggestions(self, posts: List[Dict]) -> Dict:
        """Extract success patterns for content suggestions"""
        high_performers = [p for p in posts if p["scores"]
                           ["performance_score"] > 75]

        if not high_performers:
            high_performers = sorted(
                posts, key=lambda x: x["scores"]["performance_score"], reverse=True)[:5]

        patterns = {
            'successful_lengths': [p['content_length'] for p in high_performers],
            'winning_tags': list(set([tag for p in high_performers for tag in p['tags']])),
            'engagement_drivers': {
                'questions': len([p for p in high_performers if p.get('has_question', False)]),
                'exclamations': len([p for p in high_performers if p.get('has_exclamation', False)]),
                'mentions': sum(p.get('mention_count', 0) for p in high_performers),
                'hashtags': sum(p.get('hashtag_count', 0) for p in high_performers)
            },
            'top_content_samples': [p['content'][:100] + '...' for p in high_performers[:3]]
        }

        return patterns

    async def _get_llm_insights(self, prompt: str) -> str:
        """Get insights from LLM with enhanced error handling and retries"""
        try:
            def get_completion():
                return self.llm.call_openai(
                    prompt=prompt,
                    model="gpt-4o-mini",
                    max_tokens=1500,  # Increased for more detailed analysis
                    temperature=0.7
                )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, get_completion)

            if response and len(response.strip()) > 50:  # Ensure meaningful response
                return response
            else:
                logger.warning("LLM returned short or empty response")
                return "No meaningful insights generated"

        except Exception as e:
            logger.error(f"LLM insights failed: {e}")
            return f"LLM analysis failed: {str(e)}"

    def _parse_structured_insights(self, insights_text: str, category: str) -> List[Dict]:
        """Parse LLM insights into structured format with enhanced parsing"""
        insights = []
        lines = insights_text.split('\n')

        current_insight = None
        for line in lines:
            line = line.strip()

            # Look for structured insight patterns
            if ':' in line and any(keyword in line.upper() for keyword in
                                   ['STRATEGY', 'TACTICS', 'OPTIMIZATION', 'ANALYSIS', 'RECOMMENDATION',
                                    'TEMPLATES', 'COMBINATIONS', 'HOOKS', 'VARIANTS', 'DIFFERENTIATION',
                                    'PATTERNS', 'GAPS', 'THREATS', 'EVOLUTION', 'MOMENTUM', 'SHIFTS']):

                if current_insight:
                    insights.append(current_insight)

                # Extract title and description
                parts = line.split(':', 1)
                title = parts[0].strip()
                description = parts[1].strip() if len(
                    parts) > 1 else "No description"

                # Calculate priority based on keywords
                priority = self._calculate_insight_priority(title, description)

                current_insight = {
                    "title": title,
                    "description": description,
                    "category": category,
                    "priority": priority,
                    "actionable": self._is_actionable_insight(description),
                    "confidence": self._extract_confidence_level(description),
                    "timeline": self._extract_timeline(description)
                }
            elif current_insight and line and not line.startswith(('-', '•', '*')):
                # Continue description (but not bullet points)
                current_insight["description"] += " " + line
            elif line.startswith(('-', '•', '*')) and current_insight:
                # Add bullet points as separate insights
                bullet_content = line[1:].strip()
                if len(bullet_content) > 20:  # Meaningful content
                    insights.append({
                        "title": f"{current_insight['title']} - Detail",
                        "description": bullet_content,
                        "category": category,
                        # Lower priority for details
                        "priority": current_insight['priority'] - 10,
                        "actionable": self._is_actionable_insight(bullet_content),
                        "confidence": self._extract_confidence_level(bullet_content),
                        "timeline": self._extract_timeline(bullet_content)
                    })

        if current_insight:
            insights.append(current_insight)

        # Sort by priority and actionability
        insights.sort(key=lambda x: (
            x['priority'], x['actionable']), reverse=True)
        return insights[:8]  # Top 8 insights per category

    def _calculate_insight_priority(self, title: str, description: str) -> int:
        """Calculate priority score for insights"""
        priority = 50  # Base priority

        # High-value keywords
        high_value_keywords = ['immediate', 'urgent', 'critical',
                               'opportunity', 'competitive', 'viral', 'trending']
        for keyword in high_value_keywords:
            if keyword.lower() in (title + ' ' + description).lower():
                priority += 15

        # Actionable indicators
        actionable_keywords = ['implement', 'use', 'apply',
                               'create', 'optimize', 'increase', 'decrease']
        for keyword in actionable_keywords:
            if keyword.lower() in description.lower():
                priority += 10

        # Data-driven indicators
        if any(indicator in description for indicator in ['%', 'score', 'rate', 'ratio', 'performance']):
            priority += 10

        return min(100, priority)

    def _is_actionable_insight(self, description: str) -> bool:
        """Determine if insight is actionable"""
        actionable_patterns = [
            r'\b(use|create|implement|optimize|increase|decrease|focus on|avoid|try|test)\b',
            r'\b(should|must|need to|recommended|suggest)\b',
            r'\b(post at|include|add|remove|change)\b'
        ]

        import re
        for pattern in actionable_patterns:
            if re.search(pattern, description.lower()):
                return True
        return False

    def _extract_confidence_level(self, text: str) -> str:
        """Extract confidence level from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['high confidence', 'strongly', 'definitely', 'proven']):
            return 'high'
        elif any(word in text_lower for word in ['medium confidence', 'likely', 'probably', 'suggest']):
            return 'medium'
        elif any(word in text_lower for word in ['low confidence', 'might', 'possibly', 'uncertain']):
            return 'low'
        return 'medium'  # Default

    def _extract_timeline(self, text: str) -> str:
        """Extract timeline from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['immediate', 'now', 'today', 'next week']):
            return 'immediate'
        elif any(word in text_lower for word in ['next month', 'within month', 'short term']):
            return 'short_term'
        elif any(word in text_lower for word in ['quarter', 'long term', 'future']):
            return 'long_term'
        return 'short_term'  # Default

    def _rank_insights_by_quality(self, all_insights: List[Dict]) -> List[Dict]:
        """Rank insights by quality score"""
        for insight in all_insights:
            quality_score = 0

            # Priority weight
            quality_score += insight.get('priority', 50) * 0.4

            # Actionability weight
            if insight.get('actionable', False):
                quality_score += 30

            # Confidence weight
            confidence_scores = {'high': 25, 'medium': 15, 'low': 5}
            quality_score += confidence_scores.get(
                insight.get('confidence', 'medium'), 15)

            # Timeline urgency weight
            timeline_scores = {'immediate': 20,
                               'short_term': 15, 'long_term': 10}
            quality_score += timeline_scores.get(
                insight.get('timeline', 'short_term'), 15)

            # Description length and quality
            desc_length = len(insight.get('description', ''))
            if 50 <= desc_length <= 200:  # Optimal length
                quality_score += 10
            elif desc_length > 200:
                quality_score += 5

            insight['quality_score'] = round(quality_score, 2)

        # Sort by quality score
        all_insights.sort(key=lambda x: x.get(
            'quality_score', 0), reverse=True)
        return all_insights

    def _categorize_insight(self, title: str) -> str:
        """Categorize insight type"""
        title_upper = title.upper()
        if 'CONTENT' in title_upper:
            return 'content_strategy'
        elif 'TIMING' in title_upper:
            return 'timing_optimization'
        elif 'ENGAGEMENT' in title_upper:
            return 'engagement_tactics'
        elif 'COMPETITIVE' in title_upper:
            return 'competitive_advantage'
        else:
            return 'general_insight'

    def _analyze_success_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze patterns in successful posts"""
        if not posts:
            return {}

        try:
            # Handle different data formats
            performance_scores = []
            for post in posts:
                if "scores" in post and "performance_score" in post["scores"]:
                    performance_scores.append(
                        post["scores"]["performance_score"])
                elif "virality_score" in post:
                    performance_scores.append(post["virality_score"])
                elif "engagement_rate" in post:
                    performance_scores.append(post["engagement_rate"])
                else:
                    # Calculate basic performance score
                    likes = post.get('likes', 0)
                    shares = post.get('shares', 0)
                    comments = post.get('comments', 0)
                    performance_scores.append(
                        (likes + shares * 2 + comments * 3) / 100)

            if not performance_scores:
                return {}

            # Separate high and low performers
            threshold = np.percentile(performance_scores, 75)
            high_performers = []

            for i, post in enumerate(posts):
                if performance_scores[i] >= threshold:
                    # Normalize post data
                    normalized_post = post.copy()
                    if "content_length" not in normalized_post:
                        normalized_post["content_length"] = len(
                            post.get("content", ""))
                    if "tags" not in normalized_post:
                        normalized_post["tags"] = post.get("hashtags", [])
                    high_performers.append(normalized_post)

            if not high_performers:
                return {}

            # Analyze patterns
            patterns = {
                "optimal_length": {
                    "range": self._analyze_length_patterns(high_performers),
                    "avg": round(np.mean([p["content_length"] for p in high_performers]), 1)
                },
                "best_tags": self._analyze_tag_patterns(high_performers),
                "engagement_patterns": self._analyze_engagement_patterns(high_performers),
                "timing_patterns": self._analyze_timing_patterns(high_performers),
                "content_features": self._analyze_content_features(high_performers)
            }

            return patterns

        except Exception as e:
            logger.warning(f"Success pattern analysis failed: {e}")
            return {}

    def _analyze_length_patterns(self, posts: List[Dict]) -> Tuple[int, int]:
        """Analyze optimal content length"""
        lengths = [p["content_length"] for p in posts]
        return (int(np.percentile(lengths, 25)), int(np.percentile(lengths, 75)))

    def _analyze_tag_patterns(self, posts: List[Dict]) -> List[str]:
        """Analyze most effective tags"""
        tag_counter = Counter()
        for post in posts:
            tag_counter.update(post["tags"])
        return [tag for tag, count in tag_counter.most_common(5)]

    def _analyze_engagement_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze engagement patterns"""
        try:
            # Calculate ratios with flexible data format
            like_ratios = []
            repost_ratios = []
            engagement_scores = []

            for post in posts:
                # Calculate like ratio
                likes = post.get('likes', 0)
                views = post.get('views', 1)  # Avoid division by zero
                like_ratios.append(likes / max(views, 1))

                # Calculate repost ratio
                shares = post.get('shares', 0)
                repost_ratios.append(shares / max(views, 1))

                # Get engagement score
                if 'scores' in post and 'engagement_score' in post['scores']:
                    engagement_scores.append(
                        post['scores']['engagement_score'])
                elif 'engagement_rate' in post:
                    engagement_scores.append(post['engagement_rate'])
                else:
                    # Calculate basic engagement score
                    total_engagement = likes + \
                        post.get('shares', 0) + post.get('comments', 0)
                    engagement_scores.append(
                        total_engagement / max(views, 1) * 100)

            return {
                "avg_like_ratio": round(np.mean(like_ratios) if like_ratios else 0, 3),
                "avg_repost_ratio": round(np.mean(repost_ratios) if repost_ratios else 0, 3),
                "high_engagement_threshold": round(np.percentile(engagement_scores, 90) if engagement_scores else 0, 1)
            }
        except Exception as e:
            logger.warning(f"Engagement pattern analysis failed: {e}")
            return {"avg_like_ratio": 0, "avg_repost_ratio": 0, "high_engagement_threshold": 0}

    def _analyze_timing_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze posting time patterns"""
        hours = []
        for post in posts:
            try:
                dt = datetime.fromisoformat(
                    post["created_at"].replace('Z', '+00:00'))
                hours.append(dt.hour)
            except:
                continue

        if not hours:
            return {}

        hour_counter = Counter(hours)
        return {
            "peak_hours": [hour for hour, count in hour_counter.most_common(3)],
            "avg_hour": round(np.mean(hours), 1)
        }

    def _analyze_content_features(self, posts: List[Dict]) -> Dict:
        """Analyze content feature patterns"""
        try:
            features = {}

            # Calculate content features with flexible format
            has_question_list = []
            has_exclamation_list = []
            has_embed_list = []
            hashtag_counts = []
            mention_counts = []

            for post in posts:
                content = post.get('content', '')

                # Check for question marks
                has_question_list.append('?' in content)

                # Check for exclamation marks
                has_exclamation_list.append('!' in content)

                # Check for embeds (links, images, etc.)
                has_embed_list.append(
                    'http' in content.lower() or 'www.' in content.lower())

                # Count hashtags
                if 'hashtag_count' in post:
                    hashtag_counts.append(post['hashtag_count'])
                elif 'hashtags' in post:
                    hashtag_counts.append(len(post['hashtags']))
                else:
                    hashtag_counts.append(content.count('#'))

                # Count mentions
                if 'mention_count' in post:
                    mention_counts.append(post['mention_count'])
                else:
                    mention_counts.append(content.count('@'))

            features = {
                "has_question_rate": np.mean(has_question_list) if has_question_list else 0,
                "has_exclamation_rate": np.mean(has_exclamation_list) if has_exclamation_list else 0,
                "has_embed_rate": np.mean(has_embed_list) if has_embed_list else 0,
                "avg_hashtag_count": round(np.mean(hashtag_counts), 1) if hashtag_counts else 0,
                "avg_mention_count": round(np.mean(mention_counts), 1) if mention_counts else 0
            }

            return {k: round(v, 3) if isinstance(v, float) else v for k, v in features.items()}

        except Exception as e:
            logger.warning(f"Content features analysis failed: {e}")
            return {"has_question_rate": 0, "has_exclamation_rate": 0, "has_embed_rate": 0, "avg_hashtag_count": 0, "avg_mention_count": 0}

    def _analyze_competitive_landscape(self, posts: List[Dict]) -> Dict:
        """Analyze competitive landscape"""
        try:
            # Group by authors
            author_stats = defaultdict(
                lambda: {"posts": 0, "total_score": 0, "best_score": 0})

            for post in posts:
                # Handle different author format
                if 'author' in post and isinstance(post['author'], dict):
                    username = post['author'].get('username', 'unknown')
                elif 'author' in post:
                    username = post['author']
                else:
                    username = 'unknown'

                # Get performance score with fallback
                if 'scores' in post and 'performance_score' in post['scores']:
                    score = post['scores']['performance_score']
                elif 'virality_score' in post:
                    score = post['virality_score']
                elif 'engagement_rate' in post:
                    score = post['engagement_rate']
                else:
                    # Calculate basic score
                    likes = post.get('likes', 0)
                    shares = post.get('shares', 0)
                    comments = post.get('comments', 0)
                    score = (likes + shares * 2 + comments * 3) / 10

                author_stats[username]["posts"] += 1
                author_stats[username]["total_score"] += score
                author_stats[username]["best_score"] = max(
                    author_stats[username]["best_score"], score)

            # Calculate averages and rank
            ranked_authors = []
            for username, stats in author_stats.items():
                avg_score = stats["total_score"] / stats["posts"]
                ranked_authors.append({
                    "username": username,
                    "post_count": stats["posts"],
                    "avg_score": round(avg_score, 2),
                    "best_score": round(stats["best_score"], 2)
                })

            ranked_authors.sort(key=lambda x: x["avg_score"], reverse=True)

            return {
                "top_performers": ranked_authors[:5],
                "market_concentration": len(ranked_authors),
                "competitive_intensity": round(np.std([a["avg_score"] for a in ranked_authors]), 2) if ranked_authors else 0
            }

        except Exception as e:
            logger.warning(f"Competitive landscape analysis failed: {e}")
            return {"top_performers": [], "market_concentration": 0, "competitive_intensity": 0}

    async def format_report(self, analysis_results: Dict, batch_id: str) -> Dict:
        """Stage 5: Format comprehensive report"""
        logger.info("📝 Formatting final report...")

        insights = analysis_results.get("strategic_insights", [])
        patterns = analysis_results.get("success_patterns", {})
        competitive = analysis_results.get("competitive_insights", {})
        metrics = analysis_results.get("aggregate_metrics", {})

        # Create summary
        summary = {
            "batch_id": batch_id,
            "total_posts": metrics.get("total_posts", 0),
            "avg_engagement_score": metrics.get("engagement_stats", {}).get("mean_engagement", 0),
            "success_pattern_score": patterns.get("engagement_patterns", {}).get("high_engagement_threshold", 0),
            "trending_tags": metrics.get("trending_tags", [])[:5],
            "top_performer": competitive.get("top_performers", [{}])[0].get("username", "N/A") if competitive.get("top_performers") else "N/A"
        }

        # Format top insights
        top_insights = insights[:3]  # Top 3 most important

        report = {
            "batch_id": batch_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "top_insights": top_insights,
            "success_patterns": patterns,
            "competitive_landscape": competitive,
            "detailed_metrics": metrics
        }

        # Create Discord embed for the report
        try:
            discord_embed = await self.create_discord_embed(analysis_results, {
                'title_prefix': '🚀 Trending Intelligence Report',
                'max_fields': 6,
                'show_links': True,
                'include_footer_timestamp': True
            })
            report["discord_embed"] = discord_embed
            logger.info("✅ Discord embed added to report")
        except Exception as e:
            logger.warning(f"Failed to create Discord embed: {e}")

        # Save final report
        await self._save_processed_data(report, batch_id, "report")

        return report

    async def _save_processed_data(self, data: Dict, batch_id: str, stage: str):
        """Save processed data to structured directory"""
        try:
            now = datetime.now(timezone.utc)
            dir_path = f"data/processed/{now.year:04d}/{now.month:02d}/{now.day:02d}/{stage}"

            os.makedirs(dir_path, exist_ok=True)

            filepath = f"{dir_path}/{batch_id}_{stage}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"💾 {stage.title()} data saved to: {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save {stage} data: {e}")

    async def _generate_enhanced_content_suggestions(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Generate enhanced content suggestions using advanced prompt engine"""
        try:
            logger.info("🎨 Generating enhanced content suggestions...")

            # Prepare analysis data for prompt engine
            analysis_data = {
                'posts': posts,
                'aggregate_metrics': metrics,
                'success_patterns': self._analyze_success_patterns(posts)
            }

            # Generate comprehensive suggestions
            suggestions_result = await self.prompt_engine.generate_comprehensive_suggestions(
                analysis_data,
                target_goals=['viral', 'engagement',
                              'educational', 'community_building']
            )

            # Convert suggestions to insights format
            insights = []
            top_suggestions = suggestions_result.get(
                'top_recommendations', [])[:8]

            for i, suggestion in enumerate(top_suggestions, 1):
                insight = {
                    'title': f"CONTENT_SUGGESTION_{i}",
                    'description': f"Ready-to-post content: \"{suggestion.get('content', '')}\" | Hashtags: {', '.join(suggestion.get('hashtags', []))} | Performance prediction: {suggestion.get('performance_prediction', 0):.0f}/100",
                    'category': 'content_suggestions',
                    'priority': 90 - i * 5,  # High priority, decreasing
                    'actionable': True,
                    'confidence': 'high',
                    'timeline': 'immediate',
                    'performance_prediction': suggestion.get('performance_prediction', 0),
                    'ready_to_use': True,
                    'content_ready': suggestion.get('content', ''),
                    'hashtags_ready': suggestion.get('hashtags', []),
                    'optimal_timing': suggestion.get('timing', 'peak_hours')
                }
                insights.append(insight)

            logger.info(
                f"✅ Generated {len(insights)} enhanced content suggestions")
            return insights

        except Exception as e:
            logger.warning(f"Enhanced content suggestions failed: {e}")
            return []

    async def _generate_advanced_prompt_suggestions(self, posts: List[Dict], metrics: Dict) -> List[Dict]:
        """Generate advanced prompt suggestions and content calendar"""
        try:
            logger.info(
                "📅 Generating advanced prompt suggestions and calendar...")

            # Prepare analysis data
            analysis_data = {
                'posts': posts,
                'aggregate_metrics': metrics,
                'success_patterns': self._analyze_success_patterns(posts)
            }

            # Generate weekly content calendar
            calendar_result = await self.calendar_generator.generate_weekly_calendar(
                analysis_data,
                focus_areas=['viral', 'engagement', 'educational']
            )

            # Convert calendar to insights
            insights = []
            weekly_calendar = calendar_result.get('weekly_calendar', {})

            for day, day_data in weekly_calendar.items():
                primary_content = day_data.get('primary_content')
                if primary_content:
                    insight = {
                        'title': f"CALENDAR_{day.upper()}",
                        'description': f"{day} strategy: \"{primary_content.get('content', '')[:100]}...\" | Focus: {day_data.get('focus_theme', 'general')} | Times: {', '.join(day_data.get('optimal_times', []))}",
                        'category': 'content_calendar',
                        'priority': 80,
                        'actionable': True,
                        'confidence': 'high',
                        'timeline': 'weekly_planning',
                        'day_of_week': day,
                        'optimal_times': day_data.get('optimal_times', []),
                        'focus_theme': day_data.get('focus_theme', ''),
                        'backup_options': len(day_data.get('backup_options', []))
                    }
                    insights.append(insight)

            # Add strategic calendar insight
            if weekly_calendar:
                total_content = calendar_result.get('total_content_pieces', 0)
                strategic_insight = {
                    'title': 'WEEKLY_CONTENT_STRATEGY',
                    'description': f"Complete 7-day content calendar generated with {total_content} pieces. Focus areas: {', '.join(calendar_result.get('focus_areas', []))}. Optimized posting times and themes for maximum engagement.",
                    'category': 'strategic_planning',
                    'priority': 95,
                    'actionable': True,
                    'confidence': 'high',
                    'timeline': 'weekly_planning',
                    'content_pieces': total_content,
                    'calendar_ready': True
                }
                insights.append(strategic_insight)

            logger.info(
                f"✅ Generated {len(insights)} advanced prompt and calendar insights")
            return insights

        except Exception as e:
            logger.warning(f"Advanced prompt suggestions failed: {e}")
            return []

    async def generate_full_content_package(self, posts: List[Dict], metrics: Dict) -> Dict:
        """Generate a comprehensive content package with all suggestions"""
        try:
            logger.info("📦 Generating full content package...")

            analysis_data = {
                'posts': posts,
                'aggregate_metrics': metrics,
                'success_patterns': self._analyze_success_patterns(posts),
                'competitive_insights': self._analyze_competitive_landscape(posts)
            }

            # Generate all types of content suggestions
            content_package = {}

            # 1. Comprehensive suggestions
            comprehensive_suggestions = await self.prompt_engine.generate_comprehensive_suggestions(
                analysis_data,
                target_goals=['viral', 'engagement',
                              'educational', 'community_building']
            )
            content_package['comprehensive_suggestions'] = comprehensive_suggestions

            # 2. Weekly calendar
            weekly_calendar = await self.calendar_generator.generate_weekly_calendar(
                analysis_data,
                focus_areas=['viral', 'engagement', 'educational']
            )
            content_package['weekly_calendar'] = weekly_calendar

            # 3. A/B test variations
            ab_test_suggestions = comprehensive_suggestions.get(
                'suggestions_by_category', {}).get('ab_test_variations', [])
            content_package['ab_test_ready'] = ab_test_suggestions[:5]

            # 4. Immediate action items
            top_recommendations = comprehensive_suggestions.get(
                'top_recommendations', [])
            immediate_actions = [
                {
                    'content': rec.get('content', ''),
                    'hashtags': rec.get('hashtags', []),
                    'timing': rec.get('timing', 'optimal'),
                    'performance_prediction': rec.get('performance_prediction', 0),
                    'category': rec.get('category', ''),
                    'priority': 'high' if rec.get('performance_prediction', 0) > 75 else 'medium'
                }
                for rec in top_recommendations[:10]
            ]
            content_package['immediate_actions'] = immediate_actions

            # 5. Strategic insights summary
            insights_summary = {
                'total_suggestions': comprehensive_suggestions.get('total_suggestions', 0),
                'calendar_days_covered': len(weekly_calendar.get('weekly_calendar', {})),
                'high_confidence_items': len([item for item in immediate_actions if item['performance_prediction'] > 80]),
                'ready_to_post_count': len([item for item in immediate_actions if item['content']]),
                'categories_covered': list(set([item['category'] for item in immediate_actions if item.get('category')])),
                'generation_timestamp': datetime.now(timezone.utc).isoformat()
            }
            content_package['insights_summary'] = insights_summary

            logger.info(
                f"✅ Generated full content package with {insights_summary['total_suggestions']} total suggestions")
            return content_package

        except Exception as e:
            logger.error(f"Full content package generation failed: {e}")
            return {}

    async def create_discord_embed(self, analysis_results: Dict, options: Optional[Dict] = None) -> Dict:
        """Create Discord embed from analysis results using LLM formatting"""
        try:
            logger.info("🎨 Creating Discord embed from analysis results...")

            # Use Discord formatter to create embed
            embed_payload = await self.discord_formatter.format_analysis_to_discord(
                analysis_results, options
            )

            logger.info("✅ Discord embed created successfully")
            return embed_payload

        except Exception as e:
            logger.error(f"Discord embed creation failed: {e}")
            return {
                "embeds": [{
                    "title": "❌ Analysis Report",
                    "description": f"Report generation completed with errors: {str(e)}",
                    "color": 0xff6b6b,
                    "footer": {
                        "text": f"Generated at {datetime.now(timezone.utc).isoformat()}"
                    }
                }]
            }

    async def create_quick_discord_update(self, metrics: Dict, top_insights: List[Dict]) -> Dict:
        """Create a quick Discord update embed for real-time notifications"""
        try:
            logger.info("⚡ Creating quick Discord update...")

            embed_payload = await self.discord_formatter.format_quick_update(metrics, top_insights)

            logger.info("✅ Quick Discord update created")
            return embed_payload

        except Exception as e:
            logger.error(f"Quick Discord update failed: {e}")
            return {
                "embeds": [{
                    "title": "⚡ Quick Update",
                    "description": f"Update failed: {str(e)}",
                    "color": 0xff6b6b
                }]
            }
