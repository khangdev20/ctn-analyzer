from discord_webhook import DiscordWebhook, DiscordEmbed
import json
import logging
from datetime import datetime

from config.config import Config

webhook_url = Config.DISCORD_WEBHOOK
logger = logging.getLogger(__name__)


def send_discord_message_webhook(content):
    """
    Send Discord message with support for both text and embed payloads

    Args:
        content: Can be either:
                - String: Simple text message
                - Dict with 'embeds': Rich embed payload
    """
    try:
        webhook = DiscordWebhook(url=webhook_url)

        # Handle different content types
        if isinstance(content, dict) and 'embeds' in content:
            # Rich embed payload
            logger.info("📤 Sending Discord embed payload...")

            for embed_data in content['embeds']:
                embed = DiscordEmbed()

                # Set basic embed properties
                if 'title' in embed_data:
                    embed.set_title(embed_data['title'])
                if 'description' in embed_data:
                    embed.set_description(embed_data['description'])
                if 'color' in embed_data:
                    embed.set_color(embed_data['color'])

                # Add fields
                for field in embed_data.get('fields', []):
                    embed.add_embed_field(
                        name=field.get('name', ''),
                        value=field.get('value', ''),
                        inline=field.get('inline', False)
                    )

                # Set footer
                if 'footer' in embed_data:
                    footer = embed_data['footer']
                    embed.set_footer(text=footer.get('text', ''))

                # Add embed to webhook
                webhook.add_embed(embed)

        elif isinstance(content, str):
            # Simple text message
            logger.info("📝 Sending Discord text message...")
            webhook.content = content
        else:
            # Try to convert to JSON string
            logger.info("🔄 Converting content to JSON string...")
            webhook.content = json.dumps(content, indent=2)

        # Execute webhook
        response = webhook.execute()

        if response.status_code == 200:
            logger.info("✅ Discord message sent successfully!")
            return response
        else:
            logger.error(
                f"❌ Failed to send Discord message: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"❌ Discord webhook error: {e}")
        return None


def send_quick_discord_update(metrics: dict, insights: list):
    """Send a quick Discord update with key metrics"""
    try:
        embed = DiscordEmbed(
            title="⚡ Trending Intelligence Update",
            color=0x1e90ff
        )

        # Add metrics
        total_posts = metrics.get('total_posts', 0)
        avg_engagement = metrics.get(
            'engagement_stats', {}).get('mean_engagement', 0)
        trending_tags = metrics.get('trending_tags', [])[:3]

        embed.add_embed_field(
            name="📊 Current Stats",
            value=f"Posts: {total_posts} | Avg Engagement: {avg_engagement:.1f}%",
            inline=True
        )

        if trending_tags:
            embed.add_embed_field(
                name="🔥 Trending Now",
                value=", ".join([f"#{tag}" for tag in trending_tags]),
                inline=True
            )

        # Add top insight
        if insights:
            top_insight = insights[0]
            embed.add_embed_field(
                name="💡 Latest Insight",
                value=top_insight.get(
                    'description', 'New pattern detected')[:200],
                inline=False
            )

        embed.set_footer(
            text=f"Live update • {datetime.now().strftime('%H:%M UTC')}")

        webhook = DiscordWebhook(url=webhook_url)
        webhook.add_embed(embed)

        response = webhook.execute()

        if response.status_code == 200:
            logger.info("✅ Quick Discord update sent!")
            return response
        else:
            logger.error(f"❌ Quick update failed: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"❌ Quick Discord update error: {e}")
        return None
