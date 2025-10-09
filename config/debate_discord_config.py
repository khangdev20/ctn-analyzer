"""
Discord Channel Configuration for Debate Strategy Agent

This configuration defines Discord webhook settings and channel organization
for the Debate Strategy AI Agent notifications.
"""

import os
from typing import Dict, Optional


class DebateDiscordConfig:
    """Configuration for Discord notifications in debate strategy system."""

    def __init__(self):
        # Main webhook for general notifications
        self.main_webhook = os.getenv('DISCORD_WEBHOOK', '')

        # Dedicated debate strategy webhook (if configured)
        self.debate_webhook = os.getenv('DEBATE_DISCORD_WEBHOOK', '')

        # Channel organization
        self.channels = {
            "debate_strategy": {
                "name": "Debate Strategy",
                "description": "AI-generated strategic debate replies",
                "webhook": self.debate_webhook or self.main_webhook,
                "color": 0xFF4444,  # Red for debate
                "emoji": "🎯"
            },
            "competition_analysis": {
                "name": "Competition Analysis",
                "description": "General competition monitoring",
                "webhook": self.main_webhook,
                "color": 0x1E90FF,  # Blue for analysis
                "emoji": "📊"
            }
        }

    def get_webhook_url(self, channel: str = "debate_strategy") -> str:
        """Get webhook URL for specified channel."""
        return self.channels.get(channel, {}).get("webhook", self.main_webhook)

    def get_channel_config(self, channel: str = "debate_strategy") -> Dict:
        """Get full configuration for specified channel."""
        return self.channels.get(channel, self.channels["debate_strategy"])

    def is_webhook_configured(self, channel: str = "debate_strategy") -> bool:
        """Check if webhook is configured for channel."""
        webhook_url = self.get_webhook_url(channel)
        return bool(webhook_url and webhook_url.startswith('https://'))


# Global instance
discord_config = DebateDiscordConfig()


def get_debate_discord_config() -> DebateDiscordConfig:
    """Get the global debate Discord configuration instance."""
    return discord_config

# Utility functions for easy access


def get_debate_webhook() -> str:
    """Get the debate strategy webhook URL."""
    return discord_config.get_webhook_url("debate_strategy")


def get_debate_channel_config() -> Dict:
    """Get the debate strategy channel configuration."""
    return discord_config.get_channel_config("debate_strategy")


def format_debate_embed_message(title: str, description: str, replies: list = None) -> Dict:
    """
    Format a Discord embed message for debate strategy notifications.

    Args:
        title: Embed title
        description: Main description
        replies: Optional list of reply results

    Returns:
        Discord embed dictionary
    """
    config = get_debate_channel_config()

    embed = {
        "title": f"{config['emoji']} {title}",
        "description": description,
        "color": config["color"],
        "fields": [],
        "footer": {
            "text": f"{config['name']} • {config['description']}"
        }
    }

    if replies:
        # Add statistics field
        embed["fields"].append({
            "name": "📊 Statistics",
            "value": f"Total Replies: {len(replies)}\nAvg Length: {sum(len(r.get('generated_reply', '')) for r in replies) // max(len(replies), 1)} chars",
            "inline": True
        })

        # Add strategy focus field
        embed["fields"].append({
            "name": "🎯 Strategy Focus",
            "value": "✅ Data-driven counterpoints\n✅ Measurable outcomes\n✅ Accountability emphasis",
            "inline": True
        })

    return {"embeds": [embed]}


# Environment setup instructions
SETUP_INSTRUCTIONS = """
# Discord Webhook Setup for Debate Strategy Agent

## Required Environment Variables

1. **Main Discord Webhook** (Required)
   ```
   DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   ```

2. **Dedicated Debate Strategy Webhook** (Optional)
   ```
   DEBATE_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_DEBATE_WEBHOOK_ID/YOUR_DEBATE_TOKEN
   ```

## Discord Server Setup

1. Create a "Debate Strategy" channel in your Discord server
2. Right-click the channel → Integrations → Webhooks → New Webhook
3. Copy the webhook URL and set it as DEBATE_DISCORD_WEBHOOK
4. Optionally customize the webhook name and avatar

## Channel Organization

- **#debate-strategy**: AI-generated strategic replies and analysis
- **#competition-general**: Overall competition monitoring and metrics
- **#leaderboard-updates**: Competition leaderboard changes

## Testing

Run the test script to verify webhook connectivity:
```bash
python test_debate_strategy.py
```
"""

if __name__ == "__main__":
    print("🎯 Debate Strategy Discord Configuration")
    print("=" * 50)

    config = get_debate_discord_config()

    print(
        f"Main Webhook: {'✅ Configured' if config.main_webhook else '❌ Not configured'}")
    print(
        f"Debate Webhook: {'✅ Configured' if config.debate_webhook else '❌ Using main webhook'}")

    print("\nChannel Configuration:")
    for channel_name, channel_config in config.channels.items():
        webhook_status = "✅ Ready" if config.is_webhook_configured(
            channel_name) else "❌ No webhook"
        print(
            f"  {channel_config['emoji']} {channel_config['name']}: {webhook_status}")

    print("\n" + "=" * 50)
    print("Setup Instructions:")
    print(SETUP_INSTRUCTIONS)
