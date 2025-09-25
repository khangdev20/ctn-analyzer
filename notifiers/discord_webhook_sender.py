from discord_webhook import DiscordWebhook

from config.config import Config

webhook_url = Config.DISCORD_WEBHOOK


def send_discord_message_webhook(content):
    webhook = DiscordWebhook(url=webhook_url, content=content)
    response = webhook.execute()

    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code}")
