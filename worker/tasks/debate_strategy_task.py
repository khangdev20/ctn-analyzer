"""
Debate Strategy AI Agent - Competition Social Analysis

This module implements an AI agent for monitoring debate-related posts and generating
strategic, concise replies. The agent fetches posts from kingstondaily, analyzes
debate content, and generates targeted responses via Discord.

Features:
- Real-time post monitoring from kingstondaily activity feed
- Debate content filtering and analysis (stance, claims, evidence)
- Strategic reply generation with data-driven counterpoints
- Discord notifications with formatted debate strategies
- Engagement-based post prioritization

Author: AI Assistant
Date: October 9, 2025
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import LLM integration
from llms.llm_models import LLMModels

# Import notification system
try:
    from notifiers.discord_webhook_sender import DiscordWebhookSender
except ImportError:
    DiscordWebhookSender = None
    logging.warning("Discord webhook sender not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DebateStrategyAgent:
    """
    AI Agent for monitoring debate posts and generating strategic replies.

    This agent implements a 3-stage workflow:
    1. Data Fetcher: Monitor kingstondaily activity for debate posts
    2. Debate Analyzer: Analyze stance, claims, and engagement metrics
    3. Reply Generator: Create strategic, factual responses
    """

    def __init__(self):
        """Initialize the debate strategy agent."""
        self.llm = LLMModels()

        # Initialize Discord sender with dedicated debate webhook
        if DiscordWebhookSender:
            # Import debate discord config
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))

            try:
                from config.debate_discord_config import get_debate_webhook
                debate_webhook = get_debate_webhook()

                # Create custom Discord sender with debate webhook
                self.discord_sender = DiscordWebhookSender()
                # Override the webhook URL with debate-specific webhook
                if hasattr(self.discord_sender, 'webhook_url') and debate_webhook:
                    self.discord_sender.webhook_url = debate_webhook
                    logger.info(f"[🎯] Using dedicated debate Discord webhook")
                else:
                    logger.info(
                        f"[🎯] Using default Discord webhook for debate strategy")

            except ImportError:
                logger.warning(
                    "[🎯] Debate Discord config not available, using default")
                self.discord_sender = DiscordWebhookSender()
        else:
            self.discord_sender = None

        # Configuration
        self.api_endpoint = "https://social.legitreal.com/api/users/@kingstondaily/activity"
        self.debate_keywords = ["debate", "slogan",
                                "argument", "policy", "Castillo2025"]
        self.engagement_threshold = 30
        self.reply_hashtags = ["#DebateDay",
                               "#PolicyOverPosters", "#Accountability"]

        # Data paths
        self.base_data_path = Path("data")
        self.reports_path = self.base_data_path / "reports" / "debate_strategy"
        self.reports_path.mkdir(parents=True, exist_ok=True)

    async def run_debate_monitoring_workflow(self, batch_id: str = None, send_discord: bool = True) -> Dict:
        """
        Execute complete debate monitoring workflow.

        Args:
            batch_id: Optional batch identifier for tracking
            send_discord: Whether to send Discord notifications (default True)

        Returns:
            Dictionary containing workflow results and generated replies
        """
        if not batch_id:
            batch_id = f"debate_strategy_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

        logger.info(
            f"[🎯] Starting debate strategy workflow for batch {batch_id}")

        try:
            # Step 1: Data Fetcher - Fetch latest posts from kingstondaily
            posts_data = await self._fetch_kingstondaily_posts()

            if not posts_data:
                logger.warning("No posts data collected for debate analysis")
                return {'status': 'no_data', 'batch_id': batch_id}

            logger.info(
                f"[📊] Fetched {len(posts_data)} posts from kingstondaily")

            # Step 2: Filter posts for debate-related content
            debate_posts = await self._filter_debate_posts(posts_data)

            if not debate_posts:
                logger.info("No debate-related posts found")
                return {'status': 'no_debate_posts', 'batch_id': batch_id}

            logger.info(f"[🔍] Found {len(debate_posts)} debate-related posts")

            # Step 3: Select high-engagement posts for replies
            selected_posts = await self._select_reply_worthy_posts(debate_posts)

            if not selected_posts:
                logger.info("No posts meet engagement threshold for replies")
                return {'status': 'no_worthy_posts', 'batch_id': batch_id}

            logger.info(
                f"[⚡] Selected {len(selected_posts)} posts for strategic replies")

            # Step 4: Generate strategic replies for each selected post
            reply_results = []
            for post in selected_posts:
                reply_result = await self._generate_strategic_reply(post)
                if reply_result:
                    reply_results.append(reply_result)

            logger.info(
                f"[💬] Generated {len(reply_results)} strategic replies")

            # Step 5: Format and send Discord notifications
            discord_success = False
            if send_discord and self.discord_sender and reply_results:
                discord_success = await self._send_discord_notifications(reply_results, batch_id)

            # Step 6: Save results
            workflow_results = {
                'status': 'success',
                'batch_id': batch_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'statistics': {
                    'total_posts_fetched': len(posts_data),
                    'debate_posts_found': len(debate_posts),
                    'posts_selected': len(selected_posts),
                    'replies_generated': len(reply_results)
                },
                'replies': reply_results,
                'discord_sent': discord_success
            }

            await self._save_workflow_results(workflow_results, batch_id)

            logger.info(
                f"[✅] Debate strategy workflow completed successfully for batch {batch_id}")
            return workflow_results

        except Exception as e:
            error_msg = f"Debate strategy workflow error: {str(e)}"
            logger.error(f"[❌] {error_msg}")
            return {
                'status': 'error',
                'batch_id': batch_id,
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _fetch_kingstondaily_posts(self) -> List[Dict]:
        """
        Fetch latest posts from kingstondaily activity feed.
        Falls back to mock data if API is unavailable.

        Returns:
            List of post dictionaries with content, engagement metrics, etc.
        """
        try:
            logger.info(
                "[📡] Fetching posts from kingstondaily activity feed...")

            # Setup request with timeout and retries
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'DebateStrategyAgent/1.0',
                'Accept': 'application/json'
            })

            response = session.get(self.api_endpoint, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Handle different API response formats
                if isinstance(data, dict):
                    # Try different possible keys for posts
                    posts = data.get('posts', []) or data.get(
                        'data', []) or data.get('activities', [])
                else:
                    posts = data if isinstance(data, list) else []

                logger.info(
                    f"[✅] Successfully fetched {len(posts)} posts from API")

                # If no posts found in live API, fall back to mock data for testing
                if len(posts) == 0:
                    logger.info(
                        "[ℹ️] No posts from API, falling back to mock data for testing")
                    return await self._fetch_mock_posts()

                return posts
            else:
                logger.warning(
                    f"[⚠️] API request failed with status {response.status_code}, using mock data")
                return await self._fetch_mock_posts()

        except requests.exceptions.Timeout:
            logger.warning("[⚠️] API request timed out, using mock data")
            return await self._fetch_mock_posts()
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"[⚠️] API request error: {str(e)}, using mock data")
            return await self._fetch_mock_posts()
        except Exception as e:
            logger.warning(
                f"[⚠️] Unexpected error fetching posts: {str(e)}, using mock data")
            return await self._fetch_mock_posts()

    async def _fetch_mock_posts(self) -> List[Dict]:
        """
        Fetch mock posts for testing when API is unavailable.

        Returns:
            List of mock post dictionaries
        """
        try:
            # Import mock data provider
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))

            from mock_debate_data import get_mock_api_response

            mock_response = get_mock_api_response()
            posts = mock_response.get('posts', [])

            logger.info(f"[🎭] Using mock data: {len(posts)} posts generated")
            return posts

        except ImportError:
            logger.error("[❌] Mock data provider not available")
            return []
        except Exception as e:
            logger.error(f"[❌] Error generating mock data: {str(e)}")
            return []

    async def _filter_debate_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Filter posts containing debate-related keywords.

        Args:
            posts: List of post dictionaries

        Returns:
            List of posts containing debate keywords
        """
        debate_posts = []

        for post in posts:
            content = post.get('content', '').lower()

            # Check if any debate keyword is present
            if any(keyword.lower() in content for keyword in self.debate_keywords):
                # Extract relevant data
                filtered_post = {
                    'id': post.get('id'),
                    'content': post.get('content', ''),
                    'embed_link': post.get('embed_link') or post.get('url'),
                    'like_count': post.get('like_count', 0),
                    'reply_count': post.get('reply_count', 0),
                    'hashtags': post.get('hashtags', []),
                    'timestamp': post.get('timestamp') or post.get('created_at'),
                    'engagement_score': post.get('like_count', 0) + post.get('reply_count', 0) * 2
                }
                debate_posts.append(filtered_post)

        logger.info(
            f"[🔍] Filtered {len(debate_posts)} debate posts from {len(posts)} total posts")
        return debate_posts

    async def _select_reply_worthy_posts(self, debate_posts: List[Dict]) -> List[Dict]:
        """
        Select posts that meet engagement threshold or have trending tags.

        Args:
            debate_posts: List of filtered debate posts

        Returns:
            List of posts worth replying to
        """
        worthy_posts = []

        for post in debate_posts:
            engagement_score = post.get('engagement_score', 0)
            hashtags = post.get('hashtags', [])

            # Check engagement threshold
            if engagement_score >= self.engagement_threshold:
                post['selection_reason'] = f'High engagement ({engagement_score})'
                worthy_posts.append(post)
            # Check for trending hashtags (common political/debate tags)
            elif any(tag.lower() in ['trending', 'viral', 'breaking', 'urgent', 'debate2025']
                     for tag in hashtags):
                post['selection_reason'] = 'Trending hashtags'
                worthy_posts.append(post)

        # Sort by engagement score descending
        worthy_posts.sort(key=lambda x: x.get(
            'engagement_score', 0), reverse=True)

        logger.info(f"[⚡] Selected {len(worthy_posts)} posts meeting criteria")
        return worthy_posts

    async def _generate_strategic_reply(self, post: Dict) -> Optional[Dict]:
        """
        Generate a strategic reply for a debate post using LLM analysis.

        Args:
            post: Post dictionary with content and metadata

        Returns:
            Dictionary with analysis and generated reply
        """
        try:
            content = post.get('content', '')

            # Step 1: Analyze the post's stance and claims
            analysis_prompt = f"""
            Analyze this social media post for debate strategy:

            POST CONTENT: "{content}"

            Provide analysis in this JSON format:
            {{
                "stance": "supportive|critical|neutral",
                "core_claim": "main argument or claim",
                "topic": "primary debate topic",
                "has_evidence": true/false,
                "evidence_type": "data|anecdotal|none",
                "reply_worthy": true/false,
                "reply_strategy": "counterpoint approach"
            }}
            """

            analysis_response = self.llm.call_openai(
                analysis_prompt,
                system_prompt="You are a political debate analyst. Analyze posts objectively and identify strategic response opportunities.",
                model="gpt-4o-mini"
            )

            try:
                analysis = json.loads(analysis_response)
            except json.JSONDecodeError:
                logger.warning(
                    f"[⚠️] Failed to parse analysis JSON for post {post.get('id')}")
                return None

            if not analysis.get('reply_worthy', False):
                logger.info(
                    f"[⏭️] Post {post.get('id')} not deemed reply-worthy")
                return None

            # Step 2: Generate strategic reply
            reply_prompt = f"""
            Generate a strategic debate reply for this post:

            ORIGINAL POST: "{content}"
            STANCE: {analysis.get('stance')}
            CORE CLAIM: {analysis.get('core_claim')}
            TOPIC: {analysis.get('topic')}

            Create a 1-2 sentence reply that:
            - Provides a data-driven or logical counterpoint
            - Uses measurable or realistic framing
            - Remains civil and factual
            - Is under 240 characters
            - Avoids repeating slogans
            - Emphasizes clarity and accountability

            REPLY:
            """

            reply_response = self.llm.call_openai(
                reply_prompt,
                system_prompt="You are a strategic debate response generator. Create concise, factual replies that challenge claims with logic and data.",
                model="gpt-4o-mini"
            )

            # Clean and validate reply
            reply_text = reply_response.strip().strip('"')
            if len(reply_text) > 240:
                reply_text = reply_text[:237] + "..."

            # Add hashtags
            hashtag_selection = self.reply_hashtags[:2]  # Use first 2 hashtags
            final_reply = f"{reply_text} {' '.join(hashtag_selection)}"

            result = {
                'post_id': post.get('id'),
                'original_content': content,
                'embed_link': post.get('embed_link'),
                'engagement_score': post.get('engagement_score', 0),
                'analysis': analysis,
                'generated_reply': final_reply,
                'reply_length': len(final_reply),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            logger.info(
                f"[💬] Generated reply for post {post.get('id')}: {len(final_reply)} chars")
            return result

        except Exception as e:
            logger.error(
                f"[❌] Error generating reply for post {post.get('id')}: {str(e)}")
            return None

    async def _send_discord_notifications(self, reply_results: List[Dict], batch_id: str) -> bool:
        """
        Send Discord notifications with generated debate replies.

        Args:
            reply_results: List of reply result dictionaries
            batch_id: Batch identifier

        Returns:
            True if notifications sent successfully
        """
        if not self.discord_sender:
            logger.warning(
                "[⚠️] Discord sender not available, skipping notifications")
            return False

        try:
            # Send summary embed
            total_replies = len(reply_results)
            avg_engagement = sum(r.get('engagement_score', 0)
                                 for r in reply_results) / max(total_replies, 1)

            summary_success = await self.discord_sender.send_rich_embed(
                title="🎯 Debate Strategy Report",
                description=f"Generated {total_replies} strategic debate replies",
                color=0xFF4444,  # Red color for debate strategy
                fields=[
                    {
                        "name": "📊 Statistics",
                        "value": f"Replies: {total_replies}\nAvg Engagement: {avg_engagement:.1f}",
                        "inline": True
                    },
                    {
                        "name": "🎯 Strategy Focus",
                        "value": "Data-driven counterpoints\nMeasurable outcomes\nAccountability emphasis",
                        "inline": True
                    }
                ],
                footer={"text": f"Debate Strategy • Batch: {batch_id}"}
            )

            # Send individual reply notifications
            individual_success = True
            for result in reply_results[:5]:  # Limit to 5 to avoid spam
                embed_link = result.get('embed_link', 'No link available')
                reply_text = result.get('generated_reply', '')
                engagement = result.get('engagement_score', 0)

                reply_message = f"""🎯 **Debate Reply Ready**
🔗 **Post:** {embed_link}
⚡ **Engagement:** {engagement}
💬 **Reply:** "{reply_text}"
"""

                success = await self.discord_sender.send_message(reply_message)
                if not success:
                    individual_success = False

            logger.info(
                f"[✅] Discord notifications sent - Summary: {summary_success}, Individual: {individual_success}")
            return summary_success and individual_success

        except Exception as e:
            logger.error(f"[❌] Discord notification error: {str(e)}")
            return False

    async def _save_workflow_results(self, results: Dict, batch_id: str):
        """
        Save workflow results to local storage.

        Args:
            results: Workflow results dictionary
            batch_id: Batch identifier
        """
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"debate_strategy_{batch_id}_{timestamp}.json"
            filepath = self.reports_path / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"[💾] Workflow results saved to {filepath}")

        except Exception as e:
            logger.error(f"[❌] Error saving workflow results: {str(e)}")


# Async task function for integration with worker system
async def run_debate_strategy_task(batch_id: str = None, send_discord: bool = True) -> Dict:
    """
    Run debate strategy monitoring task.

    Args:
        batch_id: Optional batch identifier
        send_discord: Whether to send Discord notifications

    Returns:
        Task execution results
    """
    agent = DebateStrategyAgent()
    return await agent.run_debate_monitoring_workflow(batch_id, send_discord)


if __name__ == "__main__":
    # CLI support for testing
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Run Debate Strategy Agent')
    parser.add_argument('--batch-id', help='Batch identifier')
    parser.add_argument('--no-discord', action='store_true',
                        help='Skip Discord notifications')

    args = parser.parse_args()

    # Run the agent
    async def main():
        agent = DebateStrategyAgent()
        result = await agent.run_debate_monitoring_workflow(
            batch_id=args.batch_id,
            send_discord=not args.no_discord
        )
        print(json.dumps(result, indent=2))

    asyncio.run(main())
