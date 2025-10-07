#!/usr/bin/env python3
"""
Test Discord sending with sample analysis data
"""

from notifiers.discord_webhook_sender import send_discord_message_webhook
from worker.features.intelligence_pipeline import TrendingIntelligencePipeline
import sys
import os
import asyncio
import logging
import json
from datetime import datetime, timezone

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_sample_analysis_results():
    """Create sample analysis results for testing"""
    return {
        "batch_id": f"test_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')}",
        "aggregate_metrics": {
            "total_posts": 25,
            "engagement_stats": {
                "mean_engagement": 75.2
            },
            "trending_tags": ["AI", "Technology", "Innovation", "StartupLife", "TechNews"]
        },
        "strategic_insights": [
            {
                "title": "AI Content Dominance",
                "description": "AI-related posts are generating 35% higher engagement than average",
                "confidence": 0.89,
                "category": "content_strategy"
            },
            {
                "title": "Visual Content Boost",
                "description": "Posts with images or videos see 60% more interactions",
                "confidence": 0.94,
                "category": "engagement_optimization"
            },
            {
                "title": "Early Morning Peak",
                "description": "Content posted between 6-8 AM UTC performs best",
                "confidence": 0.82,
                "category": "timing_strategy"
            }
        ],
        "success_patterns": {
            "engagement_patterns": {
                "high_engagement_threshold": 80.5
            }
        },
        "competitive_insights": {
            "top_performers": [
                {"username": "tech_guru", "avg_engagement": 89.2}
            ]
        }
    }


async def test_discord_with_pipeline():
    """Test Discord sending through the pipeline"""

    print("[TEST] Testing Discord sending through pipeline...")

    # Create sample analysis data
    analysis_results = create_sample_analysis_results()
    batch_id = analysis_results["batch_id"]

    try:
        # Initialize pipeline
        pipeline = TrendingIntelligencePipeline()
        print("[PIPELINE] Pipeline initialized")

        # Format report
        print("[FORMAT] Formatting analysis report...")
        report = await pipeline.format_report(analysis_results, batch_id)

        print(f"[SUCCESS] Report formatted successfully")
        print(f"[INFO] Report has discord_embed: {'discord_embed' in report}")

        # Test Discord sending
        if "discord_embed" in report:
            print("[DISCORD] Testing Discord embed sending...")

            embed_payload = report["discord_embed"]
            result = send_discord_message_webhook(embed_payload)

            if result and result.status_code == 200:
                print("[SUCCESS] Discord embed sent successfully!")
                return True
            else:
                print(
                    f"[FAILED] Discord embed failed: {result.status_code if result else 'No response'}")

        # Fallback to text message
        print("[FALLBACK] Testing fallback text message...")

        summary = report.get("summary", {})
        fallback_message = f"""**🧪 Test Intelligence Report - {batch_id}**

**Summary:**
• Total Posts: {summary.get('total_posts', 0)}
• Avg Engagement: {summary.get('avg_engagement_score', 0):.1f}%
• Top Tags: {', '.join(summary.get('trending_tags', [])[:3])}

**Key Insights:**
• AI content shows 35% higher engagement
• Visual posts get 60% more interactions  
• Early morning (6-8 AM UTC) is optimal timing

*Test completed at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"""

        result = send_discord_message_webhook(fallback_message)

        if result and result.status_code == 200:
            print("[SUCCESS] Fallback text message sent successfully!")
            return True
        else:
            print(
                f"[FAILED] Fallback message failed: {result.status_code if result else 'No response'}")
            return False

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_discord_with_pipeline())
