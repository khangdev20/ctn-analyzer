# """
# Discord Bot Notifier Module
# Handles sending notifications to Discord servers via bot integration.
# """
# import discord
# from discord.ext import commands
# import asyncio
# import logging
# from typing import Optional, List
# from config.config import Config

# # Setup logging
# logger = logging.getLogger(__name__)


# class DiscordNotifier:
#     """Discord bot for sending notifications to Discord servers."""

#     def __init__(self, token: str = None, intents: discord.Intents = None):
#         """Initialize the Discord notifier bot."""
#         self.token = token or getattr(Config, 'DISCORD_BOT_TOKEN', None)
#         if not self.token:
#             raise ValueError("Discord bot token is required")

#         # Set up intents (using only non-privileged intents)
#         if intents is None:
#             intents = discord.Intents.default()
#             # Don't enable message_content as it requires privileged intent
#             # intents.message_content = True

#         # Create bot instance
#         self.bot = commands.Bot(command_prefix='!', intents=intents)
#         self.is_connected = False

#         # Setup event handlers
#         self._setup_events()

#     def _setup_events(self):
#         """Setup bot event handlers."""

#         @self.bot.event
#         async def on_ready():
#             logger.info(f'Discord bot logged in as {self.bot.user}')
#             self.is_connected = True

#         @self.bot.event
#         async def on_disconnect():
#             logger.warning('Discord bot disconnected')
#             self.is_connected = False

#         @self.bot.event
#         async def on_error(event, *args, **kwargs):
#             logger.error(f'Discord bot error in {event}: {args}')

#         @self.bot.event
#         async def on_resumed():
#             logger.info('Discord bot connection resumed')
#             self.is_connected = True

#     async def start_bot(self):
#         """Start the Discord bot."""
#         try:
#             await self.bot.start(self.token)
#         except Exception as e:
#             logger.error(f"Failed to start Discord bot: {e}")
#             raise

#     async def stop_bot(self):
#         """Stop the Discord bot."""
#         if self.bot and not self.bot.is_closed():
#             try:
#                 # Set connection status to false first
#                 self.is_connected = False

#                 # Cancel Discord-related tasks only (safer approach)
#                 loop = asyncio.get_event_loop()
#                 for task in asyncio.all_tasks(loop):
#                     if (not task.done() and
#                         task != asyncio.current_task() and
#                         hasattr(task, '_coro') and
#                             'discord' in str(task._coro).lower()):
#                         task.cancel()

#                 # Give a moment for tasks to cancel
#                 await asyncio.sleep(0.1)

#                 # Close the bot connection
#                 await self.bot.close()
#                 logger.info("Discord bot closed successfully")
#             except Exception as e:
#                 logger.debug(f"Error during bot shutdown: {e}")
#         self.is_connected = False

#     async def send_message(self, channel_id: int, message: str, embed: discord.Embed = None):
#         """Send a message to a specific Discord channel."""
#         if not self.is_connected:
#             logger.warning(
#                 "Bot is not connected to Discord - message will be skipped")
#             return False

#         try:
#             channel = self.bot.get_channel(channel_id)
#             if not channel:
#                 logger.error(f"Channel {channel_id} not found")
#                 return False

#             if embed:
#                 await channel.send(message, embed=embed)
#             else:
#                 await channel.send(message)

#             logger.info(f"Message sent to channel {channel_id}")
#             return True

#         except Exception as e:
#             logger.error(
#                 f"Failed to send message to channel {channel_id}: {e}")
#             return False

#     async def send_notification(self, channel_id: int, title: str, description: str,
#                                 color: discord.Color = discord.Color.blue(),
#                                 fields: List[dict] = None):
#         """Send a formatted notification embed to Discord channel."""
#         embed = discord.Embed(
#             title=title,
#             description=description,
#             color=color,
#             timestamp=discord.utils.utcnow()
#         )

#         # Add fields if provided
#         if fields:
#             for field in fields:
#                 embed.add_field(
#                     name=field.get('name', 'Field'),
#                     value=field.get('value', 'Value'),
#                     inline=field.get('inline', False)
#                 )

#         # Add footer
#         embed.set_footer(
#             text=f"Bot: {getattr(Config, 'BOT_NAME', 'NotificationBot')}")

#         return await self.send_message(channel_id, "", embed)

#     async def send_alert(self, channel_id: int, alert_type: str, message: str):
#         """Send an alert notification with appropriate color coding."""
#         color_map = {
#             'success': discord.Color.green(),
#             'warning': discord.Color.orange(),
#             'error': discord.Color.red(),
#             'info': discord.Color.blue()
#         }

#         color = color_map.get(alert_type.lower(), discord.Color.blue())

#         return await self.send_notification(
#             channel_id=channel_id,
#             title=f"{alert_type.title()} Alert",
#             description=message,
#             color=color
#         )

#     def add_command(self, name: str, func):
#         """Add a custom command to the bot."""
#         @self.bot.command(name=name)
#         async def custom_command(ctx, *args):
#             try:
#                 await func(ctx, *args)
#             except Exception as e:
#                 logger.error(f"Error in command {name}: {e}")
#                 await ctx.send(f"An error occurred: {e}")

#         logger.info(f"Added command: {name}")


# class DiscordNotifierManager:
#     """Manager class for handling Discord bot lifecycle."""

#     def __init__(self):
#         self.notifier = None
#         self.task = None

#     async def initialize(self, token: str = None):
#         """Initialize and start the Discord notifier."""
#         try:
#             self.notifier = DiscordNotifier(token)

#             # Add basic commands
#             self._add_basic_commands()

#             # Start bot in background task with error handling
#             self.task = asyncio.create_task(self._start_bot_with_retry())

#             # Wait longer for connection and check multiple times
#             max_wait_time = 10  # seconds
#             check_interval = 0.5  # seconds
#             waited = 0

#             while waited < max_wait_time and not self.notifier.is_connected:
#                 await asyncio.sleep(check_interval)
#                 waited += check_interval

#             if self.notifier.is_connected:
#                 logger.info("Discord bot connected successfully!")
#             else:
#                 logger.warning(
#                     "Discord bot connection timeout - may still be connecting in background")

#         except Exception as e:
#             logger.error(f"Failed to initialize Discord notifier: {e}")
#             # Don't re-raise to prevent breaking the entire app
#             await self.shutdown()

#     async def _start_bot_with_retry(self):
#         """Start bot with retry logic and better error handling."""
#         max_retries = 3
#         retry_delay = 2

#         for attempt in range(max_retries):
#             try:
#                 await self.notifier.start_bot()
#                 return
#             except Exception as e:
#                 logger.warning(
#                     f"Discord bot start attempt {attempt + 1} failed: {e}")
#                 if attempt < max_retries - 1:
#                     await asyncio.sleep(retry_delay)
#                     retry_delay *= 2  # Exponential backoff
#                 else:
#                     logger.error("All Discord bot start attempts failed")
#                     raise

#     def _add_basic_commands(self):
#         """Add basic bot commands."""

#         async def ping_command(ctx):
#             await ctx.send('Pong! Bot is running.')

#         async def status_command(ctx):
#             status = "✅ Connected" if self.notifier.is_connected else "❌ Disconnected"
#             await ctx.send(f"Bot Status: {status}")

#         self.notifier.add_command('ping', ping_command)
#         self.notifier.add_command('status', status_command)

#     async def send_notification(self, channel_id: int, **kwargs):
#         """Wrapper method to send notifications."""
#         if not self.notifier:
#             logger.warning(
#                 "Discord notifier not initialized - notification skipped")
#             return False

#         if not self.notifier.is_connected:
#             logger.warning("Discord bot not connected - notification skipped")
#             return False

#         return await self.notifier.send_notification(channel_id, **kwargs)

#     async def send_alert(self, channel_id: int, alert_type: str, message: str):
#         """Wrapper method to send alerts."""
#         if not self.notifier:
#             logger.warning("Discord notifier not initialized - alert skipped")
#             return False

#         if not self.notifier.is_connected:
#             logger.warning("Discord bot not connected - alert skipped")
#             return False

#         return await self.notifier.send_alert(channel_id, alert_type, message)

#     async def shutdown(self):
#         """Shutdown the Discord notifier."""
#         logger.info("Shutting down Discord notifier...")

#         if self.task and not self.task.done():
#             self.task.cancel()
#             try:
#                 await asyncio.wait_for(self.task, timeout=5.0)
#             except (asyncio.CancelledError, asyncio.TimeoutError):
#                 logger.debug("Discord task cancelled or timed out")

#         if self.notifier:
#             await self.notifier.stop_bot()

#         logger.info("Discord notifier shutdown complete")


# # Global instance for easy access
# discord_manager = DiscordNotifierManager()


# async def initialize_discord_bot(token: str = None):
#     """Initialize the global Discord bot instance."""
#     await discord_manager.initialize(token)


# async def send_discord_notification(channel_id: int, title: str, description: str, **kwargs):
#     """Send a notification to Discord channel."""
#     if not discord_manager.notifier:
#         logger.warning(
#             "Discord notifier not initialized - notification skipped")
#         return False

#     logger.info(f"Sending Discord notification: {title}")
#     return await discord_manager.send_notification(
#         channel_id=channel_id,
#         title=title,
#         description=description,
#         **kwargs
#     )


# async def send_discord_alert(channel_id: int, alert_type: str, message: str):
#     """Send an alert to Discord channel."""
#     return await discord_manager.send_alert(channel_id, alert_type, message)
