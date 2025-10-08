# 🟦 Stage 8: Reporting — Generate Intelligence Report for Discord

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from llms.llm_models import LLMModels

# Redis cache integration
try:
    from database.redis_helper import get_redis_helper
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReportingStage:
    """
    Task: Generate human-readable intelligence report from latest batch
    - Input: combined analysis results (score, rubric, growth, network, prediction)
    - Output: Discord-ready embed JSON
    - Steps:
      1. Summarize: total posts, avg engagement, top tags
      2. Highlight top velocity and top rubric posts
      3. Summarize predictions and weekly focus
      4. Format as Discord embed payload
      5. Send via webhook
    - Return: {embed_payload, timestamp, send_status}
    """

    def __init__(self, config):
        self.config = config
        self.llm = LLMModels()

        # Initialize Redis helper
        self.redis_helper = None
        if REDIS_AVAILABLE:
            self._redis_initialized = False

    async def execute(self, batch_id: str, prediction_data: Dict, **kwargs) -> Optional[Dict]:
        """Execute reporting stage"""
        logger.info("[BELL] Stage 8: Generating intelligence report...")

        try:
            posts = prediction_data.get("posts", [])

            # 1. Generate comprehensive summary
            summary = await self._generate_comprehensive_summary(posts, batch_id)

            # 2. Create insights and highlights
            insights = await self._create_insights_and_highlights(posts)

            # 3. Generate LLM-powered analysis
            llm_analysis = await self._generate_llm_analysis(summary, insights)

            # 4. Format Discord embed
            discord_embed = await self._create_discord_embed(summary, insights, llm_analysis, batch_id)

            # 5. Create backup text report
            text_report = await self._create_text_report(summary, insights, llm_analysis, batch_id)

            # Create report data structure
            report_data = {
                "batch_id": batch_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": summary,
                "insights": insights,
                "llm_analysis": llm_analysis,
                "discord_embed": discord_embed,
                "text_report": text_report,
                "metadata": {
                    "total_posts_analyzed": len(posts),
                    "report_version": "1.0"
                }
            }

            # Save report data
            output_path = await self._save_report_data(report_data, batch_id)

            # Generate final summary
            final_summary = self._generate_final_summary(report_data, batch_id)

            logger.info(f"[OK] Stage 8 completed: Intelligence report generated")
            logger.info(
                f"[ANALYTICS] Report includes {len(insights.get('top_posts', []))} highlighted posts")

            return {
                **final_summary,
                "report_data": report_data,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"[ERROR] Stage 8 error: {e}")
            return None

    async def _generate_comprehensive_summary(self, posts: List[Dict], batch_id: str) -> Dict:
        """Generate comprehensive summary statistics"""
        if not posts:
            return {"total_posts": 0, "error": "No posts to analyze"}

        # Basic statistics
        total_posts = len(posts)
        total_engagement = sum(post.get("total_engagement", 0)
                               for post in posts)
        avg_engagement = total_engagement / total_posts

        # Score statistics
        final_scores = [post.get("final_score", 0) for post in posts]
        avg_final_score = sum(final_scores) / len(final_scores)

        story_scores = [post.get("story_score", 0) for post in posts]
        avg_story_score = sum(story_scores) / len(story_scores)

        engagement_scores = [post.get("engagement_score", 0) for post in posts]
        avg_engagement_score = sum(engagement_scores) / len(engagement_scores)

        # Trending probabilities
        probabilities = [post.get("trending_probability", 0) for post in posts]
        avg_probability = sum(probabilities) / len(probabilities)

        # Tag analysis
        all_tags = []
        for post in posts:
            all_tags.extend(post.get("tags", []))

        from collections import Counter
        tag_counter = Counter(all_tags)
        trending_tags = [tag for tag, count in tag_counter.most_common(10)]

        # Classification analysis
        classifications = [post.get("classification", "Unknown")
                           for post in posts]
        classification_counts = Counter(classifications)

        # Velocity analysis
        velocities = [post.get("velocity_per_min", 0) for post in posts]
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0

        return {
            "batch_id": batch_id,
            "total_posts": total_posts,
            "avg_engagement": round(avg_engagement, 2),
            "total_engagement": total_engagement,
            "avg_final_score": round(avg_final_score, 2),
            "avg_story_score": round(avg_story_score, 2),
            "avg_engagement_score": round(avg_engagement_score, 2),
            "avg_trending_probability": round(avg_probability, 3),
            "avg_velocity": round(avg_velocity, 2),
            "trending_tags": trending_tags,
            "classification_distribution": dict(classification_counts),
            "high_scoring_posts": len([p for p in posts if p.get("final_score", 0) >= 70]),
            "viral_candidates": len([p for p in posts if p.get("trending_probability", 0) >= 0.8]),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def _create_insights_and_highlights(self, posts: List[Dict]) -> Dict:
        """Create insights and highlight top performing posts"""

        # Top posts by different metrics
        top_velocity_posts = sorted(posts, key=lambda p: p.get(
            "velocity_per_min", 0), reverse=True)[:5]
        top_rubric_posts = sorted(posts, key=lambda p: p.get(
            "final_score", 0), reverse=True)[:5]
        top_prediction_posts = sorted(posts, key=lambda p: p.get(
            "trending_probability", 0), reverse=True)[:5]
        top_engagement_posts = sorted(posts, key=lambda p: p.get(
            "total_engagement", 0), reverse=True)[:5]

        # Strategy insights
        strategy_insights = []

        # Analyze successful patterns
        high_performers = [p for p in posts if p.get("final_score", 0) >= 70]
        if high_performers:
            # Common traits among high performers
            avg_length = sum(p.get("content_length", 0)
                             for p in high_performers) / len(high_performers)
            avg_tags = sum(p.get("tag_count", 0)
                           for p in high_performers) / len(high_performers)

            strategy_insights.append({
                "type": "high_performer_pattern",
                "insight": f"High-performing posts average {avg_length:.0f} characters and {avg_tags:.1f} hashtags",
                "count": len(high_performers),
                "recommendation": "Maintain optimal content length and strategic hashtag usage"
            })

        # Viral candidate analysis
        viral_candidates = [p for p in posts if p.get(
            "trending_probability", 0) >= 0.8]
        if viral_candidates:
            common_factors = []
            for post in viral_candidates:
                common_factors.extend(post.get("key_factors", []))

            from collections import Counter
            factor_counts = Counter(common_factors)
            top_factors = [factor for factor,
                           count in factor_counts.most_common(3)]

            strategy_insights.append({
                "type": "viral_pattern",
                "insight": f"Viral candidates share these traits: {', '.join(top_factors)}",
                "count": len(viral_candidates),
                "recommendation": "Focus on these success factors for viral potential"
            })

        # Engagement pattern analysis
        high_engagement_posts = [
            p for p in posts if p.get("total_engagement", 0) > 20]
        if high_engagement_posts:
            avg_reply_ratio = sum(p.get("reply_count", 0) / max(1, p.get("total_engagement", 1))
                                  for p in high_engagement_posts) / len(high_engagement_posts)

            strategy_insights.append({
                "type": "engagement_pattern",
                "insight": f"High-engagement posts have {avg_reply_ratio:.1%} reply ratio on average",
                "count": len(high_engagement_posts),
                "recommendation": "Create content that encourages discussion and replies"
            })

        return {
            "top_velocity_posts": self._format_post_highlights(top_velocity_posts, "velocity_per_min"),
            "top_rubric_posts": self._format_post_highlights(top_rubric_posts, "final_score"),
            "top_prediction_posts": self._format_post_highlights(top_prediction_posts, "trending_probability"),
            "top_engagement_posts": self._format_post_highlights(top_engagement_posts, "total_engagement"),
            "strategy_insights": strategy_insights,
            "key_findings": self._extract_key_findings(posts)
        }

    def _format_post_highlights(self, posts: List[Dict], metric_key: str) -> List[Dict]:
        """Format post highlights for reporting"""
        highlights = []
        for post in posts:
            highlight = {
                "id": post.get("id"),
                "author": post.get("author"),
                "content_preview": post.get("content", "")[:80] + "..." if len(post.get("content", "")) > 80 else post.get("content", ""),
                "metric_value": post.get(metric_key, 0),
                "final_score": post.get("final_score", 0),
                "trending_probability": post.get("trending_probability", 0),
                "classification": post.get("classification", "Unknown")
            }
            highlights.append(highlight)
        return highlights

    def _extract_key_findings(self, posts: List[Dict]) -> List[str]:
        """Extract key findings from the analysis"""
        findings = []

        # Performance distribution
        high_score_count = len(
            [p for p in posts if p.get("final_score", 0) >= 70])
        if high_score_count > 0:
            percentage = (high_score_count / len(posts)) * 100
            findings.append(
                f"{percentage:.1f}% of posts scored 70+ on viral rubric")

        # Trending potential
        high_prob_count = len(
            [p for p in posts if p.get("trending_probability", 0) >= 0.6])
        if high_prob_count > 0:
            percentage = (high_prob_count / len(posts)) * 100
            findings.append(
                f"{percentage:.1f}% of posts show strong trending potential")

        # Velocity insights
        velocities = [p.get("velocity_per_min", 0) for p in posts]
        if velocities:
            max_velocity = max(velocities)
            if max_velocity > 5:
                findings.append(
                    f"Peak engagement velocity reached {max_velocity:.1f} interactions/minute")

        # Tag effectiveness
        tag_posts = [p for p in posts if p.get("tag_count", 0) > 0]
        no_tag_posts = [p for p in posts if p.get("tag_count", 0) == 0]

        if tag_posts and no_tag_posts:
            tag_avg_score = sum(p.get("final_score", 0)
                                for p in tag_posts) / len(tag_posts)
            no_tag_avg_score = sum(p.get("final_score", 0)
                                   for p in no_tag_posts) / len(no_tag_posts)

            if tag_avg_score > no_tag_avg_score + 5:
                findings.append(
                    "Posts with hashtags significantly outperform those without")

        return findings[:5]  # Limit to top 5 findings

    async def _generate_llm_analysis(self, summary: Dict, insights: Dict) -> Dict:
        """Generate LLM-powered strategic analysis"""
        try:
            # Prepare context for LLM
            context = f"""
            Trending Intelligence Analysis Summary:
            - Total Posts: {summary.get('total_posts', 0)}
            - Average Engagement: {summary.get('avg_engagement', 0)}
            - Average Viral Score: {summary.get('avg_final_score', 0)}/100
            - Viral Candidates: {summary.get('viral_candidates', 0)}
            - Top Tags: {', '.join(summary.get('trending_tags', [])[:5])}
            
            Key Findings:
            {chr(10).join('- ' + finding for finding in insights.get('key_findings', []))}
            
            Strategy Insights:
            {chr(10).join('- ' + insight.get('insight', '') for insight in insights.get('strategy_insights', []))}
            """

            # Generate strategic recommendations
            strategy_prompt = f"""Based on this social media trending analysis, provide 3 strategic recommendations for content creators to improve their viral potential. Be specific and actionable.

            Context: {context}
            
            Format your response as:
            1. [Specific recommendation]
            2. [Specific recommendation] 
            3. [Specific recommendation]"""

            # Initialize Redis helper if needed
            if not self._redis_initialized and REDIS_AVAILABLE:
                try:
                    self.redis_helper = await get_redis_helper()
                    self._redis_initialized = True
                    logger.debug(
                        "[OK] Redis helper initialized for reporting stage")
                except Exception as e:
                    logger.warning(f"Redis initialization failed: {e}")
                    self.redis_helper = None

            # Generate strategic recommendations with cache
            if self.redis_helper and self.redis_helper.cache_enabled:
                async def get_strategy_analysis():
                    return await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.llm.call_openai(
                            strategy_prompt,
                            "You are a social media strategist expert. Provide actionable insights based on data analysis.",
                            model="gpt-4o-mini"
                        )
                    )

                strategy_response = await self.redis_helper.get_or_analyze(
                    "strategic_recommendations", strategy_prompt, get_strategy_analysis
                )
            else:
                strategy_response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm.call_openai(
                        strategy_prompt,
                        "You are a social media strategist expert. Provide actionable insights based on data analysis.",
                        model="gpt-4o-mini"
                    )
                )

            # Generate trend predictions
            trend_prompt = f"""Based on this trending analysis, predict 3 emerging content trends and opportunities for the next week.

            Context: {context}
            
            Format your response as:
            1. [Trend prediction with reasoning]
            2. [Trend prediction with reasoning]
            3. [Trend prediction with reasoning]"""

            # Generate trend predictions with cache
            if self.redis_helper and self.redis_helper.cache_enabled:
                async def get_trend_analysis():
                    return await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.llm.call_openai(
                            trend_prompt,
                            "You are a trend forecasting expert. Identify emerging patterns and opportunities.",
                            model="gpt-4o-mini"
                        )
                    )

                trend_response = await self.redis_helper.get_or_analyze(
                    "trend_predictions", trend_prompt, get_trend_analysis
                )
            else:
                trend_response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm.call_openai(
                        trend_prompt,
                        "You are a trend forecasting expert. Identify emerging patterns and opportunities.",
                        model="gpt-4o-mini"
                    )
                )

            return {
                "strategic_recommendations": strategy_response.strip() if strategy_response else "Analysis in progress...",
                "trend_predictions": trend_response.strip() if trend_response else "Trends being analyzed...",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_used": "gpt-4o-mini"
            }

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "strategic_recommendations": "Strategic analysis will be available in the next report.",
                "trend_predictions": "Trend predictions will be available in the next report.",
                "error": str(e)
            }

    async def _create_discord_embed(self, summary: Dict, insights: Dict, llm_analysis: Dict, batch_id: str) -> Dict:
        """Create Discord embed payload"""

        # Main embed
        embed = {
            "title": "[ANALYTICS] Trending Intelligence Report",
            "description": f"**Batch {batch_id}** • {summary.get('total_posts', 0)} posts analyzed",
            "color": 0x1e90ff,  # Blue color
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fields": []
        }

        # Summary field
        embed["fields"].append({
            "name": "[TRENDING_UP] Summary Statistics",
            "value": f"""**Posts Analyzed:** {summary.get('total_posts', 0)}
**Avg Engagement:** {summary.get('avg_engagement', 0):.1f}
**Avg Viral Score:** {summary.get('avg_final_score', 0):.1f}/100
**Viral Candidates:** {summary.get('viral_candidates', 0)}""",
            "inline": True
        })

        # Classification distribution
        classifications = summary.get('classification_distribution', {})
        class_text = "\n".join(
            [f"**{k}:** {v}" for k, v in classifications.items()])
        embed["fields"].append({
            "name": "[TARGET] Performance Tiers",
            "value": class_text if class_text else "No data",
            "inline": True
        })

        # Top trending tags
        top_tags = summary.get('trending_tags', [])[:5]
        if top_tags:
            embed["fields"].append({
                "name": "[HOT] Trending Tags",
                "value": " ".join([f"#{tag}" for tag in top_tags]),
                "inline": False
            })

        # Top performing post
        top_posts = insights.get('top_prediction_posts', [])
        if top_posts:
            top_post = top_posts[0]
            embed["fields"].append({
                "name": "[STAR] Top Viral Candidate",
                "value": f"**@{top_post.get('author', 'unknown')}** • {top_post.get('trending_probability', 0):.1%} viral probability\n`{top_post.get('content_preview', 'No content')}`",
                "inline": False
            })

        # Strategic insights
        strategy_insights = insights.get('strategy_insights', [])
        if strategy_insights:
            insight_text = "\n".join(
                [f"• {insight.get('insight', '')}" for insight in strategy_insights[:2]])
            embed["fields"].append({
                "name": "[IDEA] Key Insights",
                "value": insight_text,
                "inline": False
            })

        # LLM recommendations (truncated for Discord)
        if llm_analysis.get('strategic_recommendations'):
            recommendations = llm_analysis['strategic_recommendations'][:500] + "..." if len(
                llm_analysis['strategic_recommendations']) > 500 else llm_analysis['strategic_recommendations']
            embed["fields"].append({
                "name": "[LAUNCH] AI Recommendations",
                "value": recommendations,
                "inline": False
            })

        # Footer
        embed["footer"] = {
            "text": f"Intelligence Pipeline v1.0 • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
        }

        return embed

    async def _create_text_report(self, summary: Dict, insights: Dict, llm_analysis: Dict, batch_id: str) -> str:
        """Create backup text report"""

        report_lines = [
            f"[TARGET] TRENDING INTELLIGENCE REPORT - {batch_id}",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "=" * 60,
            "",
            "[ANALYTICS] SUMMARY STATISTICS:",
            f"• Total Posts Analyzed: {summary.get('total_posts', 0)}",
            f"• Average Engagement: {summary.get('avg_engagement', 0):.1f}",
            f"• Average Viral Score: {summary.get('avg_final_score', 0):.1f}/100",
            f"• Viral Candidates: {summary.get('viral_candidates', 0)}",
            f"• Average Trending Probability: {summary.get('avg_trending_probability', 0):.1%}",
            "",
            "🏷️ TOP TRENDING TAGS:",
            " ".join([f"#{tag}" for tag in summary.get(
                'trending_tags', [])[:8]]),
            "",
            "[TARGET] PERFORMANCE DISTRIBUTION:"
        ]

        # Add classification distribution
        for classification, count in summary.get('classification_distribution', {}).items():
            report_lines.append(f"• {classification}: {count}")

        report_lines.extend([
            "",
            "[IDEA] KEY INSIGHTS:"
        ])

        # Add insights
        for finding in insights.get('key_findings', []):
            report_lines.append(f"• {finding}")

        # Add strategy insights
        for insight in insights.get('strategy_insights', []):
            report_lines.append(f"• {insight.get('insight', '')}")

        # Add LLM analysis
        if llm_analysis.get('strategic_recommendations'):
            report_lines.extend([
                "",
                "[LAUNCH] AI STRATEGIC RECOMMENDATIONS:",
                llm_analysis['strategic_recommendations']
            ])

        if llm_analysis.get('trend_predictions'):
            report_lines.extend([
                "",
                "[TRENDING_UP] TREND PREDICTIONS:",
                llm_analysis['trend_predictions']
            ])

        report_lines.extend([
            "",
            "=" * 60,
            f"Report completed at {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
        ])

        return "\n".join(report_lines)

    async def _save_report_data(self, data: Dict, batch_id: str) -> str:
        """Save report data to structured directory"""
        now = datetime.now(timezone.utc)
        dir_path = f"data/reports/{now.year:04d}/{now.month:02d}/{now.day:02d}"
        os.makedirs(dir_path, exist_ok=True)

        filepath = f"{dir_path}/batch_{batch_id}.report.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def _generate_final_summary(self, report_data: Dict, batch_id: str) -> Dict:
        """Generate final summary as specified in AI Agent Prompts"""
        summary = report_data.get("summary", {})
        discord_embed = report_data.get("discord_embed", {})

        return {
            "batch_id": batch_id,
            "embed_payload": discord_embed,
            "timestamp": report_data.get("generated_at"),
            "send_status": "ready",  # Will be updated when actually sent
            "report_highlights": {
                "total_posts": summary.get("total_posts", 0),
                "viral_candidates": summary.get("viral_candidates", 0),
                "top_trending_tags": summary.get("trending_tags", [])[:5],
                "avg_viral_score": summary.get("avg_final_score", 0),
                "key_insights_count": len(report_data.get("insights", {}).get("key_findings", []))
            }
        }
