#!/usr/bin/env python3
"""
Discord Message Formatter using LLM
===================================

This module uses LLM to format analysis outputs into Discord embed payloads.
The LLM acts as a Message Composer that transforms analytics data into 
rich, engaging Discord embeds.

Usage:
    formatter = DiscordMessageFormatter()
    embed_payload = await formatter.format_analysis_to_discord(analysis_data)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import asyncio

# Setup logging
logger = logging.getLogger(__name__)


class DiscordMessageFormatter:
    """LLM-powered Discord message formatter for trending intelligence"""

    def __init__(self, llm_client=None):
        """Initialize with optional LLM client"""
        self.llm_client = llm_client
        if not llm_client:
            # Import LLM client from existing modules
            try:
                from llms.llm_models import LLMModels
                self.llm_client = LLMModels()
                logger.info(
                    "[OK] LLM client initialized for Discord formatting")
            except ImportError:
                logger.warning(
                    "[WARNING] LLM client not available, using fallback formatting")
                self.llm_client = None

    async def format_analysis_to_discord(self, analysis_data: Dict, options: Optional[Dict] = None) -> Dict:
        """
        Format analysis outputs into Discord embed payload using LLM

        Args:
            analysis_data: Complete analysis results from trending intelligence pipeline
            options: Formatting options (locale, max_fields, colors, etc.)

        Returns:
            Dict: Discord webhook payload with embeds
        """
        try:
            logger.info(
                "[FORMATTING] Formatting analysis data for Discord using LLM...")

            # Prepare formatted data for LLM
            formatted_input = self._prepare_llm_input(
                analysis_data, options or {})

            # Use LLM to generate Discord embed
            if self.llm_client:
                embed_payload = await self._generate_with_llm(formatted_input)
            else:
                # Fallback to structured formatting
                embed_payload = self._generate_fallback_embed(formatted_input)

            # Validate and enhance payload
            validated_payload = self._validate_discord_payload(embed_payload)

            logger.info(
                "[SUCCESS] Discord embed payload generated successfully")
            return validated_payload

        except Exception as e:
            logger.error(f"[ERROR] Discord formatting failed: {e}")
            return self._generate_error_embed(str(e))

    def _prepare_llm_input(self, analysis_data: Dict, options: Dict) -> Dict:
        """Prepare structured input for LLM"""
        # Extract key data from analysis results
        batch_id = analysis_data.get(
            'batch_id', f"batch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')}")

        # Summary data
        summary = {
            "total_posts": analysis_data.get('aggregate_metrics', {}).get('total_posts', 0),
            "avg_engagement_score": analysis_data.get('aggregate_metrics', {}).get('engagement_stats', {}).get('mean_engagement', 0),
            "top_tags": analysis_data.get('aggregate_metrics', {}).get('trending_tags', [])[:3]
        }

        # Strategy insights from LLM analysis
        strategy_insights = {
            "top_strategies": [],
            "cohort_notes": []
        }

        strategic_insights = analysis_data.get('strategic_insights', [])
        for insight in strategic_insights[:3]:  # Top 3 strategies
            strategy_insights["top_strategies"].append({
                "label": insight.get('title', 'Strategy'),
                # Convert to 0-1 scale
                "avg_raw_score": insight.get('confidence_score', 0.0) / 100.0,
                "evidence": [
                    insight.get('category', 'analysis'),
                    f"priority: {insight.get('priority', 0)}"
                ]
            })

        # Add actionable insights as cohort notes
        actionable_insights = [
            i for i in strategic_insights if i.get('actionable')]
        for insight in actionable_insights[:2]:
            note = insight.get('description', '')[:100] + "..." if len(
                insight.get('description', '')) > 100 else insight.get('description', '')
            strategy_insights["cohort_notes"].append(note)

        # Growth summary from performance data
        growth_summary = {
            "avg_velocity_per_min": analysis_data.get('aggregate_metrics', {}).get('velocity_stats', {}).get('mean_velocity', 0),
            "top_velocity_posts": [],
            "top_velocity_tags": analysis_data.get('aggregate_metrics', {}).get('trending_tags', [])[:2]
        }

        # Extract top performing posts
        processed_posts = analysis_data.get('processed_posts', [])
        high_performing_posts = sorted(processed_posts, key=lambda x: x.get(
            'virality_score', 0), reverse=True)[:2]

        for post in high_performing_posts:
            growth_summary["top_velocity_posts"].append({
                "post_id": post.get('id', 'unknown'),
                "author": post.get('author', 'unknown'),
                # Normalize
                "velocity_per_min": post.get('virality_score', 0) / 10.0,
                "tag_sample": post.get('hashtags', [])[:2],
                # Placeholder URL
                "url": f"https://example.com/post/{post.get('id', 'unknown')}"
            })

        # Rubric summary from scoring
        rubric_summary = {
            "avg_final_score": analysis_data.get('aggregate_metrics', {}).get('scoring_stats', {}).get('mean_score', 0),
            "trending_candidates": len([p for p in processed_posts if p.get('virality_score', 0) > 80]),
            "high_engagement_posts": len([p for p in processed_posts if p.get('engagement_rate', 0) > 10]),
            "top_posts": []
        }

        for post in high_performing_posts:
            rubric_summary["top_posts"].append({
                "post_id": post.get('id', 'unknown'),
                "author": post.get('author', 'unknown'),
                "final_score": post.get('virality_score', 0),
                "class": "Trending Candidate" if post.get('virality_score', 0) > 80 else "High Engagement",
                "url": f"https://example.com/post/{post.get('id', 'unknown')}"
            })

        # Prepare complete LLM input
        llm_input = {
            "batch_id": batch_id,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "strategy_insights": strategy_insights,
            "growth_summary": growth_summary,
            "rubric_summary": rubric_summary,
            "notes": [
                "Confidence values are heuristic (0-1).",
                "Analysis generated by Trending Intelligence Pipeline.",
                "Data reflects latest trending patterns and engagement metrics."
            ],
            "options": {
                "locale": options.get('locale', 'en'),
                "max_fields": options.get('max_fields', 6),
                "show_links": options.get('show_links', True),
                "include_footer_timestamp": options.get('include_footer_timestamp', True),
                "title_prefix": options.get('title_prefix', '[TRENDING] Trending Intelligence'),
                "include_cohort_notes": options.get('include_cohort_notes', True)
            }
        }

        return llm_input

    async def _generate_with_llm(self, formatted_input: Dict) -> Dict:
        """Generate Discord embed using LLM"""
        try:
            # Create the LLM prompt
            prompt = self._build_discord_formatting_prompt(formatted_input)

            # Call LLM
            response = self.llm_client.generate_response(
                prompt, provider="openai", context="discord_embed_formatting")

            # Parse JSON response
            try:
                embed_payload = json.loads(response)
                return embed_payload
            except json.JSONDecodeError:
                # Try to extract JSON from response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    embed_payload = json.loads(json_str)
                    return embed_payload
                else:
                    raise ValueError("No valid JSON found in LLM response")

        except Exception as e:
            logger.warning(f"LLM formatting failed: {e}, using fallback")
            return self._generate_fallback_embed(formatted_input)

    def _build_discord_formatting_prompt(self, input_data: Dict) -> str:
        """Build the LLM prompt for Discord formatting"""
        prompt = f"""# 🧠 PROMPT: "Use an LLM to format the Discord message (embed) from analysis outputs"

## Role
You are a **Message Composer LLM** that turns analytics outputs into a **Discord embed payload**.  
You do **not** fetch data from the internet. You receive all inputs below.  
Return **only JSON** that is valid for a Discord webhook payload (embeds).

---

## Inputs (provided at runtime)
```json
{json.dumps(input_data, indent=2)}
```

## Instructions
1. Create a visually appealing Discord embed with rich formatting
2. Use emojis and colors to make it engaging
3. Structure information in clear fields
4. Include actionable insights prominently
5. Keep field values concise but informative
6. Use color codes: 0x00ff00 (green) for positive trends, 0xffa500 (orange) for moderate, 0xff0000 (red) for alerts
7. Return ONLY the JSON payload, no explanations

## Required Output Format
```json
{{
  "embeds": [
    {{
      "title": "[TRENDING] Trending Intelligence Report",
      "description": "Latest trending analysis results",
      "color": 0x00ff00,
      "fields": [
        {{
          "name": "[SUMMARY] Summary",
          "value": "Posts analyzed: X\\nAvg engagement: Y%\\nTop tags: #tag1, #tag2",
          "inline": false
        }}
      ],
      "footer": {{
        "text": "Generated at timestamp"
      }}
    }}
  ]
}}
```

Generate the Discord embed payload now:"""

        return prompt

    def _generate_fallback_embed(self, input_data: Dict) -> Dict:
        """Generate fallback embed without LLM"""
        summary = input_data.get('summary', {})
        strategy_insights = input_data.get('strategy_insights', {})
        growth_summary = input_data.get('growth_summary', {})
        rubric_summary = input_data.get('rubric_summary', {})
        options = input_data.get('options', {})

        # Determine color based on performance
        avg_score = rubric_summary.get('avg_final_score', 0)
        if avg_score >= 80:
            color = 0x00ff00  # Green
        elif avg_score >= 60:
            color = 0xffa500  # Orange
        else:
            color = 0xff6b6b  # Red

        # Build embed
        embed = {
            "title": f"{options.get('title_prefix', '[TRENDING] Trending Intelligence')} Report",
            "description": f"Analysis completed for batch `{input_data.get('batch_id', 'unknown')}`",
            "color": color,
            "fields": []
        }

        # Summary field
        embed["fields"].append({
            "name": "[ANALYSIS] Analysis Summary",
            "value": f"**Posts Analyzed:** {summary.get('total_posts', 0)}\n**Avg Engagement:** {summary.get('avg_engagement_score', 0):.1f}%\n**Top Tags:** {', '.join([f'#{tag}' for tag in summary.get('top_tags', [])])[:100]}",
            "inline": False
        })

        # Strategy insights
        if strategy_insights.get('top_strategies'):
            strategies_text = []
            for strategy in strategy_insights['top_strategies'][:2]:
                confidence = int(strategy.get('avg_raw_score', 0) * 100)
                strategies_text.append(
                    f"• **{strategy.get('label', 'Strategy')}** ({confidence}%)")

            embed["fields"].append({
                "name": "[STRATEGIES] Top Strategies",
                "value": "\n".join(strategies_text),
                "inline": True
            })

        # Growth metrics
        embed["fields"].append({
            "name": "[METRICS] Growth Metrics",
            "value": f"**Velocity:** {growth_summary.get('avg_velocity_per_min', 0):.2f}/min\n**Trending Candidates:** {rubric_summary.get('trending_candidates', 0)}\n**High Engagement:** {rubric_summary.get('high_engagement_posts', 0)}",
            "inline": True
        })

        # Top performing content
        if rubric_summary.get('top_posts'):
            top_posts_text = []
            for post in rubric_summary['top_posts'][:2]:
                score = post.get('final_score', 0)
                author = post.get('author', 'unknown')
                top_posts_text.append(f"• **@{author}** - {score:.1f} pts")

            embed["fields"].append({
                "name": "[PERFORMERS] Top Performers",
                "value": "\n".join(top_posts_text),
                "inline": False
            })

        # Actionable insights
        if strategy_insights.get('cohort_notes'):
            insights_text = []
            for note in strategy_insights['cohort_notes'][:2]:
                insights_text.append(f"[INSIGHT] {note}")

            embed["fields"].append({
                "name": "🧠 Key Insights",
                "value": "\n".join(insights_text),
                "inline": False
            })

        # Footer
        if options.get('include_footer_timestamp'):
            embed["footer"] = {
                "text": f"Generated at {input_data.get('generated_at_utc', datetime.now(timezone.utc).isoformat())}"
            }

        return {"embeds": [embed]}

    def _validate_discord_payload(self, payload: Dict) -> Dict:
        """Validate and clean Discord payload"""
        try:
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a dictionary")

            if "embeds" not in payload:
                raise ValueError("Payload must contain 'embeds' key")

            embeds = payload["embeds"]
            if not isinstance(embeds, list) or len(embeds) == 0:
                raise ValueError("Embeds must be a non-empty list")

            # Validate each embed
            for embed in embeds:
                # Ensure required fields
                if "title" not in embed:
                    embed["title"] = "[TRENDING] Trending Intelligence Report"

                # Validate color
                if "color" in embed and not isinstance(embed["color"], int):
                    embed["color"] = 0x00ff00  # Default green

                # Validate fields
                if "fields" in embed:
                    valid_fields = []
                    for field in embed["fields"]:
                        if isinstance(field, dict) and "name" in field and "value" in field:
                            # Truncate long values
                            if len(field["value"]) > 1024:
                                field["value"] = field["value"][:1021] + "..."
                            valid_fields.append(field)
                    embed["fields"] = valid_fields[:25]  # Discord limit

            return payload

        except Exception as e:
            logger.error(f"Payload validation failed: {e}")
            return self._generate_error_embed(f"Validation error: {e}")

    def _generate_error_embed(self, error_message: str) -> Dict:
        """Generate error embed"""
        return {
            "embeds": [{
                "title": "[ERROR] Formatting Error",
                "description": f"Failed to format analysis results: {error_message}",
                "color": 0xff0000,  # Red
                "footer": {
                    "text": f"Error occurred at {datetime.now(timezone.utc).isoformat()}"
                }
            }]
        }

    async def format_quick_update(self, metrics: Dict, insights: List[Dict]) -> Dict:
        """Format a quick update embed for real-time notifications"""
        try:
            # Extract key metrics
            total_posts = metrics.get('total_posts', 0)
            trending_tags = metrics.get('trending_tags', [])[:3]
            avg_engagement = metrics.get(
                'engagement_stats', {}).get('mean_engagement', 0)

            # Get top insight
            top_insight = insights[0] if insights else None

            embed = {
                "title": "[QUICK] Quick Intelligence Update",
                "color": 0x1e90ff,  # Blue
                "fields": [
                    {
                        "name": "[STATS] Current Stats",
                        "value": f"Posts: {total_posts} | Avg Engagement: {avg_engagement:.1f}%",
                        "inline": True
                    }
                ]
            }

            if trending_tags:
                embed["fields"].append({
                    "name": "[TRENDING] Trending Now",
                    "value": ", ".join([f"#{tag}" for tag in trending_tags]),
                    "inline": True
                })

            if top_insight:
                embed["fields"].append({
                    "name": "[INSIGHT] Latest Insight",
                    "value": top_insight.get('description', 'New trending pattern detected')[:200],
                    "inline": False
                })

            embed["footer"] = {
                "text": f"Live update • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
            }

            return {"embeds": [embed]}

        except Exception as e:
            logger.error(f"Quick update formatting failed: {e}")
            return self._generate_error_embed(f"Quick update error: {e}")

# Usage example and testing


async def test_discord_formatter():
    """Test the Discord formatter with sample data"""
    formatter = DiscordMessageFormatter()

    # Sample analysis data
    sample_data = {
        'batch_id': '20251005T0315Z',
        'aggregate_metrics': {
            'total_posts': 243,
            'engagement_stats': {'mean_engagement': 41.78},
            'trending_tags': ['tideturning', 'votehawthorne', 'castillo2025'],
            'velocity_stats': {'mean_velocity': 2.41}
        },
        'strategic_insights': [
            {
                'title': 'Political Debate Strategy',
                'description': 'High engagement through political content with specific hashtags',
                'category': 'content_strategy',
                'priority': 95,
                'confidence_score': 82,
                'actionable': True
            },
            {
                'title': 'Optimal Timing Pattern',
                'description': 'Peak hours (01-03 UTC) show 1.8x higher engagement rates',
                'category': 'timing_strategy',
                'priority': 88,
                'confidence_score': 76,
                'actionable': True
            }
        ],
        'processed_posts': [
            {
                'id': 'p123',
                'author': 'user1',
                'virality_score': 92.1,
                'engagement_rate': 15.2,
                'hashtags': ['votehawthorne', 'election2025']
            },
            {
                'id': 'p888',
                'author': 'user8',
                'virality_score': 89.4,
                'engagement_rate': 14.8,
                'hashtags': ['castillo2025', 'politics']
            }
        ]
    }

    # Test formatting
    result = await formatter.format_analysis_to_discord(sample_data)

    print("[DISCORD] Discord Embed Payload:")
    print(json.dumps(result, indent=2))

    return result

if __name__ == "__main__":
    # Run test
    asyncio.run(test_discord_formatter())
