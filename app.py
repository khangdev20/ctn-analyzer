"""
Flask Background Worker Bot Application
Main application file for the background worker bot.
"""
import os
import logging
from flask import Flask, jsonify
from dotenv import load_dotenv
from config.config import Config
from worker.base import BackgroundWorker

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global variables for cleanup
_worker = None
_discord_thread = None


# def setup_signal_handlers():
#     """Setup signal handlers for graceful shutdown."""
#     def signal_handler(signum, frame):
#         logger.info(
#             f"Received signal {signum}, initiating graceful shutdown...")
#         if _worker:
#             _worker.stop()

#         # Shutdown Discord bot
#         try:
#             from notifiers.discord import discord_manager
#             if discord_manager.notifier:
#                 # Run shutdown in a new loop since we're not in async context
#                 loop = asyncio.new_event_loop()
#                 asyncio.set_event_loop(loop)
#                 try:
#                     loop.run_until_complete(discord_manager.shutdown())
#                 finally:
#                     loop.close()
#         except Exception as e:
#             logger.debug(f"Discord shutdown error during signal handling: {e}")

#         sys.exit(0)

#     signal.signal(signal.SIGINT, signal_handler)
#     signal.signal(signal.SIGTERM, signal_handler)


def create_app():
    """Create and configure the Flask application."""
    global _worker, _discord_thread

    app = Flask(__name__)
    app.config.from_object(Config)
    # Initialize background worker
    _worker = BackgroundWorker()

    # Start the background worker automatically
    _worker.start()
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"Starting Background Worker Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
