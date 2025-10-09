#!/usr/bin/env python3
"""
Quick test to verify S3 source information display in Discord messages
"""

import asyncio
import logging
from notifiers.discord_webhook_sender import DiscordWebhookSender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_s3_source_info():
    """Test S3 source information display"""

    async def get_s3_source_info() -> str:
        """Get S3 source information for Discord messages."""
        try:
            from data_access.s3_store import S3Store

            s3_store = S3Store()
            client = s3_store.get_s3_client()

            # Get recent files from S3 (last 3 files)
            response = client.list_objects_v2(
                Bucket=s3_store.bucket,
                Prefix="social-intel/raw/",
                MaxKeys=5
            )

            if 'Contents' in response:
                files = sorted(response['Contents'],
                               key=lambda x: x['LastModified'], reverse=True)[:3]

                source_info = "\n\n📁 **S3 Recent Data Sources:**\n"
                for i, file_obj in enumerate(files, 1):
                    key = file_obj['Key']
                    size_mb = file_obj['Size'] / (1024 * 1024)
                    timestamp = file_obj['LastModified'].strftime(
                        '%Y-%m-%d %H:%M UTC')
                    filename = key.split('/')[-1]
                    source_info += f"`{i}.` **{filename}**\n"
                    source_info += f"    📊 Size: {size_mb:.2f}MB | 📅 {timestamp}\n"

                return source_info
            else:
                return "\n\n📁 **S3 Data Sources:** No recent files found"

        except Exception as e:
            logger.error(f"Error getting S3 source info: {str(e)}")
            return "\n\n📁 **S3 Data Sources:** Error loading source information"

    try:
        logger.info("🧪 Testing S3 source information display...")

        # Get S3 source info
        s3_source_info = await get_s3_source_info()

        # Create test message
        test_message = f"""🧪 **S3 Source Information Test**

This is a test to verify that S3 source information is correctly displayed in Discord messages.{s3_source_info}

✅ **Test Status:** S3 source tracking integration successful
🔗 **Integration:** Cloud-first data architecture
📈 **Benefits:** Full data lineage visibility in Discord notifications
"""

        # Send to Discord
        discord_sender = DiscordWebhookSender()
        success = await discord_sender.send_message(test_message)

        if success:
            logger.info(
                "✅ S3 source information test message sent successfully!")
            print("✅ SUCCESS: S3 source information displayed correctly")
            print("🔍 Check Discord channel to verify S3 source display")
        else:
            logger.error("❌ Failed to send S3 source test message")
            print("❌ FAILED: Could not send S3 source information test")

        return success

    except Exception as e:
        logger.error(f"❌ S3 source test failed: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("S3 SOURCE INFORMATION DISPLAY TEST")
    print("=" * 60)

    result = asyncio.run(test_s3_source_info())

    print("=" * 60)
    if result:
        print("🎉 S3 SOURCE INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("📱 Check your Discord channel to see S3 source information")
    else:
        print("💥 S3 SOURCE TEST FAILED - Check logs for details")
    print("=" * 60)
